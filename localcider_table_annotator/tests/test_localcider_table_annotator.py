"""
Unit and regression test for the localcider_table_annotator package.
"""

# Import package, test suite, and other packages as needed
import sys

import pytest

import localcider_table_annotator


def test_localcider_table_annotator_imported():
    """Sample test, will always pass so long as import statement worked."""
    assert "localcider_table_annotator" in sys.modules
