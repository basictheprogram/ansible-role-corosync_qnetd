"""Shared constants for the ansible-role-corosync_qnetd Molecule test suite.

All values here must stay in sync with molecule/default/converge.yml and
the role's vars/ files. Do not import from conftest.py in test files —
conftest is a pytest plugin, not a regular module, and the import breaks
when __init__.py is present.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# OS-family detection
# ---------------------------------------------------------------------------

#: Distribution names that map to the RedHat OS family.
REDHAT_DISTROS: frozenset[str] = frozenset(
    {
        "rocky",
        "almalinux",
        "rhel",
        "centos",
        "ol",
        "fedora",
    }
)

# ---------------------------------------------------------------------------
# Package expectations (must match vars/Debian.yml and vars/RedHat.yml)
# ---------------------------------------------------------------------------

#: corosync-qnetd packages installed on Debian-family systems.
DEBIAN_PKGS: tuple[str, ...] = ("corosync-qnetd",)

#: corosync-qnetd packages installed on RedHat-family systems.
REDHAT_PKGS: tuple[str, ...] = ("corosync-qnetd",)

# ---------------------------------------------------------------------------
# Service (must match the systemd unit name in tasks/main.yml)
# ---------------------------------------------------------------------------

#: systemd unit installed and managed by the role.
SERVICE_NAME: str = "corosync-qnetd.service"

# ---------------------------------------------------------------------------
# Env file (must match __corosync_qnetd_env_file in vars/*.yml)
# ---------------------------------------------------------------------------

#: COROSYNC_QNETD_OPTIONS env file path on Debian-family systems.
DEBIAN_ENV_FILE: str = "/etc/default/corosync-qnetd"

#: COROSYNC_QNETD_OPTIONS env file path on RedHat-family systems.
REDHAT_ENV_FILE: str = "/etc/sysconfig/corosync-qnetd"

#: Expected COROSYNC_QNETD_OPTIONS value rendered from converge.yml's
#: unmodified corosync_qnetd_* defaults (port 5403, TLS on with client
#: cert required, no limit on max clients — see defaults/main.yml).
DEFAULT_OPTIONS_LINE: str = 'COROSYNC_QNETD_OPTIONS="-p 5403 -s on -c on -m 0"'

# ---------------------------------------------------------------------------
# NSS certificate database (must match the creates: path in tasks/main.yml)
# ---------------------------------------------------------------------------

#: CA certificate exported by `corosync-qnetd-certutil -i`. Used as the
#: idempotency marker for the NSS-db-init task and as proof, in tests,
#: that the (default-on) task ran.
QNETD_CACERT_PATH: str = "/etc/corosync/qnetd/nssdb/qnetd-cacert.crt"
