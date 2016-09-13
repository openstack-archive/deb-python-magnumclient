# Copyright 2014
# The Cloudscaling Group, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


###
# This code is taken from python-novaclient. Goal is minimal modification.
###

"""
Command-line interface to the OpenStack Magnum API.
"""

from __future__ import print_function
import argparse
import getpass
import logging
import os
import sys

from oslo_utils import encodeutils
from oslo_utils import strutils
import six

HAS_KEYRING = False
all_errors = ValueError
try:
    import keyring
    HAS_KEYRING = True
    try:
        if isinstance(keyring.get_keyring(), keyring.backend.GnomeKeyring):
            import gnomekeyring
            all_errors = (ValueError,
                          gnomekeyring.IOError,
                          gnomekeyring.NoKeyringDaemonError)
    except Exception:
        pass
except ImportError:
    pass

from magnumclient.common import cliutils
from magnumclient import exceptions as exc
from magnumclient.v1 import client as client_v1
from magnumclient.v1 import shell as shell_v1
from magnumclient import version

LATEST_API_VERSION = ('1', 'latest')
DEFAULT_INTERFACE = 'public'
DEFAULT_SERVICE_TYPE = 'container-infra'

logger = logging.getLogger(__name__)


def positive_non_zero_float(text):
    if text is None:
        return None
    try:
        value = float(text)
    except ValueError:
        msg = "%s must be a float" % text
        raise argparse.ArgumentTypeError(msg)
    if value <= 0:
        msg = "%s must be greater than 0" % text
        raise argparse.ArgumentTypeError(msg)
    return value


class SecretsHelper(object):
    def __init__(self, args, client):
        self.args = args
        self.client = client
        self.key = None

    def _validate_string(self, text):
        if text is None or len(text) == 0:
            return False
        return True

    def _make_key(self):
        if self.key is not None:
            return self.key
        keys = [
            self.client.auth_url,
            self.client.projectid,
            self.client.user,
            self.client.region_name,
            self.client.endpoint_type,
            self.client.service_type,
            self.client.service_name,
            self.client.volume_service_name,
        ]
        for (index, key) in enumerate(keys):
            if key is None:
                keys[index] = '?'
            else:
                keys[index] = str(keys[index])
        self.key = "/".join(keys)
        return self.key

    def _prompt_password(self, verify=True):
        pw = None
        if hasattr(sys.stdin, 'isatty') and sys.stdin.isatty():
            # Check for Ctl-D
            try:
                while True:
                    pw1 = getpass.getpass('OS Password: ')
                    if verify:
                        pw2 = getpass.getpass('Please verify: ')
                    else:
                        pw2 = pw1
                    if pw1 == pw2 and self._validate_string(pw1):
                        pw = pw1
                        break
            except EOFError:
                pass
        return pw

    def save(self, auth_token, management_url, tenant_id):
        if not HAS_KEYRING or not self.args.os_cache:
            return
        if (auth_token == self.auth_token and
           management_url == self.management_url):
            # Nothing changed....
            return
        if not all([management_url, auth_token, tenant_id]):
            raise ValueError("Unable to save empty management url/auth token")
        value = "|".join([str(auth_token),
                          str(management_url),
                          str(tenant_id)])
        keyring.set_password("magnumclient_auth", self._make_key(), value)

    @property
    def password(self):
        if self._validate_string(self.args.os_password):
            return self.args.os_password
        verify_pass = (
            strutils.bool_from_string(cliutils.env("OS_VERIFY_PASSWORD"))
        )
        return self._prompt_password(verify_pass)

    @property
    def management_url(self):
        if not HAS_KEYRING or not self.args.os_cache:
            return None
        management_url = None
        try:
            block = keyring.get_password('magnumclient_auth',
                                         self._make_key())
            if block:
                _token, management_url, _tenant_id = block.split('|', 2)
        except all_errors:
            pass
        return management_url

    @property
    def auth_token(self):
        # Now is where it gets complicated since we
        # want to look into the keyring module, if it
        # exists and see if anything was provided in that
        # file that we can use.
        if not HAS_KEYRING or not self.args.os_cache:
            return None
        token = None
        try:
            block = keyring.get_password('magnumclient_auth',
                                         self._make_key())
            if block:
                token, _management_url, _tenant_id = block.split('|', 2)
        except all_errors:
            pass
        return token

    @property
    def tenant_id(self):
        if not HAS_KEYRING or not self.args.os_cache:
            return None
        tenant_id = None
        try:
            block = keyring.get_password('magnumclient_auth',
                                         self._make_key())
            if block:
                _token, _management_url, tenant_id = block.split('|', 2)
        except all_errors:
            pass
        return tenant_id


class MagnumClientArgumentParser(argparse.ArgumentParser):

    def __init__(self, *args, **kwargs):
        super(MagnumClientArgumentParser, self).__init__(*args, **kwargs)

    def error(self, message):
        """error(message: string)

        Prints a usage message incorporating the message to stderr and
        exits.
        """
        self.print_usage(sys.stderr)
        # FIXME(lzyeval): if changes occur in argparse.ArgParser._check_value
        choose_from = ' (choose from'
        progparts = self.prog.partition(' ')
        self.exit(2, "error: %(errmsg)s\nTry '%(mainp)s help %(subp)s'"
                     " for more information.\n" %
                     {'errmsg': message.split(choose_from)[0],
                      'mainp': progparts[0],
                      'subp': progparts[2]})


class OpenStackMagnumShell(object):

    def get_base_parser(self):
        parser = MagnumClientArgumentParser(
            prog='magnum',
            description=__doc__.strip(),
            epilog='See "magnum help COMMAND" '
                   'for help on a specific command.',
            add_help=False,
            formatter_class=OpenStackHelpFormatter,
        )

        # Global arguments
        parser.add_argument('-h', '--help',
                            action='store_true',
                            help=argparse.SUPPRESS)

        parser.add_argument('--version',
                            action='version',
                            version=version.version_info.version_string())

        parser.add_argument('--debug',
                            default=False,
                            action='store_true',
                            help="Print debugging output.")

        parser.add_argument('--os-cache',
                            default=strutils.bool_from_string(
                                cliutils.env('OS_CACHE', default=False)),
                            action='store_true',
                            help="Use the auth token cache. Defaults to False "
                            "if env[OS_CACHE] is not set.")

        parser.add_argument('--os-region-name',
                            metavar='<region-name>',
                            default=os.environ.get('OS_REGION_NAME'),
                            help='Region name. Default=env[OS_REGION_NAME].')


# TODO(mattf) - add get_timings support to Client
#        parser.add_argument('--timings',
#            default=False,
#            action='store_true',
#            help="Print call timing info")

# TODO(mattf) - use timeout
#        parser.add_argument('--timeout',
#            default=600,
#            metavar='<seconds>',
#            type=positive_non_zero_float,
#            help="Set HTTP call timeout (in seconds)")

        parser.add_argument('--os-auth-url',
                            metavar='<auth-auth-url>',
                            default=cliutils.env('OS_AUTH_URL', default=None),
                            help='Defaults to env[OS_AUTH_URL].')

        parser.add_argument('--os-user-id',
                            metavar='<auth-user-id>',
                            default=cliutils.env('OS_USER_ID', default=None),
                            help='Defaults to env[OS_USER_ID].')

        parser.add_argument('--os-username',
                            metavar='<auth-username>',
                            default=cliutils.env('OS_USERNAME', default=None),
                            help='Defaults to env[OS_USERNAME].')

        parser.add_argument('--os-user-domain-id',
                            metavar='<auth-user-domain-id>',
                            default=cliutils.env('OS_USER_DOMAIN_ID',
                                                 default=None),
                            help='Defaults to env[OS_USER_DOMAIN_ID].')

        parser.add_argument('--os-user-domain-name',
                            metavar='<auth-user-domain-name>',
                            default=cliutils.env('OS_USER_DOMAIN_NAME',
                                                 default=None),
                            help='Defaults to env[OS_USER_DOMAIN_NAME].')

        parser.add_argument('--os-project-id',
                            metavar='<auth-project-id>',
                            default=cliutils.env('OS_PROJECT_ID',
                                                 default=None),
                            help='Defaults to env[OS_PROJECT_ID].')

        parser.add_argument('--os-project-name',
                            metavar='<auth-project-name>',
                            default=cliutils.env('OS_PROJECT_NAME',
                                                 default=None),
                            help='Defaults to env[OS_PROJECT_NAME].')

        parser.add_argument('--os-tenant-id',
                            metavar='<auth-tenant-id>',
                            default=cliutils.env('OS_TENANT_ID',
                                                 default=None),
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-tenant-name',
                            metavar='<auth-tenant-name>',
                            default=cliutils.env('OS_TENANT_NAME',
                                                 default=None),
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-project-domain-id',
                            metavar='<auth-project-domain-id>',
                            default=cliutils.env('OS_PROJECT_DOMAIN_ID',
                                                 default=None),
                            help='Defaults to env[OS_PROJECT_DOMAIN_ID].')

        parser.add_argument('--os-project-domain-name',
                            metavar='<auth-project-domain-name>',
                            default=cliutils.env('OS_PROJECT_DOMAIN_NAME',
                                                 default=None),
                            help='Defaults to env[OS_PROJECT_DOMAIN_NAME].')

        parser.add_argument('--os-token',
                            metavar='<auth-token>',
                            default=cliutils.env('OS_TOKEN', default=None),
                            help='Defaults to env[OS_TOKEN].')

        parser.add_argument('--os-password',
                            metavar='<auth-password>',
                            default=cliutils.env('OS_PASSWORD',
                                                 default=None),
                            help='Defaults to env[OS_PASSWORD].')

        parser.add_argument('--service-type',
                            metavar='<service-type>',
                            help='Defaults to container-infra for all '
                                 'actions.')
        parser.add_argument('--service_type',
                            help=argparse.SUPPRESS)

        parser.add_argument('--endpoint-type',
                            metavar='<endpoint-type>',
                            default=cliutils.env('OS_ENDPOINT_TYPE',
                                                 default=None),
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-endpoint-type',
                            metavar='<os-endpoint-type>',
                            default=cliutils.env('OS_ENDPOINT_TYPE',
                                                 default=None),
                            help='Defaults to env[OS_ENDPOINT_TYPE]')

        parser.add_argument('--os-interface',
                            metavar='<os-interface>',
                            default=cliutils.env(
                                'OS_INTERFACE',
                                default=DEFAULT_INTERFACE),
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-cloud',
                            metavar='<auth-cloud>',
                            default=cliutils.env('OS_CLOUD', default=None),
                            help='Defaults to env[OS_CLOUD].')

        # NOTE(dtroyer): We can't add --endpoint_type here due to argparse
        #                thinking usage-list --end is ambiguous; but it
        #                works fine with only --endpoint-type present
        #                Go figure.  I'm leaving this here for doc purposes.
        # parser.add_argument('--endpoint_type',
        #    help=argparse.SUPPRESS)

        parser.add_argument('--magnum-api-version',
                            metavar='<magnum-api-ver>',
                            default=cliutils.env(
                                'MAGNUM_API_VERSION',
                                default='latest'),
                            help='Accepts "api", '
                                 'defaults to env[MAGNUM_API_VERSION].')
        parser.add_argument('--magnum_api_version',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-cacert',
                            metavar='<ca-certificate>',
                            default=cliutils.env('OS_CACERT', default=None),
                            help='Specify a CA bundle file to use in '
                            'verifying a TLS (https) server certificate. '
                            'Defaults to env[OS_CACERT].')

        parser.add_argument('--os-endpoint-override',
                            metavar='<endpoint-override>',
                            default=cliutils.env('OS_ENDPOINT_OVERRIDE',
                                                 default=None),
                            help="Use this API endpoint instead of the "
                            "Service Catalog.")
        parser.add_argument('--bypass-url',
                            metavar='<bypass-url>',
                            default=cliutils.env('BYPASS_URL', default=None),
                            dest='bypass_url',
                            help=argparse.SUPPRESS)
        parser.add_argument('--bypass_url',
                            help=argparse.SUPPRESS)

        parser.add_argument('--insecure',
                            default=cliutils.env('MAGNUMCLIENT_INSECURE',
                                                 default=False),
                            action='store_true',
                            help="Do not verify https connections")

        return parser

    def get_subcommand_parser(self, version):
        parser = self.get_base_parser()

        self.subcommands = {}
        subparsers = parser.add_subparsers(metavar='<subcommand>')

        try:
            actions_modules = {
                '1': shell_v1.COMMAND_MODULES
            }[version]
        except KeyError:
            actions_modules = shell_v1.COMMAND_MODULES

        for actions_module in actions_modules:
            self._find_actions(subparsers, actions_module)
        self._find_actions(subparsers, self)

        self._add_bash_completion_subparser(subparsers)

        return parser

    def _add_bash_completion_subparser(self, subparsers):
        subparser = (
            subparsers.add_parser('bash_completion',
                                  add_help=False,
                                  formatter_class=OpenStackHelpFormatter)
        )
        self.subcommands['bash_completion'] = subparser
        subparser.set_defaults(func=self.do_bash_completion)

    def _find_actions(self, subparsers, actions_module):
        for attr in (a for a in dir(actions_module) if a.startswith('do_')):
            # I prefer to be hyphen-separated instead of underscores.
            command = attr[3:].replace('_', '-')
            callback = getattr(actions_module, attr)
            desc = callback.__doc__ or ''
            action_help = desc.strip()
            arguments = getattr(callback, 'arguments', [])

            subparser = (
                subparsers.add_parser(command,
                                      help=action_help,
                                      description=desc,
                                      add_help=False,
                                      formatter_class=OpenStackHelpFormatter)
            )
            subparser.add_argument('-h', '--help',
                                   action='help',
                                   help=argparse.SUPPRESS,)
            self.subcommands[command] = subparser
            for (args, kwargs) in arguments:
                subparser.add_argument(*args, **kwargs)
            subparser.set_defaults(func=callback)

    def setup_debugging(self, debug):
        if debug:
            streamformat = "%(levelname)s (%(module)s:%(lineno)d) %(message)s"
            # Set up the root logger to debug so that the submodules can
            # print debug messages
            logging.basicConfig(level=logging.DEBUG,
                                format=streamformat)
        else:
            streamformat = "%(levelname)s %(message)s"
            logging.basicConfig(level=logging.CRITICAL,
                                format=streamformat)

    def _check_version(self, api_version):
        if api_version == 'latest':
            return LATEST_API_VERSION
        else:
            try:
                versions = tuple(int(i) for i in api_version.split('.'))
            except ValueError:
                versions = ()
            if len(versions) == 1:
                # Default value of magnum_api_version is '1'.
                # If user not specify the value of api version, not passing
                # headers at all.
                magnum_api_version = None
            elif len(versions) == 2:
                magnum_api_version = api_version
                # In the case of '1.0'
                if versions[1] == 0:
                    magnum_api_version = None
            else:
                msg = _("The requested API version %(ver)s is an unexpected "
                        "format. Acceptable formats are 'X', 'X.Y', or the "
                        "literal string '%(latest)s'."
                        ) % {'ver': api_version, 'latest': 'latest'}
                raise exc.CommandError(msg)

            api_major_version = versions[0]
            return (api_major_version, magnum_api_version)

    def main(self, argv):

        # NOTE(Christoph Jansen): With Python 3.4 argv somehow becomes a Map.
        #                         This hack fixes it.
        argv = list(argv)

        # Parse args once to find version and debug settings
        parser = self.get_base_parser()
        (options, args) = parser.parse_known_args(argv)
        self.setup_debugging(options.debug)

        # NOTE(dtroyer): Hackery to handle --endpoint_type due to argparse
        #                thinking usage-list --end is ambiguous; but it
        #                works fine with only --endpoint-type present
        #                Go figure.
        if '--endpoint_type' in argv:
            spot = argv.index('--endpoint_type')
            argv[spot] = '--endpoint-type'

        # build available subcommands based on version
        (api_major_version, magnum_api_version) = (
            self._check_version(options.magnum_api_version))

        subcommand_parser = (
            self.get_subcommand_parser(api_major_version)
        )
        self.parser = subcommand_parser

        if options.help or not argv:
            subcommand_parser.print_help()
            return 0

        args = subcommand_parser.parse_args(argv)

        # Short-circuit and deal with help right away.
        # NOTE(jamespage): args.func is not guaranteed with python >= 3.4
        if not hasattr(args, 'func') or args.func == self.do_help:
            self.do_help(args)
            return 0
        elif args.func == self.do_bash_completion:
            self.do_bash_completion(args)
            return 0

        if not args.service_type:
            args.service_type = DEFAULT_SERVICE_TYPE

        if args.bypass_url:
            args.os_endpoint_override = args.bypass_url

        args.os_project_id = (args.os_project_id or args.os_tenant_id)
        args.os_project_name = (args.os_project_name or args.os_tenant_name)

        if not cliutils.isunauthenticated(args.func):
            if (not (args.os_token and
                     (args.os_auth_url or args.os_endpoint_override)) and
                not args.os_cloud
                ):

                if not (args.os_username or args.os_user_id):
                    raise exc.CommandError(
                        "You must provide a username via either --os-username "
                        "or via env[OS_USERNAME]"
                    )
                if not args.os_password:
                    raise exc.CommandError(
                        "You must provide a password via either "
                        "--os-password, env[OS_PASSWORD], or prompted "
                        "response"
                    )
                if (not args.os_project_name and not args.os_project_id):
                    raise exc.CommandError(
                        "You must provide a project name or project id via "
                        "--os-project-name, --os-project-id, "
                        "env[OS_PROJECT_NAME] or env[OS_PROJECT_ID]"
                    )
                if not args.os_auth_url:
                    raise exc.CommandError(
                        "You must provide an auth url via either "
                        "--os-auth-url or via env[OS_AUTH_URL]"
                    )
        try:
            client = {
                '1': client_v1,
            }[api_major_version]
        except KeyError:
            client = client_v1

        args.os_endpoint_type = (args.os_endpoint_type or args.endpoint_type)
        if args.os_endpoint_type:
            args.os_interface = args.os_endpoint_type

        if args.os_interface.endswith('URL'):
            args.os_interface = args.os_interface[:-3]

        self.cs = client.Client(
            cloud=args.os_cloud,
            user_id=args.os_user_id,
            username=args.os_username,
            password=args.os_password,
            auth_token=args.os_token,
            project_id=args.os_project_id,
            project_name=args.os_project_name,
            user_domain_id=args.os_user_domain_id,
            user_domain_name=args.os_user_domain_name,
            project_domain_id=args.os_project_domain_id,
            project_domain_name=args.os_project_domain_name,
            auth_url=args.os_auth_url,
            service_type=args.service_type,
            region_name=args.os_region_name,
            magnum_url=args.os_endpoint_override,
            interface=args.os_interface,
            insecure=args.insecure,
            api_version=args.magnum_api_version,
        )

        args.func(self.cs, args)

    def _dump_timings(self, timings):
        class Tyme(object):
            def __init__(self, url, seconds):
                self.url = url
                self.seconds = seconds
        results = [Tyme(url, end - start) for url, start, end in timings]
        total = 0.0
        for tyme in results:
            total += tyme.seconds
        results.append(Tyme("Total", total))
        cliutils.print_list(results, ["url", "seconds"], sortby_index=None)

    def do_bash_completion(self, _args):
        """Prints arguments for bash-completion.

        Prints all of the commands and options to stdout so that the
        magnum.bash_completion script doesn't have to hard code them.
        """
        commands = set()
        options = set()
        for sc_str, sc in self.subcommands.items():
            commands.add(sc_str)
            for option in sc._optionals._option_string_actions.keys():
                options.add(option)

        commands.remove('bash-completion')
        commands.remove('bash_completion')
        print(' '.join(commands | options))

    @cliutils.arg('command', metavar='<subcommand>', nargs='?',
                  help='Display help for <subcommand>.')
    def do_help(self, args):
        """Display help about this program or one of its subcommands."""
        # NOTE(jamespage): args.command is not guaranteed with python >= 3.4
        command = getattr(args, 'command', '')

        if command:
            if args.command in self.subcommands:
                self.subcommands[args.command].print_help()
            else:
                raise exc.CommandError("'%s' is not a valid subcommand" %
                                       args.command)
        else:
            self.parser.print_help()


# I'm picky about my shell help.
class OpenStackHelpFormatter(argparse.HelpFormatter):
    def start_section(self, heading):
        # Title-case the headings
        heading = '%s%s' % (heading[0].upper(), heading[1:])
        super(OpenStackHelpFormatter, self).start_section(heading)


def main():
    try:
        OpenStackMagnumShell().main(map(encodeutils.safe_decode, sys.argv[1:]))

    except Exception as e:
        logger.debug(e, exc_info=1)
        print("ERROR: %s" % encodeutils.safe_encode(six.text_type(e)),
              file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
