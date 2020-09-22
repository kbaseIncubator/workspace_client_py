"""
Get a sample of refdata
"""
import os

from kbase_workspace_client import WorkspaceClient

assert 'TOKEN' in os.environ, 'env var for a KBase auth token is required (TOKEN)'
assert 'KBASE_ENDPOINT' in os.environ, 'env var for KBase endpoint is required (KBASE_ENDPOINT)'

ws_client = WorkspaceClient(
  url=os.environ['KBASE_ENDPOINT'],
  token=os.environ["TOKEN"],
)

narr_ids = []
for wsid in range(1, 60000):
    try:
        for objinfo in ws_client.generate_obj_infos(wsid, admin=True):
            if objinfo[2] == 'KBaseGenomes.Genome-11.0':
                print(f"{objinfo[6]}/{objinfo[0]}/{objinfo[4]}")
    except Exception:
        continue

