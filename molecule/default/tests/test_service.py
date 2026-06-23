"""Tests for the corosync-qnetd service managed by the role.

corosync-qnetd has no hardware dependency — unlike NUT, it is a plain TCP
listener (port 5403) with its own NSS certificate database, which distro
packaging initializes during package installation. This means, unlike
ansible-role-nut, the service is expected to actually start under Docker
and is asserted as running here, not just enabled.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._data import SERVICE_NAME

if TYPE_CHECKING:
    from testinfra.host import Host


def test_service_is_enabled(host: Host) -> None:
    """corosync-qnetd.service is enabled at boot."""
    assert host.service(SERVICE_NAME).is_enabled


def test_service_is_running(host: Host) -> None:
    """corosync-qnetd.service is active."""
    assert host.service(SERVICE_NAME).is_running
