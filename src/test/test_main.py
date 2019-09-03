import os
import unittest
from src.kbase_workspace_client import WorkspaceClient, WorkspaceResponseError

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

    def test_handle_to_shock(self):
        valid_ws_id = '34819/10/1'
        data = _ws_client.req('get_objects2', {
            'objects': [{'ref': valid_ws_id}],
            'no_data': 1
        })['data'][0]
        handle_id = data['extracted_ids']['handle'][0]
        shock_id = _ws_client.handle_to_shock(handle_id)
        self.assertEqual(shock_id, 'd2d2ba03-b4f1-4ec9-91f0-99ea70991607')

    def test_download_shock_file(self):
        pass

    def test_generate_all_ids_for_workspace(self):
        ids = []
        for each in _ws_client.generate_all_ids_for_workspace(33192):
            ids.append(each)
        expected = [(1, 52), (4, 1), (7, 1), (9, 1), (10, 1), (11, 1), (12, 4), (19, 1)]
        self.assertEqual(ids, expected)

    def test_generate_all_ids_for_workspace_all_versions(self):
        count = 0
        for _ in _ws_client.generate_all_ids_for_workspace(33192, admin=True, latest=False):
            count += 1
        expected = [(1, 52), (4, 1), (7, 1), (9, 1), (10, 1), (11, 1), (12, 4), (19, 1)]
        self.assertTrue(count > len(expected))

    def test_err(self):
        _id = '0/0/0'
        with self.assertRaises(WorkspaceResponseError):
            _ws_client.req('get_objects2', {
                'objects': [{'ref': _id}],
                'no_data': 1
            })
