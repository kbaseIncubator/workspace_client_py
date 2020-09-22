# KBase Workspace - Python Client and Utilities

Generic, pip-installable workspace client for [KBase's workspace service](https://kbase.us/services/ws/docs).

This package covers many common tasks when working with the KBase Workspace.

Note that you cannot write any data to the workspace using this module. You'll have to use the KBase SDK for that.

## Installation

Install with pip:

```sh
pip install kbase-workspace-client==0.0.1
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

### ws_client.generate_obj_infos(workspace_id, admin=False, latest=True)

Generator that yields all object info tuples for a workspace.

[See the object info type here](https://kbase.us/services/ws/docs/Workspace.html#typedefWorkspace.object_info)

Options:
* `admin` - default `False` - whether to do a Workspace "list_objects" method call using regular or admin credentials
* `latest` - default `True` - whether to fetch only the latest object versions, or all object versions

```py
for objinfo in workspace_client.generate_obj_infos(123):
    print(f"Found object with info tuple {objinfo}")
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

### ws_client.get_assembly_from_genome(ref, admin=False)

Given a Genome object, fetch the reference to its Assembly object in the workspace.

Options:
* `admin` - whether or not to download as an admin or as a normal user

```py
assembly_ref = ws_client.get_assembly_from_genome('1/2/3')
```

### The ObjInfo Named Tuple

For convenience, a [namedtuple](https://docs.python.org/3.7/library/collections.html#collections.namedtuple) called `ObjInfo` is provided to give key names to the `object_info` tuple, found in various results from the workspace: https://kbase.us/services/ws/docs/Workspace.html#typedefWorkspace.object_info

Example usage:

```py
> from kbase_workspace_client import ObjInfo
> obj_info_list
[1, "xyz", "Module.Type-12.3", 2, 3, "xyz", 0, "ws_name", 10, 10, {"xyz": 123}]
> obj_info = ObjInfo(*obj_info_list)
ObjInfo(objid=1, name='xyz', type='Module.Type-12.3', save_date=2, version=3, saved_by='xyz', wsid=0, workspace='ws_name', chsum=10, size=10, meta={'xyz': 123})
> obj_info.meta
{'xyz': 123}
```

### The WSInfo Named Tuple

For convenience, a [namedtuple](https://docs.python.org/3.7/library/collections.html#collections.namedtuple) called `WSInfo` is provided to give key names to the `workspace_info` tuple, found in various results from the workspace: https://kbase.us/services/ws/docs/Workspace.html#typedefWorkspace.workspace_info

Example usage:

```py
> from kbase_workspace_client import WSInfo
> ws_info_list
[123, "x", "username", 123, 123, "n", "n", "unlocked", {"x": 1}]
> ws_info = WSInfo(*ws_info_list)
WSInfo(id=123, workspace='x', owner='username', moddate=123, max_objid=123, user_permission='n', globalread='n', lockstat='unlocked', metadata={'x': 1})
> ws_info.metadata
{'x': 1}
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

Install the dependencies using python 3:

```
pip install poetry
poetry install
poetry check
```

### Tests

Run tests with: `TEST_TOKEN=xyz make test`

The `TEST_TOKEN` env var should be set to a KBase workspace token.

### Publishing

Build the package

```
poetry build
poetry publish
```
