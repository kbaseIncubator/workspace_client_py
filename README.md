# KBase Workspace - Python Client

Generic, pip-installable workspace client for [KBase's workspace service](https://kbase.us/services/ws/docs).

This package covers many common tasks when working with the KBase Workspace.

Note that you cannot write any data to the workspace using this module. You'll have to use the KBase SDK for that.

## Installation

Install with pip:

```sh
pip install --extra-index-url https://pypi.anaconda.org/kbase/simple \
    kbase-workspace-client==0.2.0
```

## Usage

Import and initialize the `WorkspaceClient` class:

```py
from kbase_workspace_client import WorkspaceClient

ws_client = WorkspaceClient(
  url="https://appdev.kbase.us/services/",
  token="my_authentication_token"
)
```

`url` should be the base URL for the KBase services, which will be one of:

* `https://ci.kbase.us/services/`
* `https://appdev.kbase.us/services/`
* `https://kbase.us/services/`

`token` should be a developer or service authentication token.

## API

### ws_client.req(method, params)

Call a workspace method and receive the results as python dictionaries/lists. If the request is unsuccessful, then this raises a `WorkspaceResponseError`.

See the KIDL documentation here: https://kbase.us/services/ws/docs/Workspace.html

```py
objects = workspace_client.req('get_objects2', {
    'objects': [{'ref': '1/2/3'}, {'ref': '99/98/97'}],
    'no_data': 1
})
```

### ws_client.admin_req(method, params)

Run an administration method using its separate interface.

See the workspace docs here: https://kbase.us/services/ws/docs/administrationinterface.html

If the request is unsuccessful, then this raises a `WorkspaceResponseError`.

```py
objects = workspace_client.admin_req('getObjects', {
    'objects': [{'ref': '1/2/3'}, {'ref': '99/98/97'}],
    'no_data': 1
})
```

### ws_client.generate_all_ids_for_workspace(workspace_id, admin=False, latest=True)

Generator that yields pairs of `(object_id, object_version)` for a workspace.

This will yield IDs/versions for *every* object in the workspace.

Options:
* `admin` - whether to do a "list_objects" method call using regular or admin credentials
* `latest` - whether to fetch only the latest object versions, or all object versions

```py
for (object_id, object_version) in workspace_client.generate_all_ids_for_workspace(123):
    print(f"Found object with ID {object_id} and version {object_version}")
```

### Streaming responses to files

You can stream the workspace response to a file by using:

* `ws_client.req_download(method, params, file_path)`
* `ws_client.admin_req_download(method, params, file_path)`

The `file_path` must be a non-existent file in a writable directory.

## Misc. utilities

### ws_client.download_shock_file(shock_id, dest_path)

Download a file given a shock ID and a destination path:

```py
ws_client.download_shock_file('unique_shock_id', dest_path)
```

`dest_path` must point to a non-existent file in a writable directory.

This download will be streaming and low-memory.

### ws_client.handle_to_shock(handle_id)

Get the shock ID from a handle ID in order to download the file:

```py
shock_id = ws_client.handle_to_shock(handle_id)
ws_client.download_shock_file(shock_id, dest_path)
```

### ws_client.download_assembly_fasta(ref, save_dir, admin=False)

Download the FASTA for an Assembly (or legacy ContigSet) datatype to a directory.

Options:
* `admin` - whether or not to download as an admin or as a normal user

```py
ws_client.download_assembly_fasta("1/2/3", "/tmp/xyz")
```

### ws_client.download_reads_fastq(ref, save_dir, admin=False)

Download the fastq for a PairedEndLibrary or SingleEndLibrary datatype to a directory.

Options:
* `admin` - whether or not to download as an admin or as a normal user

```py
ws_client.download_reads_fastq("1/2/3", "/tmp/xyz")
```

## Exceptions

### WorkspaceResponseError

Raised on any invalid response from the workspace. Properties on the error object are:

* `status_code` - http response status code
* `resp_data` - parsed python dictionary of response body data (if parse-able)
* `resp_text` - raw http response body text

```py
from kbase_workspace_client import WorkspaceClient, WorkspaceResponseError

workspace_client = WorkspaceClient(
  url="https://appdev.kbase.us/services/ws",
  token="abcxyz"
)

try:
    workspace_client.req('get_objects2', {
        'objects': [{'ref': '1/2/3'}, {'ref': '99/98/97'}],
        'no_data': 1
    })
except WorkspaceResponseError as err:
    print(err)
```

`WorkspaceResponseError` is a child of `RuntimeError`.

## Development

### Publishing

Build the package

```
python setup.py sdist
```

Publish the package

```
anaconda upload -i -u kbase dist/kbase_module-{version}.tar.gz
```
