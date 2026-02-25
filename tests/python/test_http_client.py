"""
Unit tests for pipeline.utils.http_client — session creation and configuration.

Tests verify the session object returned by create_session() is correctly
configured with retry strategy, adapter mounting, and User-Agent headers.
No mocking needed — http_client.py performs pure configuration, no I/O.
"""

import requests
from requests.adapters import HTTPAdapter

from pipeline.config import USER_AGENT
from pipeline.utils.http_client import create_session


class TestCreateSession:
    """Tests for create_session()."""

    def test_returns_session_type(self):
        session = create_session()
        assert isinstance(session, requests.Session)

    def test_default_user_agent(self):
        session = create_session()
        assert session.headers['User-Agent'] == USER_AGENT

    def test_custom_user_agent(self):
        session = create_session(user_agent="Custom/1.0")
        assert session.headers['User-Agent'] == "Custom/1.0"

    def test_mounts_http_adapter(self):
        session = create_session()
        adapter = session.get_adapter("http://example.com")
        assert isinstance(adapter, HTTPAdapter)

    def test_mounts_https_adapter(self):
        session = create_session()
        adapter = session.get_adapter("https://example.com")
        assert isinstance(adapter, HTTPAdapter)

    def test_retry_strategy_total(self):
        session = create_session(retries=5)
        adapter = session.get_adapter("https://example.com")
        assert adapter.max_retries.total == 5

    def test_retry_strategy_default_total(self):
        session = create_session()
        adapter = session.get_adapter("https://example.com")
        assert adapter.max_retries.total == 3

    def test_retry_strategy_backoff_factor(self):
        session = create_session(backoff_factor=1.0)
        adapter = session.get_adapter("https://example.com")
        assert adapter.max_retries.backoff_factor == 1.0

    def test_retry_strategy_default_backoff(self):
        session = create_session()
        adapter = session.get_adapter("https://example.com")
        assert adapter.max_retries.backoff_factor == 0.5

    def test_retry_status_forcelist(self):
        session = create_session()
        adapter = session.get_adapter("https://example.com")
        assert adapter.max_retries.status_forcelist == [500, 502, 503, 504]

    def test_retry_allowed_methods(self):
        session = create_session()
        adapter = session.get_adapter("https://example.com")
        assert set(adapter.max_retries.allowed_methods) == {"GET", "POST"}
