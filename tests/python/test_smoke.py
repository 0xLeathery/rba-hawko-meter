"""
Infrastructure smoke tests for RBA Hawk-O-Meter Python test suite.

These 5 tests prove the three core guarantees provided by conftest.py:
  1. DATA_DIR isolation — tests cannot read/write the live data/ folder
  2. Network blocking — socket.socket raises RuntimeError for non-live tests
  3. Tier separation — @pytest.mark.live escapes the network blocker

If any of these tests fail, the test infrastructure itself is broken and
no other test results can be trusted.
"""

import socket
from pathlib import Path

import pytest

import pipeline.config


def test_pytest_discovers_and_exits_zero():
    """Baseline: pytest discovered this file and ran this test. Infrastructure is alive."""
    assert True


def test_data_dir_isolated_from_production():
    """
    Verify that DATA_DIR is NOT the live data/ folder.

    The isolate_data_dir autouse fixture in conftest.py patches
    pipeline.config.DATA_DIR to a tmp_path for every test. This confirms
    the patch is active and the test cannot accidentally write to data/.
    """
    live_data_dir = str(Path("data").resolve())
    test_data_dir = str(pipeline.config.DATA_DIR)

    # Must not point to the production data/ directory
    assert test_data_dir != str(Path("data")), (
        "DATA_DIR is still the relative Path('data') — isolate_data_dir fixture is not working"
    )
    assert test_data_dir != live_data_dir, (
        "DATA_DIR resolves to the live data/ folder — isolate_data_dir fixture is not working"
    )

    # Must look like a temp path (starts with / and contains 'tmp' or is an absolute path
    # not under the project root)
    assert str(pipeline.config.DATA_DIR).startswith("/"), (
        "DATA_DIR is not an absolute path — expected a tmp_path from pytest"
    )


def test_network_blocker_raises_runtime_error():
    """
    Verify that socket.socket() raises RuntimeError for non-live tests.

    The block_network autouse fixture in conftest.py replaces socket.socket
    with a function that raises RuntimeError. This confirms any network
    call from a non-live test will fail loudly rather than silently succeed.
    """
    with pytest.raises(RuntimeError, match="Network access blocked"):
        socket.socket()


@pytest.mark.live
def test_live_marker_exempts_network_block():
    """
    Verify that @pytest.mark.live tests can create real sockets.

    The block_network fixture detects the 'live' marker via
    request.node.get_closest_marker("live") and steps aside. This test
    MUST NOT raise — if it does, the live marker escape hatch is broken.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.close()


def test_fixture_csvs_loadable(fixture_cpi_df):
    """
    Verify the fixture CSV loader fixtures return valid DataFrames.

    Requests the fixture_cpi_df fixture (defined in conftest.py), which reads
    tests/python/fixtures/abs_cpi.csv. Confirms the CSV loads successfully
    with >0 rows and has the expected column headers.
    """
    assert fixture_cpi_df is not None, "fixture_cpi_df returned None"
    assert len(fixture_cpi_df) > 0, "fixture_cpi_df is empty — check abs_cpi.csv"
    assert "date" in fixture_cpi_df.columns, "Missing 'date' column in fixture CPI data"
    assert "value" in fixture_cpi_df.columns, "Missing 'value' column in fixture CPI data"
