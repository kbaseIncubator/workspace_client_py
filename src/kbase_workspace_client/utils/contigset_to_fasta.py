"""
A ContigSet is a legacy KBase datatype that stores all the contigs in a workspace object.

This module provides a utility for converting that data into a fasta file.
"""
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord
from Bio.Seq import Seq
from Bio.Alphabet import SingleLetterAlphabet


def contigset_generate_contigs(ws_obj):
    """
    A generator that produces Bio.SeqRecord objects for every contig in a ContigSet.
    Args:
      ws_obj is a workspace data object -- must have a path for data/contigs
    yields SeqRecords
    """
    contigs = ws_obj['data']['contigs']
    for contig in contigs:
        rec = SeqRecord(
            Seq(contig['sequence'], SingleLetterAlphabet),
            id=contig['id'],
            description=contig.get('description', '')
        )
        yield rec


def contigset_to_fasta(ws_obj, output_path):
    """Write out every contig to a fasta file."""
    SeqIO.write(contigset_generate_contigs(ws_obj), output_path, "fasta")
