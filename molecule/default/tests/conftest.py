"""pytest-testinfra fixtures for the ansible-role-corosync_qnetd Molecule suite."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ._data import DEBIAN_ENV_FILE, REDHAT_DISTROS, REDHAT_ENV_FILE

if TYPE_CHECKING:
    from testinfra.host import Host


@pytest.fixture(scope="module")
def corosync_qnetd_env_file(host: Host) -> str:
    """Return the COROSYNC_QNETD_OPTIONS env file path for the current host.

    Maps ansible_os_family to the value of __corosync_qnetd_env_file in
    vars/*.yml:
    - Debian family  → /etc/default/corosync-qnetd   (vars/Debian.yml)
    - RedHat family  → /etc/sysconfig/corosync-qnetd  (vars/RedHat.yml)
    """
    dist: str = host.system_info.distribution.lower()
    if dist in REDHAT_DISTROS:
        return REDHAT_ENV_FILE
    return DEBIAN_ENV_FILE
