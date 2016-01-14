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

import mock

from magnumclient.tests.v1 import shell_test_base


class ShellTest(shell_test_base.TestCommandLineArgument):

    @mock.patch('magnumclient.v1.baymodels.BayModelManager.create')
    def test_baymodel_create_success(self, mock_create):
        self._test_arg_success('baymodel-create '
                               '--name test '
                               '--image-id test_image '
                               '--keypair-id test_keypair '
                               '--external-network-id test_net '
                               '--coe swarm '
                               '--dns-nameserver test_dns '
                               '--flavor-id test_flavor '
                               '--fixed-network public '
                               '--network-driver test_driver '
                               '--labels key=val '
                               '--master-flavor-id test_flavor '
                               '--docker-volume-size 10'
                               '--public')
        self.assertTrue(mock_create.called)

        self._test_arg_success('baymodel-create '
                               '--keypair-id test_keypair '
                               '--external-network-id test_net '
                               '--image-id test_image '
                               '--coe kubernetes '
                               '--name test ')

        self.assertTrue(mock_create.called)

    @mock.patch('magnumclient.v1.baymodels.BayModelManager.create')
    def test_baymodel_create_public_success(self, mock_create):
        self._test_arg_success('baymodel-create '
                               '--name test --network-driver test_driver '
                               '--keypair-id test_keypair '
                               '--external-network-id test_net '
                               '--image-id test_image '
                               '--coe swarm'
                               '--public')
        self.assertTrue(mock_create.called)

    @mock.patch('magnumclient.v1.baymodels.BayModelManager.create')
    def test_baymodel_create_success_with_master_flavor(self, mock_create):
        self._test_arg_success('baymodel-create '
                               '--name test '
                               '--image-id test_image '
                               '--keypair-id test_keypair '
                               '--external-network-id test_net '
                               '--coe swarm '
                               '--dns-nameserver test_dns '
                               '--master-flavor-id test_flavor')
        self.assertTrue(mock_create.called)

    @mock.patch('magnumclient.v1.baymodels.BayModelManager.create')
    def test_baymodel_create_docker_vol_size_success(self, mock_create):
        self._test_arg_success('baymodel-create '
                               '--name test --docker-volume-size 4514 '
                               '--keypair-id test_keypair '
                               '--external-network-id test_net '
                               '--image-id test_image '
                               '--coe swarm'
                               )
        self.assertTrue(mock_create.called)

    @mock.patch('magnumclient.v1.baymodels.BayModelManager.create')
    def test_baymodel_create_fixed_network_success(self, mock_create):
        self._test_arg_success('baymodel-create '
                               '--name test --fixed-network private '
                               '--keypair-id test_keypair '
                               '--external-network-id test_net '
                               '--image-id test_image '
                               '--coe swarm')
        self.assertTrue(mock_create.called)

    @mock.patch('magnumclient.v1.baymodels.BayModelManager.create')
    def test_baymodel_create_network_driver_success(self, mock_create):
        self._test_arg_success('baymodel-create '
                               '--name test --network-driver test_driver '
                               '--keypair-id test_keypair '
                               '--external-network-id test_net '
                               '--image-id test_image '
                               '--coe swarm')
        self.assertTrue(mock_create.called)

    @mock.patch('magnumclient.v1.baymodels.BayModelManager.create')
    def test_baymodel_create_ssh_authorized_key_success(self, mock_create):
        self._test_arg_success('baymodel-create '
                               '--name test '
                               '--keypair-id test_keypair '
                               '--external-network-id test_net '
                               '--image-id test_image '
                               '--coe swarm '
                               '--ssh-authorized-key test_key '
                               )
        self.assertTrue(mock_create.called)

    @mock.patch('magnumclient.v1.baymodels.BayModelManager.create')
    def test_baymodel_create_http_proxy_success(self, mock_create):
        self._test_arg_success('baymodel-create '
                               '--name test --fixed-network private '
                               '--keypair-id test_keypair '
                               '--external-network-id test_net '
                               '--image-id test_image '
                               '--coe swarm '
                               '--http-proxy http_proxy ')
        self.assertTrue(mock_create.called)

    @mock.patch('magnumclient.v1.baymodels.BayModelManager.create')
    def test_baymodel_create_https_proxy_success(self, mock_create):
        self._test_arg_success('baymodel-create '
                               '--name test --fixed-network private '
                               '--keypair-id test_keypair '
                               '--external-network-id test_net '
                               '--image-id test_image '
                               '--coe swarm '
                               '--https-proxy https_proxy ')
        self.assertTrue(mock_create.called)

    @mock.patch('magnumclient.v1.baymodels.BayModelManager.create')
    def test_baymodel_create_no_proxy_success(self, mock_create):
        self._test_arg_success('baymodel-create '
                               '--name test --fixed-network private '
                               '--keypair-id test_keypair '
                               '--external-network-id test_net '
                               '--image-id test_image '
                               '--coe swarm '
                               '--no-proxy no_proxy ')

    @mock.patch('magnumclient.v1.baymodels.BayModelManager.create')
    def test_baymodel_create_labels_success(self, mock_create):
        self._test_arg_success('baymodel-create '
                               '--name test '
                               '--labels key=val '
                               '--keypair-id test_keypair '
                               '--external-network-id test_net '
                               '--image-id test_image '
                               '--coe swarm')
        self.assertTrue(mock_create.called)

    @mock.patch('magnumclient.v1.baymodels.BayModelManager.create')
    def test_baymodel_create_separate_labels_success(self, mock_create):
        self._test_arg_success('baymodel-create '
                               '--name test '
                               '--labels key1=val1 '
                               '--labels key2=val2 '
                               '--keypair-id test_keypair '
                               '--external-network-id test_net '
                               '--image-id test_image '
                               '--coe swarm')
        self.assertTrue(mock_create.called)

    @mock.patch('magnumclient.v1.baymodels.BayModelManager.create')
    def test_baymodel_create_combined_labels_success(self, mock_create):
        self._test_arg_success('baymodel-create '
                               '--name test '
                               '--labels key1=val1,key2=val2 '
                               '--keypair-id test_keypair '
                               '--external-network-id test_net '
                               '--image-id test_image '
                               '--coe swarm')
        self.assertTrue(mock_create.called)

    @mock.patch('magnumclient.v1.baymodels.BayModelManager.create')
    def test_baymodel_create_failure_few_arg(self, mock_create):
        self._test_arg_failure('baymodel-create '
                               '--name test', self._mandatory_arg_error)
        self.assertFalse(mock_create.called)

        self._test_arg_failure('baymodel-create '
                               '--image-id test', self._mandatory_arg_error)
        self.assertFalse(mock_create.called)

        self._test_arg_failure('baymodel-create '
                               '--keypair-id test', self._mandatory_arg_error)
        self.assertFalse(mock_create.called)

        self._test_arg_failure('baymodel-create '
                               '--external-network-id test',
                               self._mandatory_arg_error)
        self.assertFalse(mock_create.called)

        self._test_arg_failure('baymodel-create '
                               '--coe test', self._mandatory_arg_error)
        self.assertFalse(mock_create.called)

        self._test_arg_failure('baymodel-create', self._mandatory_arg_error)
        self.assertFalse(mock_create.called)

    @mock.patch('magnumclient.v1.baymodels.BayModelManager.get')
    def test_baymodel_show_success(self, mock_show):
        self._test_arg_success('baymodel-show xxx')
        self.assertTrue(mock_show.called)

    @mock.patch('magnumclient.v1.baymodels.BayModelManager.get')
    def test_baymodel_show_failure_no_arg(self, mock_show):
        self._test_arg_failure('baymodel-show', self._few_argument_error)
        self.assertFalse(mock_show.called)

    @mock.patch('magnumclient.v1.baymodels.BayModelManager.delete')
    def test_baymodel_delete_success(self, mock_delete):
        self._test_arg_success('baymodel-delete xxx')
        self.assertTrue(mock_delete.called)
        self.assertEqual(1, mock_delete.call_count)

    @mock.patch('magnumclient.v1.baymodels.BayModelManager.delete')
    def test_baymodel_delete_multiple_id_success(self, mock_delete):
        self._test_arg_success('baymodel-delete xxx xyz')
        self.assertTrue(mock_delete.called)
        self.assertEqual(2, mock_delete.call_count)

    @mock.patch('magnumclient.v1.baymodels.BayModelManager.delete')
    def test_baymodel_delete_failure_no_arg(self, mock_delete):
        self._test_arg_failure('baymodel-delete', self._few_argument_error)
        self.assertFalse(mock_delete.called)

    @mock.patch('magnumclient.v1.baymodels.BayModelManager.list')
    def test_baymodel_list_success(self, mock_list):
        self._test_arg_success('baymodel-list')
        self.assertTrue(mock_list.called)

    @mock.patch('magnumclient.v1.baymodels.BayModelManager.list')
    def test_baymodel_list_failure(self, mock_list):
        self._test_arg_failure('baymodel-list --wrong',
                               self._unrecognized_arg_error)
        self.assertFalse(mock_list.called)
