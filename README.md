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
- Templates the daemon's command-line options (listen address/port,
  address family, TLS mode, max clients, debug logging) into the env
  file `corosync-qnetd.service` reads at startup
- Enables and starts the `corosync-qnetd` service

Per-cluster TLS certificate trust setup is **out of scope** and remains a
manual step — see [Manual step: certificate trust](#manual-step-certificate-trust)
below.

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
| `corosync_qnetd_tls` | `"off"` | `on`, `off`, or `required`. `on`/`required` need the daemon's own NSS certificate database (`corosync-qnetd-certutil -i`), which this role does not create. Defaults to `off` so every supported platform starts cleanly with no manual steps. |
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
4. **Configure** — template `COROSYNC_QNETD_OPTIONS` into the OS-specific
   env file from the `corosync_qnetd_*` variables above; notifies a
   handler that restarts the service on change
5. **Service** — enable and start `corosync-qnetd.service` when
   `corosync_qnetd_enable_service` is `true`

Manual step: certificate trust
-------------------------------

There are two distinct certificate concerns, and this role intentionally
stays out of both:

- **The daemon's own NSS database** (`corosync-qnetd-certutil -i`) — only
  needed if you set `corosync_qnetd_tls` to `on` or `required`. The role
  defaults `corosync_qnetd_tls` to `off` specifically so no cert database
  is required out of the box. If you turn TLS on, create this database
  yourself before the service (re)starts.
- **Per-cluster trust** (`corosync-qdevice-net-certutil`) — run from each
  client cluster, regardless of the daemon's TLS setting, e.g.:

  ```bash
  corosync-qdevice-net-certutil -i -c <qnetd-host>
  ```

Consult the [corosync qdevice documentation](https://manpages.debian.org/corosync-qdevice)
for the full certificate exchange sequence for your cluster software
(e.g. Proxmox VE's `pvecm qdevice setup` wraps this for you).

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
