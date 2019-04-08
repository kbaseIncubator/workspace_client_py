import os
import json
import requests
from uuid import uuid4

from .exceptions import WorkspaceResponseError, UnauthorizedShockDownload, MissingShockFile


def _post_req(payload, url, token, file_path=None):
    """Make a post request to the workspace server and process the response."""
    headers = {'Authorization': token}
    with requests.post(url, data=json.dumps(payload), headers=headers, stream=True) as resp:
        if not resp.ok:
            raise WorkspaceResponseError(resp)
        if file_path:
            # Stream the response to a file
            with open(file_path, 'wb') as fd:
                for chunk in resp.iter_content(chunk_size=1024):
                    fd.write(chunk)
        else:
            # Parse the response as JSON in memory and check for errors
            resp_json = resp.json()
            if 'error' in resp_json:
                raise WorkspaceResponseError(resp)
            elif 'result' not in resp_json or not len(resp_json['result']):
                raise WorkspaceResponseError(resp)
            return resp_json['result'][0]


def _validate_file_for_writing(dest_path):
    """Validate that a path points to a non-existent file in a writable directory."""
    if os.path.isfile(dest_path):
        raise IOError(f"File path already exists: {dest_path}")
    try:
        fd = open(dest_path, 'wb')
        fd.close()
    except IOError:
        raise IOError(f"File path is not writable: {dest_path}")


class WorkspaceClient:

    def __init__(self, url, token=None):
        """
        Instantiate the workspace client.
        Args:
            url - URL of the workspace service with the root path
            token - User or service authentication token from KBase. Optional.
        """
        self._url = url
        self._ws_url = url
        self._token = token

    def req(self, method, params):
        """
        Make a normal request to the workspace.
        Args:
            method - workspace method name (must be a funcdef in the KIDL spec)
            params - parameters as python dicts, lists, and values
        Returns python data (dicts/lists) of response data from the workspace.
        Raises a WorkspaceResponseError on an unsuccessful request.
        """
        payload = {'version': '1.1', 'method': method, 'params': [params]}
        return _post_req(payload, self._ws_url, self._token)

    def admin_req(self, method, params):
        """
        Make a special workspace admin command.
        Args:
            method - workspace method name (must be a funcdef in the KIDL spec)
            params - parameters as python dicts, lists, and values
        Returns python data (dicts/lists) of response data from the workspace.
        Raises a WorkspaceResponseError on an unsuccessful request.
        """
        payload = {
            'version': '1.1',
            'method': 'Workspace.administer',
            'params': [{'command': method, 'params': params}]
        }
        return _post_req(payload, self._ws_url, self._token)

    def req_download(self, method, params, dest_path):
        """
        Make a workspace request and download the response to a file (streaming)
        Args:
            method - workspace method name (must be a funcdef in the KIDL spec)
            params - parameters as python dicts, lists, and values
            dest_path - filepath where you would like to write out results
        Returns None when the request is complete and the file is written.
        Raises a WorkspaceResponseError on an unsuccessful request.
        """
        _validate_file_for_writing(dest_path)
        payload = {'version': '1.1', 'method': method, 'params': [params]}
        _post_req(payload, self._ws_url, self._token, dest_path)

    def admin_req_download(self, method, params, dest_path):
        """
        Make an admin command and download the response to a file (streaming)
        Args:
            method - workspace method name (must be a funcdef in the KIDL spec)
            params - parameters as python dicts, lists, and values
            dest_path - filepath where you would like to write out results
        Returns None when the request is complete and the file is written.
        Raises a WorkspaceResponseError on an unsuccessful request.
        """
        _validate_file_for_writing(dest_path)
        payload = {
            'version': '1.1',
            'method': 'Workspace.administer',
            'params': [{'command': method, 'params': params}]
        }
        return _post_req(payload, self._ws_url, self._token, dest_path)

    def handle_to_shock(self, handle):
        """
        Convert a handle ID to a shock ID
        Args:
            handle
        Returns the shock ID as a string
        """
        headers = {'Content-Type': 'application/json'}
        if self._token:
            headers['Authorization'] = self._token
        request_data = {
            'method': 'AbstractHandle.hids_to_handles',
            'params': [[handle]],
            'id': str(uuid4())
        }
        resp = requests.post(
            self._url.replace('/ws', '/handle_service'),
            data=json.dumps(request_data),
            headers=headers
        )
        if not resp.ok:
            raise RuntimeError(f"Error from handle_service: {resp.text}")
        return resp.json()['result'][0][0]['id']

    def download_shock_file(self, shock_id, dest_path):
        """
        Download a file from shock.
        Args:
            shock_id
            dest_path
        Returns None when the file finishes downloading
        Raises UnauthorizedShockDownload or MissingShockFile on failure
        """
        _validate_file_for_writing(dest_path)
        headers = {'Authorization': ('OAuth ' + self._token) if self._token else None}
        # First, fetch some metadata about the file from shock
        shock_url = self._url + '/shock-api'
        node_url = shock_url + '/node/' + shock_id
        response = requests.get(node_url, headers=headers, allow_redirects=True)
        if not response.ok:
            raise RuntimeError(f"Error from shock: {response.text}")
        metadata = response.json()
        # Make sure the shock file is present and valid
        if metadata['status'] == 401:
            raise UnauthorizedShockDownload(shock_id)
        if metadata['status'] == 404:
            raise MissingShockFile(shock_id)
        # Fetch and stream the actual file to dest_path
        with requests.get(node_url + '?download_raw',
                          headers=headers, allow_redirects=True, stream=True) as resp:
            with open(dest_path, 'wb') as fwrite:
                for block in resp.iter_content(1024):
                    fwrite.write(block)
