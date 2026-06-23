"""Tests that the correct corosync-qnetd packages are installed for each OS family."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ._data import DEBIAN_PKGS, REDHAT_DISTROS, REDHAT_PKGS

if TYPE_CHECKING:
    from testinfra.host import Host


@pytest.mark.parametrize("pkg", DEBIAN_PKGS)
def test_debian_packages_installed(host: Host, pkg: str) -> None:
    """Debian-family corosync-qnetd packages are installed."""
    dist: str = host.system_info.distribution.lower()
    if dist in REDHAT_DISTROS:
        pytest.skip("Debian packages not applicable on RedHat family")
    assert host.package(pkg).is_installed


@pytest.mark.parametrize("pkg", REDHAT_PKGS)
def test_redhat_packages_installed(host: Host, pkg: str) -> None:
    """RedHat-family corosync-qnetd packages are installed."""
    dist: str = host.system_info.distribution.lower()
    if dist not in REDHAT_DISTROS:
        pytest.skip("RedHat packages not applicable on Debian family")
    assert host.package(pkg).is_installed
