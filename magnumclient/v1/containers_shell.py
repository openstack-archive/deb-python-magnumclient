# Copyright 2015 NEC Corporation.  All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import json

from magnumclient.common import utils as magnum_utils
from magnumclient.openstack.common import cliutils as utils


def _show_container(container):
    utils.print_dict(container._info)


@utils.arg('--name',
           metavar='<name>',
           help='name of the container')
@utils.arg('--image',
           required=True,
           metavar='<image>',
           help='name or ID of the image')
@utils.arg('--bay',
           required=True,
           metavar='<bay>',
           help='ID or name of the bay.')
@utils.arg('--command',
           metavar='<command>',
           help='Send command to the container')
@utils.arg('--memory',
           metavar='<memory>',
           help='The container memory size (format: <number><optional unit>, '
                'where unit = b, k, m or g)')
def do_container_create(cs, args):
    """Create a container."""
    bay = cs.bays.get(args.bay)
    if bay.status not in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
        print('Bay status for %s is: %s. We can not create a %s there'
              ' until the status is CREATE_COMPLETE or UPDATE_COMPLETE.' %
              (bay.uuid, bay.status, "pod"))
        return
    opts = {}
    opts['name'] = args.name
    opts['image'] = args.image
    opts['bay_uuid'] = bay.uuid
    opts['command'] = args.command
    opts['memory'] = args.memory
    _show_container(cs.containers.create(**opts))


def do_container_list(cs, args):
    """Print a list of available containers."""
    containers = cs.containers.list()
    columns = ('uuid', 'name', 'status')
    utils.print_list(containers, columns,
                     {'versions': magnum_utils.print_list_field('versions')})


@utils.arg('containers',
           metavar='<container>',
           nargs='+',
           help='ID or name of the (container)s to delete.')
def do_container_delete(cs, args):
    """Delete specified containers."""
    for container in args.containers:
        try:
            cs.containers.delete(container)
        except Exception as e:
            print("Delete for container %(container)s failed: %(e)s" %
                  {'container': container, 'e': e})


@utils.arg('container',
           metavar='<container>',
           help='ID or name of the container to show.')
@utils.arg('--json',
           action='store_true',
           default=False,
           help='Print JSON representation of the container.')
def do_container_show(cs, args):
    """Show details of a container."""
    container = cs.containers.get(args.container)
    if args.json:
        print(json.dumps(container._info))
    else:
        _show_container(container)


@utils.arg('containers',
           metavar='<container>',
           nargs='+',
           help='ID or name of the (container)s to start.')
def do_container_reboot(cs, args):
    """Reboot specified containers."""
    for container in args.containers:
        try:
            cs.containers.reboot(container)
        except Exception as e:
            print("Reboot for container %(container)s failed: %(e)s" %
                  {'container': container, 'e': e})


@utils.arg('containers',
           metavar='<container>',
           nargs='+',
           help='ID or name of the (container)s to start.')
def do_container_stop(cs, args):
    """Stop specified containers."""
    for container in args.containers:
        try:
            cs.containers.stop(container)
        except Exception as e:
            print("Stop for container %(container)s failed: %(e)s" %
                  {'container': container, 'e': e})


@utils.arg('containers',
           metavar='<container>',
           nargs='+',
           help='ID of the (container)s to start.')
def do_container_start(cs, args):
    """Start specified containers."""
    for container in args.containers:
        try:
            cs.containers.start(container)
        except Exception as e:
            print("Start for container %(container)s failed: %(e)s" %
                  {'container': container, 'e': e})


@utils.arg('containers',
           metavar='<container>',
           nargs='+',
           help='ID or name of the (container)s to start.')
def do_container_pause(cs, args):
    """Pause specified containers."""
    for container in args.containers:
        try:
            cs.containers.pause(container)
        except Exception as e:
            print("Pause for container %(container)s failed: %(e)s" %
                  {'container': container, 'e': e})


@utils.arg('containers',
           metavar='<container>',
           nargs='+',
           help='ID or name of the (container)s to start.')
def do_container_unpause(cs, args):
    """Unpause specified containers."""
    for container in args.containers:
        try:
            cs.containers.unpause(container)
        except Exception as e:
            print("Unpause for container %(container)s failed: %(e)s" %
                  {'container': container, 'e': e})


@utils.arg('container',
           metavar='<container>',
           help='ID or name of the container to start.')
def do_container_logs(cs, args):
    """Get logs of a container."""
    logs = cs.containers.logs(args.container)
    print(logs)


@utils.arg('container',
           metavar='<container>',
           help='ID or name of the container to start.')
@utils.arg('--command',
           required=True,
           metavar='<command>',
           help='The command to execute')
def do_container_exec(cs, args):
    """Execute command in a container."""
    output = cs.containers.execute(args.container, args.command)
    print(output)
