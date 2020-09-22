from collections import namedtuple
from typing import Optional, Any, Generator, List
import json
import os
import requests
import time

from kbase_workspace_client.contigset_to_fasta import contigset_to_fasta
from kbase_workspace_client.exceptions import (
    WorkspaceResponseError,
    UnauthorizedShockDownload,
    MissingShockFile,
    InvalidWSType,
    FileExists,
    InvalidGenome,
)

# Named tuples for object info and workspace info
ObjInfo = namedtuple('ObjInfo', [
  "objid",
  "name",
  "type",
  "save_date",
  "version",
  "saved_by",
  "wsid",
  "workspace",
  "chsum",
  "size",
  "meta",
])
WSInfo = namedtuple('WSInfo', [
  "id",
  "workspace",
  "owner",
  "moddate",
  "max_objid",
  "user_permission",
  "globalread",
  "lockstat",
  "metadata",
])


def _post_req(payload: dict, url: str, token: str, file_path: str = None) -> Any:
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


def _validate_file_for_writing(dest_path: str) -> None:
    """Validate that a path points to a non-existent file in a writable directory."""
    if os.path.isfile(dest_path):
        raise IOError(f"File path already exists: {dest_path}")
    try:
        fd = open(dest_path, 'wb')
        fd.close()
    except IOError:
        raise IOError(f"File path is not writable: {dest_path}")


class WorkspaceClient:

    def __init__(self, url: str, token: str = None):
        """
        Instantiate the workspace client.
        Args:
            url: URL of the workspace service with the root path
            token: User or service authentication token from KBase. Optional.
        """
        self._url = url.strip('/')
        self._ws_url = url + '/ws'
        self._token = token

    def req(self, method: str, params: dict) -> Any:
        """
        Make a normal request to the workspace.
        Args:
            method: workspace method name (must be a funcdef in the KIDL spec)
            params: parameters as python dicts, lists, and values
        Returns:
            python data (dicts/lists) of response data from the workspace.
        Raises:
            WorkspaceResponseError on an unsuccessful request.
        """
        _id = int(time.time() * 1000)
        payload = {'version': '1.1', 'id': _id, 'method': method, 'params': [params]}
        return _post_req(payload, self._ws_url, self._token)

    def generate_obj_infos(
            self,
            wsid: int,
            minid: int = 1,
            maxid: Optional[int] = None,
            latest: bool = True,
            admin: bool = False) -> Generator[list]:
        """
        Generator, yielding all object IDs + version IDs in a workspace.
        This handles the 10k pagination and will generate *all* ids.
        Args:
            wsid: workspace ID
            latest: Generate only the latest version of each obj, or generate
                all versions of all objects.
            admin: Make the "list_objects" request as a Workspace administrator
        Yields:
            Object info tuples (as python lists)
        """
        params = {"ids": [wsid]}  # type: dict
        if maxid:
            params['maxObjectID'] = maxid
        if not latest:
            params['showAllVersions'] = 1
        while True:
            params['minObjectID'] = minid
            if admin:
                part = self.admin_req("listObjects", params)
            else:
                part = self.req("list_objects", params)
            if len(part) < 1:
                break
            minid = part[-1][0] + 1
            for obj_info in part:
                yield obj_info

    def admin_req(self, method: str, params: dict) -> Any:
        """
        Make a special workspace admin command.
        Args:
            method: workspace method name (must be a funcdef in the KIDL spec)
            params - parameters as python dicts, lists, and values
        Returns:
            python data (dicts/lists) of response data from the workspace.
        Raises:
            WorkspaceResponseError on an unsuccessful request.
        """
        payload = {
            'version': '1.1',
            'method': 'Workspace.administer',
            'params': [{'command': method, 'params': params}]
        }
        return _post_req(payload, self._ws_url, self._token)

    def req_download(self, method: str, params: dict, dest_path: str) -> None:
        """
        Make a workspace request and download the response to a file (streaming)
        Args:
            method - workspace method name (must be a funcdef in the KIDL spec)
            params - parameters as python dicts, lists, and values
            dest_path - filepath where you would like to write out results
        Returns:
            None when the request is complete and the file is written.
        Raises:
            WorkspaceResponseError on an unsuccessful request.
        """
        _validate_file_for_writing(dest_path)
        payload = {'version': '1.1', 'method': method, 'params': [params]}
        _post_req(payload, self._ws_url, self._token, dest_path)

    def admin_req_download(self, method: str, params: dict, dest_path: str) -> None:
        """
        Make an admin command and download the response to a file (streaming)
        Args:
            method - workspace method name (must be a funcdef in the KIDL spec)
            params - parameters as python dicts, lists, and values
            dest_path - filepath where you would like to write out results
        Returns:
            None when the request is complete and the file is written.
        Raises:
            WorkspaceResponseError on an unsuccessful request.
        """
        _validate_file_for_writing(dest_path)
        payload = {
            'version': '1.1',
            'method': 'Workspace.administer',
            'params': [{'command': method, 'params': params}]
        }
        _post_req(payload, self._ws_url, self._token, dest_path)

    def handle_to_shock(self, handle: str) -> str:
        """
        Convert a handle ID to a shock ID
        Args:
            handle: handle service ID
        Returns:
            The shock node ID
        """
        headers = {'Content-Type': 'application/json'}
        if self._token:
            headers['Authorization'] = self._token
        request_data = {
            'method': 'AbstractHandle.hids_to_handles',
            'params': [[handle]],
            'id': "0"
        }
        resp = requests.post(
            self._url + '/handle_service',
            data=json.dumps(request_data),
            headers=headers
        )
        if not resp.ok:
            raise RuntimeError(f"Error from handle_service: {resp.text}")
        return resp.json()['result'][0][0]['id']

    def download_shock_file(self, shock_id: str, dest_path: str) -> None:
        """
        Download a file from shock.
        Args:
            shock_id
            dest_path
        Returns:
            None when the file finishes downloading
        Raises:
            UnauthorizedShockDownload or MissingShockFile on failure
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

    def download_assembly_fasta(self, ref: str, save_dir: str, admin: bool = False) -> str:
        """
        Download an Assembly object as fasta.
        Args:
            ref: a workspace reference ID in the form 'workspace_id/object_id/version'
            save_dir: the path of a directory in which to save the fasta file
            admin: whether to make the request as a Workspace administrator
        Returns:
            an absolute path of the downloaded fasta file.
        """
        ws_obj = _download_obj(self, ref, admin=admin)
        valid_types = ['KBaseGenomeAnnotations.Assembly', 'KBaseGenomes.ContigSet']
        _validate_obj_type(ws_obj=ws_obj, types=valid_types)
        (obj_name, obj_type) = (ws_obj['info'][1], ws_obj['info'][2])
        output_path = os.path.abspath(os.path.join(save_dir, obj_name + '.fasta'))
        if os.path.exists(output_path):
            raise FileExists('File already exists at ' + output_path)
        if 'ContigSet' in obj_type:
            # Write out ContigSet data into a fasta file
            contigset_to_fasta(ws_obj, output_path)
        else:
            # Download a linked fasta file to the save directory
            data = ws_obj['data']
            if 'fasta_handle_info' in data and 'shock_id' in data['fasta_handle_info']:
                shock_id = data['fasta_handle_info']['shock_id']
            else:
                handle_id = data['fasta_handle_ref']
                shock_id = self.handle_to_shock(handle_id)
            self.download_shock_file(shock_id, output_path)
        return output_path

    def download_reads_fastq(self, ref: str, save_dir: str, admin: bool = False) -> List[str]:
        """
        Download genome reads data as fastq.

        If the reads are paired-end and non-interleaved, you will get two files, one for the forward
        (left) reads and one for the reverse (right) reads. Otherwise, you will get one file.

        File-names:
        - Paired ends and interleaved get the file ending of '.paired.interleaved.fastq'
        - Paired ends and non-interleaved get the file ending of '.paired.fwd.fastq' and
            '.paired.rev.fastq'
        - Single ends get the file ending of '.single.fastq'

        Keyword arguments:
            ref: a workspace reference ID in the form 'workspace_id/object_id/version'
            save_dir: the path of a directory in which to save the fasta file
        Returns:
            a list of paths of the downloaded fastq files.
        """
        # Fetch the workspace object and check its type
        ws_obj = _download_obj(self, ref, admin=admin)
        (obj_name, obj_type) = (ws_obj['info'][1], ws_obj['info'][2])
        valid_types = {
            'single': 'SingleEndLibrary',
            'paired': 'PairedEndLibrary',
        }
        if valid_types['single'] in obj_type:
            # One file to download
            shock_id = ws_obj['data']['lib']['file']['id']
            path = os.path.join(save_dir, obj_name + '.single.fastq')
            to_download = [(shock_id, path)]
        elif valid_types['paired'] in obj_type:
            interleaved = ws_obj['data']['interleaved']
            if interleaved:
                # One file to download
                shock_id = ws_obj['data']['lib1']['file']['id']
                path = os.path.join(save_dir, obj_name + '.paired.interleaved.fastq')
                to_download = [(shock_id, path)]
            else:
                # Two files to download (for left and right reads)
                shock_id_fwd = ws_obj['data']['lib1']['file']['id']
                shock_id_rev = ws_obj['data']['lib2']['file']['id']
                path_fwd = os.path.join(save_dir, obj_name + '.paired.fwd.fastq')
                path_rev = os.path.join(save_dir, obj_name + '.paired.rev.fastq')
                to_download = [(shock_id_fwd, path_fwd), (shock_id_rev, path_rev)]
        else:
            # Unrecognized type
            raise InvalidWSType(given=obj_type, valid_types=valid_types.values())
        # Download each shock id to each path
        for (shock_id, path) in to_download:
            self.download_shock_file(shock_id, path)
        # Return a list of the output paths that we have downloaded
        output_paths = map(lambda pair: pair[1], to_download)
        return list(output_paths)

    def get_assembly_from_genome(self, ref: str, admin: bool = False) -> str:
        """
        Given a Genome object, fetch the reference to its Assembly object on the workspace.
        Args:
            ref is a workspace reference ID in the form 'workspace_id/object_id/version'
        Returns:
            workspace reference to an assembly object
        """
        # Fetch the workspace object and check its type
        ws_obj = _download_obj(self, ref, admin=admin)
        _validate_obj_type(ws_obj, ['Genome'])
        # Extract out the assembly reference from the workspace data
        ws_data = ws_obj['data']
        assembly_ref = ws_data.get('contigset_ref') or ws_data.get('assembly_ref')
        if not assembly_ref:
            raise InvalidGenome('Genome ' + ref + ' has no assembly or contigset references')
        # Return a reference path of `genome_ref;assembly_ref`
        ref_path = ref + ';' + assembly_ref
        return ref_path

    def find_narrative(self, wsid: int, admin: bool = False) -> Optional[ObjInfo]:
        """
        Fetch the narrative object out of a workspace.
        This will be slow if the workspace has tons of objects and the
        narrative is not close to the beginning.
        Args:
            wsid: workspace ID
            admin: whether to make the request as a Workspace administrator
        Returns:
            None if no narrative present, or an ObjInfo for the narrative object.
        """
        for obj_info_raw in self.generate_obj_infos(wsid, admin=admin):
            obj_info = ObjInfo(*obj_info_raw)
            if obj_info.type.startswith("KBaseNarrative.Narrative"):
                return obj_info


def _download_obj(client, ref: str, data: bool = True, admin: bool = False) -> dict:
    """Download an object with get_objects2."""
    params = {'objects': [{'ref': ref}]}  # type: dict
    if not data:
        params['no_data'] = 1
    if admin:
        ws_obj = client.admin_req("getObjects", params)
    else:
        ws_obj = client.req("get_objects2", params)
    return ws_obj['data'][0]


def _validate_obj_type(ws_obj: dict, types: List[str]) -> None:
    """
    Given a workspace object, validate that its types match any of the strings in `types`.
    Args:
        ws_obj: a workspace reference in the form of 'workspace_id/object_id/version'
        types: a list of string type names to match against
    Raises:
        InvalidWSType error if given object not in type list
    """
    ws_type = ws_obj['info'][2]
    if all(t not in ws_type for t in types):
        raise InvalidWSType(given=ws_type, valid_types=types)
