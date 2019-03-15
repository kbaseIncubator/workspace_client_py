import os
import unittest
from kbase_workspace_client import WorkspaceClient, WorkspaceResponseError

if not os.environ.get('TEST_TOKEN'):
    raise RuntimeError("TEST_TOKEN environment variable is required.")

_URL = "https://ci.kbase.us/services/ws"
_ws_client = WorkspaceClient(url=_URL, token=os.environ['TEST_TOKEN'])


class TestMain(unittest.TestCase):

    def test_req(self):
        valid_ws_id = '15/38/4'
        objs = _ws_client.req('get_objects2', {
            'objects': [{'ref': valid_ws_id}],
            'no_data': 1
        })
        self.assertTrue(objs['data'])

    def test_admin_req(self):
        valid_ws_id = '15/38/4'
        objs = _ws_client.admin_req('getObjects', {
            'objects': [{'ref': valid_ws_id}],
            'no_data': 1
        })
        self.assertTrue(objs['data'])

    def test_req_download(self):
        valid_ws_id = '15/38/4'
        _ws_client.admin_req_download('getObjects', {
            'objects': [{'ref': valid_ws_id}],
            'no_data': 1
        }, 'tmp.json')
        with open('tmp.json') as fd:
            contents = fd.read()
            self.assertTrue(contents)
        os.remove('tmp.json')

    def test_err(self):
        _id = '0/0/0'
        with self.assertRaises(WorkspaceResponseError):
            _ws_client.req('get_objects2', {
                'objects': [{'ref': _id}],
                'no_data': 1
            })