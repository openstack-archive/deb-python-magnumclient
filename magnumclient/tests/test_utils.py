# -*- coding: utf-8 -*-
#
# Copyright 2013 OpenStack LLC.
# All Rights Reserved.
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

import six

from magnumclient.common import utils
from magnumclient.openstack.common.apiclient import exceptions as exc
from magnumclient.openstack.common import cliutils
from magnumclient.tests import utils as test_utils


class CommonFiltersTest(test_utils.BaseTestCase):
    def test_limit(self):
        result = utils.common_filters(limit=42)
        self.assertEqual(['limit=42'], result)

    def test_limit_0(self):
        result = utils.common_filters(limit=0)
        self.assertEqual([], result)

    def test_other(self):
        for key in ('marker', 'sort_key', 'sort_dir'):
            result = utils.common_filters(**{key: 'test'})
            self.assertEqual(['%s=test' % key], result)


class SplitAndDeserializeTest(test_utils.BaseTestCase):

    def test_split_and_deserialize(self):
        ret = utils.split_and_deserialize('str=foo')
        self.assertEqual(('str', 'foo'), ret)

        ret = utils.split_and_deserialize('int=1')
        self.assertEqual(('int', 1), ret)

        ret = utils.split_and_deserialize('bool=false')
        self.assertEqual(('bool', False), ret)

        ret = utils.split_and_deserialize('list=[1, "foo", 2]')
        self.assertEqual(('list', [1, "foo", 2]), ret)

        ret = utils.split_and_deserialize('dict={"foo": 1}')
        self.assertEqual(('dict', {"foo": 1}), ret)

        ret = utils.split_and_deserialize('str_int="1"')
        self.assertEqual(('str_int', "1"), ret)

    def test_split_and_deserialize_fail(self):
        self.assertRaises(exc.CommandError,
                          utils.split_and_deserialize, 'foo:bar')


class ArgsArrayToPatchTest(test_utils.BaseTestCase):

    def test_args_array_to_patch(self):
        my_args = {
            'attributes': ['str=foo', 'int=1', 'bool=true',
                           'list=[1, 2, 3]', 'dict={"foo": "bar"}'],
            'op': 'add',
        }
        patch = utils.args_array_to_patch(my_args['op'],
                                          my_args['attributes'])
        self.assertEqual([{'op': 'add', 'value': 'foo', 'path': '/str'},
                          {'op': 'add', 'value': 1, 'path': '/int'},
                          {'op': 'add', 'value': True, 'path': '/bool'},
                          {'op': 'add', 'value': [1, 2, 3], 'path': '/list'},
                          {'op': 'add', 'value': {"foo": "bar"},
                           'path': '/dict'}], patch)

    def test_args_array_to_patch_format_error(self):
        my_args = {
            'attributes': ['foobar'],
            'op': 'add',
        }
        self.assertRaises(exc.CommandError, utils.args_array_to_patch,
                          my_args['op'], my_args['attributes'])

    def test_args_array_to_patch_remove(self):
        my_args = {
            'attributes': ['/foo', 'extra/bar'],
            'op': 'remove',
        }
        patch = utils.args_array_to_patch(my_args['op'],
                                          my_args['attributes'])
        self.assertEqual([{'op': 'remove', 'path': '/foo'},
                          {'op': 'remove', 'path': '/extra/bar'}], patch)


class FormatLabelsTest(test_utils.BaseTestCase):

    def test_format_label_none(self):
        self.assertEqual({}, utils.format_labels(None))

    def test_format_labels(self):
        l = utils.format_labels([
            'K1=V1,K2=V2,'
            'K3=V3,K4=V4,'
            'K5=V5'])
        self.assertEqual({'K1': 'V1',
                          'K2': 'V2',
                          'K3': 'V3',
                          'K4': 'V4',
                          'K5': 'V5'
                          }, l)

    def test_format_labels_split(self):
        l = utils.format_labels([
            'K1=V1,'
            'K2=V22222222222222222222222222222'
            '222222222222222222222222222,'
            'K3=3.3.3.3'])
        self.assertEqual({'K1': 'V1',
                          'K2': 'V22222222222222222222222222222'
                          '222222222222222222222222222',
                          'K3': '3.3.3.3'}, l)

    def test_format_labels_multiple(self):
        l = utils.format_labels([
            'K1=V1',
            'K2=V22222222222222222222222222222'
            '222222222222222222222222222',
            'K3=3.3.3.3'])
        self.assertEqual({'K1': 'V1',
                          'K2': 'V22222222222222222222222222222'
                          '222222222222222222222222222',
                          'K3': '3.3.3.3'}, l)

    def test_format_labels_multiple_colon_values(self):
        l = utils.format_labels([
            'K1=V1',
            'K2=V2,V22,V222,V2222',
            'K3=3.3.3.3'])
        self.assertEqual({'K1': 'V1',
                          'K2': 'V2,V22,V222,V2222',
                          'K3': '3.3.3.3'}, l)

    def test_format_labels_parse_comma_false(self):
        l = utils.format_labels(
            ['K1=V1,K2=2.2.2.2,K=V'],
            parse_comma=False)
        self.assertEqual({'K1': 'V1,K2=2.2.2.2,K=V'}, l)

    def test_format_labels_multiple_values_per_labels(self):
        l = utils.format_labels([
            'K1=V1',
            'K1=V2'])
        self.assertIn('K1', l)
        self.assertIn('V1', l['K1'])
        self.assertIn('V2', l['K1'])

    def test_format_label_bad_label(self):
        labels = ['K1=V1,K22.2.2.2']
        ex = self.assertRaises(exc.CommandError,
                               utils.format_labels, labels)
        self.assertEqual('labels must be a list of KEY=VALUE '
                         'not K22.2.2.2', str(ex))

    def test_format_multiple_bad_label(self):
        labels = ['K1=V1', 'K22.2.2.2']
        ex = self.assertRaises(exc.CommandError,
                               utils.format_labels, labels)
        self.assertEqual('labels must be a list of KEY=VALUE '
                         'not K22.2.2.2', str(ex))


class CliUtilsTest(test_utils.BaseTestCase):

    def test_keys_and_vals_to_strs(self):
        dict_in = {u'a': u'1', u'b': {u'x': 1, 'y': u'2', u'z': u'3'}, 'c': 7}
        dict_exp = {'a': '1', 'b': {'x': 1, 'y': '2', 'z': '3'}, 'c': 7}
        dict_out = cliutils.keys_and_vals_to_strs(dict_in)
        self.assertEqual(six.text_type(dict_exp), six.text_type(dict_out))
