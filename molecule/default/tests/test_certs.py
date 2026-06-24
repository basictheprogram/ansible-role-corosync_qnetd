"""Tests for the daemon's own NSS certificate database.

converge.yml exercises the role's unmodified defaults, and
corosync_qnetd_manage_nss_db defaults to true (with corosync_qnetd_tls
defaulting to "on") — so the corosync-qnetd-certutil -i task runs and
the CA certificate should exist. The skip path
(corosync_qnetd_manage_nss_db: false, or corosync_qnetd_tls: off) is
not exercised here; see TODO.md.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._data import QNETD_CACERT_PATH

if TYPE_CHECKING:
    from testinfra.host import Host


def test_nss_db_created_by_default(host: Host) -> None:
    """corosync_qnetd_manage_nss_db defaults to true: the CA cert exists."""
    assert host.file(QNETD_CACERT_PATH).exists
