realtime.corosync_qnetd
========================

[![Ansible Galaxy](https://img.shields.io/badge/galaxy-realtime.corosync__qnetd-blue?logo=ansible)](https://galaxy.ansible.com/ui/standalone/roles/realtime/corosync_qnetd/)
[![Ansible Galaxy Downloads](https://img.shields.io/ansible/role/d/realtime/corosync_qnetd)](https://galaxy.ansible.com/ui/standalone/roles/realtime/corosync_qnetd/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platforms](https://img.shields.io/badge/platforms-Ubuntu%20%7C%20Debian%20%7C%20EL-informational)](https://galaxy.ansible.com/ui/standalone/roles/realtime/corosync_qnetd/)

Installs and configures `corosync-qnetd`, the standalone Qdevice Network
Quorum Daemon that acts as an external quorum arbitrator for corosync
clusters — for example, two-node Proxmox VE clusters that need a
tie-breaker vote without a third full cluster member.

The role:

- Installs the `corosync-qnetd` package (enabling the `HighAvailability`
  repo on EL hosts for that single transaction)
- Initializes the daemon's own NSS certificate database
  (`corosync-qnetd-certutil -i`) so it can speak TLS, by default
- Templates the daemon's command-line options (listen address/port,
  address family, TLS mode, client certificate required, max clients,
  debug logging) into the env file `corosync-qnetd.service` reads at
  startup
- Enables and starts the `corosync-qnetd` service

Per-cluster TLS certificate trust setup is **out of scope** and remains a
manual step — see [Manual step: certificate trust](#manual-step-certificate-trust)
below.

**Security note:** `corosync_qnetd_tls` defaults to `on`, matching
upstream's own default and Proxmox VE's own requirement that
QDevice-to-cluster traffic be encrypted — see
[Proxmox VE Cluster Manager — Corosync External Vote Support](https://pve.proxmox.com/pve-docs/chapter-pvecm.html#_corosync_external_vote_support).
`corosync_qnetd_manage_nss_db` also defaults to `true`, so the daemon's
own NSS certificate database is created automatically and the service
starts cleanly with TLS on, out of the box, on every supported
platform.

> **WARNING — do not set `corosync_qnetd_tls: off` unless you fully
> understand the tradeoff.** With TLS off, connections to this daemon
> are unauthenticated and unencrypted: anything that can reach
> TCP/5403 can claim membership in any cluster, and vote/quorum
> traffic can be read or tampered with in transit. Proxmox's own
> documentation states this traffic **must be encrypted**
> ([source](https://pve.proxmox.com/pve-docs/chapter-pvecm.html#_corosync_external_vote_support));
> setting `off` deviates from that requirement and is only appropriate
> if you separately restrict network access to known cluster nodes
> (e.g. a firewall or private network) and accept the loss of
> authentication and confidentiality.

Requirements
------------

- Ansible core >= 2.20
- On EL hosts, the `HighAvailability` repo must be available to the
  package manager (it ships disabled by default on Rocky/Alma/RHEL; the
  role enables it per-transaction via `enablerepo`, no persistent
  repo-file changes)

Supported Platforms
-------------------

| OS     | Versions                                       |
|--------|-------------------------------------------------|
| Ubuntu | jammy (22.04), noble (24.04), resolute (26.04) |
| Debian | bookworm (12), trixie (13)                     |
| EL     | 9, 10                                          |

Role Variables
--------------

### `defaults/main.yml` — user-overridable

| Variable | Default | Description |
|----------|---------|-------------|
| `corosync_qnetd_enable_service` | `true` | Whether to enable and start `corosync-qnetd` after installation. Set to `false` to manage service state externally — e.g. if certificate trust setup must happen before the daemon first starts. |
| `corosync_qnetd_extra_packages` | `[]` | Additional OS packages to install alongside `corosync-qnetd`. |
| `corosync_qnetd_listen_address` | `""` | IP address to listen on. Empty means the wildcard address. Site-specific binding addresses belong in `group_vars`/`host_vars`, not here. |
| `corosync_qnetd_listen_port` | `5403` | TCP port to listen on. |
| `corosync_qnetd_address_family` | `"any"` | `any`, `ipv4`, or `ipv6`. |
| `corosync_qnetd_tls` | `"on"` | `on`, `off`, or `required`. Defaults to `on` — Proxmox VE requires encrypted QDevice traffic, matching upstream's own default (see the warning above). `on`/`required` need the daemon's own NSS certificate database (`corosync-qnetd-certutil -i`) to exist; `corosync_qnetd_manage_nss_db` defaults to `true` so the role creates it automatically. Only set this to `off` if you understand the tradeoff. |
| `corosync_qnetd_manage_nss_db` | `true` | Whether to run `corosync-qnetd-certutil -i` to initialize the daemon's own NSS certificate database when `corosync_qnetd_tls` is not `off`. Defaults to `true` so `corosync_qnetd_tls`'s `on` default works out of the box. Idempotent — skipped once the database exists. Does not perform per-cluster trust (`corosync-qdevice-net-certutil`), which stays manual. |
| `corosync_qnetd_client_cert_required` | `true` | Whether clients must present a TLS client certificate. Only takes effect when `corosync_qnetd_tls` is not `off`. |
| `corosync_qnetd_max_clients` | `0` | Maximum simultaneous client connections. `0` means no limit. |
| `corosync_qnetd_debug` | `false` | Turn on debug-level logging. |

### `vars/` — OS-specific (loaded via `include_vars`, not user-overridable)

| File | Variable | Value |
|------|----------|-------|
| `vars/Debian.yml` | `__corosync_qnetd_packages` | `[corosync-qnetd]` |
| `vars/Debian.yml` | `__corosync_qnetd_env_file` | `/etc/default/corosync-qnetd` |
| `vars/RedHat.yml` | `__corosync_qnetd_packages` | `[corosync-qnetd]` |
| `vars/RedHat.yml` | `__corosync_qnetd_enablerepo` | `highavailability` |
| `vars/RedHat.yml` | `__corosync_qnetd_env_file` | `/etc/sysconfig/corosync-qnetd` |

Task Flow
---------

1. **include_vars** — load OS-specific package list, env-file path (and,
   on EL, the repo to enable) from `vars/`
2. **Preflight** — assert Ansible >= 2.20
3. **Package install** — `apt` (Debian/Ubuntu) or `dnf` with
   `enablerepo: highavailability` (RedHat/EL)
4. **NSS certificate database** — `corosync-qnetd-certutil -i`; runs by
   default, since `corosync_qnetd_manage_nss_db` (`true`) and
   `corosync_qnetd_tls` (`on`) both default to values that trigger it.
   Skipped once the database already exists, or if either default is
   overridden so the condition is no longer met
5. **Configure** — template `COROSYNC_QNETD_OPTIONS` into the OS-specific
   env file from the `corosync_qnetd_*` variables above; notifies a
   handler that restarts the service on change
6. **Service** — enable and start `corosync-qnetd.service` when
   `corosync_qnetd_enable_service` is `true`

Manual step: certificate trust
-------------------------------

There are two distinct certificate concerns:

- **The daemon's own NSS database** (`corosync-qnetd-certutil -i`) —
  needed whenever `corosync_qnetd_tls` is `on` or `required`, which is
  the default. The role creates this database for you automatically
  (`corosync_qnetd_manage_nss_db` defaults to `true`); only build it
  yourself if you've set `corosync_qnetd_manage_nss_db: false`.
- **Per-cluster trust** (`corosync-qdevice-net-certutil`) — always manual,
  regardless of the daemon's TLS setting or `corosync_qnetd_manage_nss_db`.
  It's an inherently multi-host operation (run from each client cluster,
  against this qnetd host) that this role intentionally stays out of —
  see DESIGN.md. For example:

  ```bash
  corosync-qdevice-net-certutil -i -c <qnetd-host>
  ```

Consult the [corosync qdevice documentation](https://manpages.debian.org/corosync-qdevice)
for the full certificate exchange sequence for your cluster software
(e.g. Proxmox VE's `pvecm qdevice setup` wraps this for you — see
[PVE cluster side: setting up the QDevice](#pve-cluster-side-setting-up-the-qdevice)
below).

PVE cluster side: setting up the QDevice
-----------------------------------------

Everything below runs **on the Proxmox VE cluster**, against this
already-converged qnetd host — none of it is performed by this role.
Source: [Proxmox VE Cluster Manager — Corosync External Vote Support](https://pve.proxmox.com/pve-docs/chapter-pvecm.html#_corosync_external_vote_support).

Prerequisites:

- An even number of cluster nodes — Proxmox supports QDevices for
  even-sized clusters and specifically recommends them for 2-node
  clusters; odd-sized clusters are discouraged.
- All cluster nodes online.
- Network access from every cluster node to this qnetd host on
  TCP/5403 (see [Firewall](#firewall) below).
- Root SSH access from a cluster node to this qnetd host: key-based,
  or password root login temporarily enabled for the setup.
- Proxmox's documentation states daemon-to-cluster traffic must be
  encrypted — this qnetd host satisfies that out of the box, since
  `corosync_qnetd_tls` and `corosync_qnetd_manage_nss_db` both default
  to `on`/`true` (see the warning above). If you've overridden either
  to `off`/`false`, set them back before running the steps below.

Steps, run on the **PVE side**:

1. Install `corosync-qdevice` on every cluster node:

   ```bash
   pve# apt install corosync-qdevice
   ```

2. From one cluster node, set up the QDevice against this qnetd host:

   ```bash
   pve# pvecm qdevice setup <this-qnetd-host-IP>
   ```

   This copies the cluster's SSH key to the qnetd host and performs
   the certificate exchange automatically — no manual
   `corosync-qdevice-net-certutil` commands are needed on the PVE
   side. If it fails with `Host key verification failed.`, run `pvecm
   updatecerts` on the PVE node and retry.

3. Verify the QDevice is active:

   ```bash
   pve# pvecm status
   ```

   A working QDevice shows up in the `Membership information` table
   with `A,V,...` flags (Alive, Voting) and adds one vote to `Total
   votes`.

To remove it later:

```bash
pve# pvecm qdevice remove
```

Firewall
--------

Not managed by this role. `corosync-qnetd` listens on TCP/5403 — open
that port from each client cluster to the qnetd host through whatever
firewall tooling you already use.

Dependencies
------------

None.

Example Playbook
----------------

```yaml
- hosts: qnetd_servers
  roles:
    - role: realtime.corosync_qnetd
```

Delay service start until after certificate trust is configured:

```yaml
- hosts: qnetd_servers
  roles:
    - role: realtime.corosync_qnetd
      vars:
        corosync_qnetd_enable_service: false
```

License
-------

MIT

Author Information
------------------

Bob Tanner
