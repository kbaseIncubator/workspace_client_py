import os
import unittest
import tempfile
import shutil
from kbase_workspace_client import WorkspaceClient, WorkspaceResponseError
from kbase_workspace_client.exceptions import InvalidWSType, InvalidGenome

if not os.environ.get('TEST_TOKEN'):
    raise RuntimeError("TEST_TOKEN environment variable is required.")

_URL = "https://ci.kbase.us/services/"
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
