# KBase Workspace Client

Generic workspace client for KBase's workspace service.

## Installation

Install with pip:

```py
pip install --extra-index-url https://pypi.anaconda.org/kbase/simple \
    kbase-workspace-client==0.0.1
```

## Usage

Import and initialize the `WorkspaceClient` class:

```py
from kbase_workspace_client import WorkspaceClient

ws_client = WorkspaceClient(
  url="https://appdev.kbase.us/services",
  token="my_authentication_token"
)
```

`url` should be the url of KBase services, which will be one of:
* `https://ci.kbase.us/services`
* `https://appdev.kbase.us/services`
* `https://kbase.us/services`

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

### Streaming responses to files

You can stream the workspace response to a file by using:

* `ws_client.req_download(method, params, file_path)`
* `ws_client.admin_req_download(method, params, file_path)`

The `file_path` must be a non-existent file in a writable directory.

### Exceptions

#### WorkspaceResponseError

Raised on any invalid response from the workspace. Properties on the error object are:

* `status_code` - http response status code
* `resp_data` - parsed python dictionary of response body data (if parse-able)
* `resp_text` - raw http response body text

```py
from kbase_workspace_client import WorkspaceClient, WorkspaceResponseError

workspace_client = WorkspaceClient(
  url="https://appdev.kbase.us/services",
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

## Downloading attached files

### ws_client.download_from_shock(shock_id, dest_path)

Download a file given a shock ID and a destination path:

```py
ws_client.download_from_shock('unique_shock_id', dest_path)
```

`dest_path` must point to a non-existent file in a writable directory.

This download will be streaming and low-memory.

### ws_client.handle_to_shock(handle_id)

Get the shock ID from a handle ID in order to download the file:

```py
shock_id = ws_client.handle_to_shock(handle_id)
ws_client.download_from_shock(shock_id, dest_path)
```
