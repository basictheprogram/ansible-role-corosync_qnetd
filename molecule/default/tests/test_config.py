"""Tests for the COROSYNC_QNETD_OPTIONS env file templated by the role.

converge.yml exercises the role's unmodified corosync_qnetd_* defaults, so
the expected content here is DEFAULT_OPTIONS_LINE from _data.py — keep both
in sync if either the defaults or the template change.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._data import DEFAULT_OPTIONS_LINE

if TYPE_CHECKING:
    from testinfra.host import Host


def test_env_file_exists(host: Host, corosync_qnetd_env_file: str) -> None:
    """The COROSYNC_QNETD_OPTIONS env file exists as a regular file."""
    f = host.file(corosync_qnetd_env_file)
    assert f.exists
    assert f.is_file


def test_env_file_owner(host: Host, corosync_qnetd_env_file: str) -> None:
    """The env file is owned by root:root."""
    f = host.file(corosync_qnetd_env_file)
    assert f.user == "root"
    assert f.group == "root"


def test_env_file_mode(host: Host, corosync_qnetd_env_file: str) -> None:
    """The env file has mode 0644."""
    f = host.file(corosync_qnetd_env_file)
    assert f.mode == 0o644


def test_env_file_default_options(host: Host, corosync_qnetd_env_file: str) -> None:
    """The default corosync_qnetd_* variables render the expected flags."""
    content: str = host.file(corosync_qnetd_env_file).content_string
    assert DEFAULT_OPTIONS_LINE in content
