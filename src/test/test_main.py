import os
import unittest
import tempfile
import shutil
from kbase_workspace_client import WorkspaceClient, WorkspaceResponseError, WSInfo, ObjInfo
from kbase_workspace_client.exceptions import InvalidWSType, InvalidGenome

if not os.environ.get('TEST_TOKEN'):
    raise RuntimeError("TEST_TOKEN environment variable is required.")

_URL = "https://ci.kbase.us/services/"
_ws_client = WorkspaceClient(url=_URL, token=os.environ['TEST_TOKEN'])


class TestMain(unittest.TestCase):

    maxDiff = None

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

    def test_generate_obj_infos(self):
        infos = []
        for info in _ws_client.generate_obj_infos(33192):
            infos.append(info)
        self.assertTrue(len(infos) > 0)
        for info in infos:
            self.assertTrue(len(info) == 11)

    def test_err(self):
        _id = '0/0/0'
        with self.assertRaises(WorkspaceResponseError):
            _ws_client.req('get_objects2', {
                'objects': [{'ref': _id}],
                'no_data': 1
            })

    def test_assembly_download_valid(self):
        try:
            tmp_dir = tempfile.mkdtemp()
            valid_ws_id = '34819/10/1'
            pathname = _ws_client.download_assembly_fasta(valid_ws_id, tmp_dir)
            self.assertEqual(os.path.getsize(pathname), 3849120)
            filename = os.path.basename(pathname)
            self.assertEqual(filename, "MEGAHIT.contigs.fasta")
        finally:
            shutil.rmtree(tmp_dir)

    # Error cases for invalid users and invalid ws references are covered in test_download_obj

    def test_assembly_download_wrong_type(self):
        try:
            reads_id = '15/45/1'
            tmp_dir = tempfile.mkdtemp()
            with self.assertRaises(InvalidWSType) as err:
                _ws_client.download_assembly_fasta(ref=reads_id, save_dir=tmp_dir)
            self.assertTrue('Invalid workspace type' in str(err.exception))
        finally:
            shutil.rmtree(tmp_dir)

    def test_reads_download_valid(self):
        """
        Test valid downloads for both paired and single-end reads. Paired-end has examples for both
        interleaved and not.
        """
        try:
            tmp_dir = tempfile.mkdtemp()
            # Paired reads, non-interleaved
            ref = '15/45/1'
            paths = _ws_client.download_reads_fastq(ref=ref, save_dir=tmp_dir)
            self.assertEqual(len(paths), 2)
            self.assertTrue('rhodobacter.art.q10.PE.reads.paired.fwd.fastq' in paths[0])
            self.assertTrue('rhodobacter.art.q10.PE.reads.paired.rev.fastq' in paths[1])
            self.assertEqual(os.path.getsize(paths[0]), 36056522)
            self.assertEqual(os.path.getsize(paths[1]), 37522557)
            # Paired reads, interleaved
            ref = '15/44/1'
            paths = _ws_client.download_reads_fastq(ref=ref, save_dir=tmp_dir)
            self.assertTrue('rhodobacter.art.q20.int.PE.reads.paired.interleaved.fastq' in paths[0])
            self.assertEqual(len(paths), 1)
            self.assertEqual(os.path.getsize(paths[0]), 36510129)
            # Single-end reads
            ref = '15/43/1'
            paths = _ws_client.download_reads_fastq(ref=ref, save_dir=tmp_dir)
            self.assertTrue('rhodobacter.art.q50.SE.reads.single.fastq' in paths[0])
            self.assertEqual(len(paths), 1)
            self.assertEqual(os.path.getsize(paths[0]), 53949468)
        finally:
            shutil.rmtree(tmp_dir)

    # Error cases for invalid users and invalid ws references are covered in test_download_obj

    def test_reads_download_wrong_type(self):
        try:
            assembly_id = '34819/10/1'
            tmp_dir = tempfile.mkdtemp()
            with self.assertRaises(InvalidWSType) as err:
                _ws_client.download_reads_fastq(ref=assembly_id, save_dir=tmp_dir)
            self.assertTrue('Invalid workspace type' in str(err.exception))
        finally:
            shutil.rmtree(tmp_dir)

    def test_get_assembly_from_genome(self):
        """Test the valid/successful case."""
        ref = '34819/14/1'
        assembly_ref = _ws_client.get_assembly_from_genome(ref)
        self.assertEqual(assembly_ref, '34819/14/1;16/7/1')

    def test_get_assembly_from_genome_missing_assembly(self):
        """
        Test the case where a Genome object does not have an assembly_ref
        """
        ref = '34819/5/9'
        with self.assertRaises(InvalidGenome) as err:
            _ws_client.get_assembly_from_genome(ref)
        self.assertTrue('no assembly or contigset references' in str(err.exception))

    def test_ws_info_tuple(self):
        """
        Test that the WSInfo is importable and works. Mostly a sanity check and some redundancy.
        """
        ws_info = [1, "x", "username", 2, 3, "n", "a", "unlocked", {"x": 1}]
        named = WSInfo(*ws_info)
        self.assertEqual(named.id, ws_info[0])
        self.assertEqual(named.workspace, ws_info[1])
        self.assertEqual(named.owner, ws_info[2])
        self.assertEqual(named.moddate, ws_info[3])
        self.assertEqual(named.max_objid, ws_info[4])
        self.assertEqual(named.user_permission, ws_info[5])
        self.assertEqual(named.globalread, ws_info[6])
        self.assertEqual(named.lockstat, ws_info[7])
        self.assertEqual(named.metadata, ws_info[8])

    def test_obj_info_tuple(self):
        """
        Test that the ObjInfo is importable and works. Mostly a sanity check and some redundancy.
        """
        obj_info = [1, "xyz", "Module.Type-12.3", 2, 3, "xyz", 4, "ws_name", 5, 6, {"xyz": 123}]
        named = ObjInfo(*obj_info)
        self.assertEqual(named.objid, obj_info[0])
        self.assertEqual(named.name, obj_info[1])
        self.assertEqual(named.type, obj_info[2])
        self.assertEqual(named.save_date, obj_info[3])
        self.assertEqual(named.version, obj_info[4])
        self.assertEqual(named.saved_by, obj_info[5])
        self.assertEqual(named.wsid, obj_info[6])
        self.assertEqual(named.workspace, obj_info[7])
        self.assertEqual(named.chsum, obj_info[8])
        self.assertEqual(named.size, obj_info[9])
        self.assertEqual(named.meta, obj_info[10])

    def test_find_narrative_ok(self):
        narr_info = _ws_client.find_narrative(34819, admin=True)
        self.assertEqual(narr_info.type, "KBaseNarrative.Narrative-4.0")
        self.assertEqual(narr_info.wsid, 34819)

    def test_find_narrative_nonexistent(self):
        with self.assertRaises(WorkspaceResponseError) as ctx:
            _ws_client.find_narrative(99999999, admin=True)
        self.assertEqual(ctx.exception.resp_data['error']['code'], -32500)

    def test_find_narrative_no_access(self):
        with self.assertRaises(WorkspaceResponseError) as ctx:
            _ws_client.find_narrative(54116)
        # Permissions error
        self.assertEqual(ctx.exception.resp_data['error']['code'], -32500)

    def test_find_narrative_admin_access(self):
        narr_info = _ws_client.find_narrative(54116, admin=True)
        self.assertEqual(narr_info.type, "KBaseNarrative.Narrative-4.0")
        self.assertEqual(narr_info.wsid, 54116)
