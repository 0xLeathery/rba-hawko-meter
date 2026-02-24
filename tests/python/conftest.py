"""
Shared test infrastructure for RBA Hawk-O-Meter Python test suite.

Provides:
  - isolate_data_dir: autouse fixture that patches pipeline.config.DATA_DIR to
    a tmp_path so tests never read/write the live data/ folder.
  - block_network: autouse fixture that patches socket.socket so any network
    access raises RuntimeError. Tests decorated with @pytest.mark.live are
    exempted.
  - Named CSV loader fixtures that return pandas DataFrames from the fixture
    CSVs in tests/python/fixtures/.
"""

import socket
from pathlib import Path

import pandas as pd
import pytest

import pipeline.config

# Use Path(__file__).parent to locate fixtures relative to this file,
# not relative to the CWD from which pytest is invoked (avoids pitfall #4).
FIXTURES_DIR = Path(__file__).parent / "fixtures"


# =============================================================================
# Autouse fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def isolate_data_dir(monkeypatch, tmp_path):
    """
    Patch pipeline.config.DATA_DIR to a temporary directory for every test.

    This prevents tests from reading or writing the live data/ folder.
    Import pipeline.config as a module (not `from pipeline.config import DATA_DIR`)
    so the monkeypatch targets the module attribute and is visible to all code
    that reads pipeline.config.DATA_DIR at call time.

    NOTE: SOURCE_METADATA paths are computed at import time from the original
    DATA_DIR value and are NOT retroactively updated by this patch. Phase 12
    tests that use SOURCE_METADATA will need additional patching of those
    individual paths.
    """
    monkeypatch.setattr(pipeline.config, "DATA_DIR", tmp_path)
    yield


@pytest.fixture(autouse=True)
def block_network(monkeypatch, request):
    """
    Block all network access for every test by replacing socket.socket.

    Any call to socket.socket() raises RuntimeError with the message
    "Network access blocked in tests. Use @pytest.mark.live for tests
    requiring network."

    Tests decorated with @pytest.mark.live are exempted — the fixture
    detects the marker and steps aside, allowing real socket connections.

    Blocks everything including localhost — there are no exceptions for
    non-live tests.
    """
    if request.node.get_closest_marker("live"):
        yield
        return

    def blocked_socket(*args, **kwargs):
        raise RuntimeError(
            "Network access blocked in tests. Use @pytest.mark.live for tests requiring network."
        )

    monkeypatch.setattr(socket, "socket", blocked_socket)
    yield


# =============================================================================
# Named CSV loader fixtures (not autouse — tests request them explicitly)
# =============================================================================


@pytest.fixture
def fixture_cpi_df():
    """Return ABS CPI fixture data as a DataFrame (abs_cpi.csv)."""
    return pd.read_csv(FIXTURES_DIR / "abs_cpi.csv")


@pytest.fixture
def fixture_employment_df():
    """Return ABS employment fixture data as a DataFrame (abs_employment.csv)."""
    return pd.read_csv(FIXTURES_DIR / "abs_employment.csv")


@pytest.fixture
def fixture_wages_df():
    """Return ABS Wage Price Index fixture data as a DataFrame (abs_wage_price_index.csv)."""
    return pd.read_csv(FIXTURES_DIR / "abs_wage_price_index.csv")


@pytest.fixture
def fixture_spending_df():
    """Return ABS Household Spending fixture data as a DataFrame (abs_household_spending.csv)."""
    return pd.read_csv(FIXTURES_DIR / "abs_household_spending.csv")


@pytest.fixture
def fixture_building_approvals_df():
    """Return ABS Building Approvals fixture data as a DataFrame (abs_building_approvals.csv)."""
    return pd.read_csv(FIXTURES_DIR / "abs_building_approvals.csv")


@pytest.fixture
def fixture_housing_df():
    """Return CoreLogic housing fixture data as a DataFrame (corelogic_housing.csv)."""
    return pd.read_csv(FIXTURES_DIR / "corelogic_housing.csv")


@pytest.fixture
def fixture_nab_capacity_df():
    """Return NAB capacity utilisation fixture data as a DataFrame (nab_capacity.csv)."""
    return pd.read_csv(FIXTURES_DIR / "nab_capacity.csv")
