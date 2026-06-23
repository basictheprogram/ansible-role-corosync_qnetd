DESIGN.md — realtime.corosync_qnetd
====================================

This is the authoritative spec for this role. `CLAUDE.md` points here;
if code and this document disagree, this document wins — flag the
discrepancy and ask before "fixing" the design to match the code.

What this role is
------------------

`corosync-qnetd` is a standalone daemon, run outside any cluster, that
acts as a tie-breaker vote for `corosync-qdevice` clients — most
commonly a two-node Proxmox VE cluster that needs a third vote without
a third full cluster member. Per the upstream man page, it's designed
to be "almost configuration and state free": no cluster-specific config
file exists on the qnetd side, and a single qnetd host can serve many
unrelated clusters.

This role installs the package, optionally configures the daemon's
command-line options via one env file, and manages the systemd service.

Scope boundaries
-----------------

### Per-cluster TLS trust stays manual

`corosync-qdevice-net-certutil` exchanges certificates between this
qnetd host and each client cluster. It is **not** automated by this
role, and isn't expected to be:

* It's inherently a multi-host coordination problem — material has to
  move between the qnetd host and every client cluster's nodes. A
  single-role, single-host task can't safely do this without either a
  shared secrets store (Vault, etc. — not assumed to exist for every
  consumer of this role) or a hand-rolled key exchange (security
  liability not worth building for an op performed once per cluster).
* The upstream tooling already wraps this well for the common case
  (`pvecm qdevice setup` on Proxmox VE), so there's little value this
  role would add over documenting the manual command.

This would change if a concrete multi-cluster consumer showed up with
a safe, already-established secrets-distribution mechanism this role
could hook into — see Open questions.

### The daemon's own TLS cert database is a separate, smaller concern

Don't confuse the above with `corosync-qnetd-certutil -i`, which only
creates the daemon's own local NSS database (a self-signed CA + server
cert) so the daemon can speak TLS at all. This is single-host and fully
automatable in principle — Debian's package postinst already runs it
automatically. This role still doesn't run it, for a narrower reason:
see "Config templating" below.

### Firewall (TCP/5403) is out of scope

Not managed by this role. Whatever firewall role or tooling a
consuming playbook already uses to manage host firewalls is expected
to own opening TCP/5403 from client clusters to the qnetd host. Folding
firewall management into every service role that needs a port open
doesn't scale; it belongs in one place.

### EL `HighAvailability` repo: enabled per-transaction, not persistently

EL ships `corosync-qnetd` in the `HighAvailability` repo, present but
disabled by default on Rocky/Alma/RHEL. The install task passes
`enablerepo: highavailability` to `dnf`, which enables the repo only
for that single transaction — no repo file is added or modified.
Don't "fix" this into a persistent `ansible.builtin.yum_repository` /
`community.general.ini_file` toggle; that's a deliberate choice to
avoid silently widening what package sources a host trusts long-term.

Config templating
------------------

`corosync-qnetd` has no structured config file. Every runtime setting
is a command-line flag, and the only place those flags live on disk is
one env file — `/etc/default/corosync-qnetd` (Debian/Ubuntu) or
`/etc/sysconfig/corosync-qnetd` (EL) — sourced by `corosync-qnetd.service`
via `EnvironmentFile=` into a single `COROSYNC_QNETD_OPTIONS` variable.
This role templates that one file from `corosync_qnetd_*` defaults.

Two scope decisions, made explicitly rather than guessed:

* **Only the SYNOPSIS-level flags are exposed as variables** — listen
  address, port, address family, TLS mode, client-cert-required, max
  clients, debug. The man page also documents roughly fourteen further
  "advanced" settings via `-S` (`nss_db_dir`, `cert_nickname`, heartbeat
  and dead-peer-detection timing, buffer sizes, etc.), but says outright
  that most of them "shouldn't be generally used... not safe to
  change." Exposing them as role variables would mean documenting and
  testing footguns nobody asked for. If a real need shows up, add a
  narrowly-scoped variable for that one setting rather than a
  catch-all advanced-settings dict.
* **`corosync_qnetd_tls` defaults to `"off"`**, not upstream's own
  default of `"on"`. `on`/`required` require the daemon's own NSS
  certificate database to already exist. Debian's package creates it
  automatically in postinst; it was never confirmed whether EL's
  package does the same (see `TODO.md` history — this is why that
  question existed). Rather than have the role's default behavior
  depend on an unconfirmed, platform-specific packaging detail, the
  default avoids the dependency entirely: TLS off needs no certificate
  database on any platform. Sites that want TLS create the database
  themselves (`corosync-qnetd-certutil -i`) and then set
  `corosync_qnetd_tls: on` — explicitly, with full awareness of the
  prerequisite, rather than the role silently depending on packaging
  behavior that varies by distro.

Generic by design
------------------

Every `corosync_qnetd_*` default is either empty/wildcard or matches
upstream's own default (port 5403, address family "any", max clients
0/unlimited, debug off — TLS being the one deliberate exception above).
None of them encode a specific site's listen address, port, or TLS
posture. Customer- or site-specific values belong in `group_vars` /
`host_vars` on the consuming inventory, not in this role's defaults —
the role's job is to expose the right knobs, not to guess values for
them.

Settled decisions
------------------

* Original role, not a fork — no upstream project by this exact name
  exists. GitLab issue tracker, Bob Tanner sole author.
* Scope: daemon install + configure (env-file only) + service. No
  template/automate either certificate concern described above.
* Platform matrix: Ubuntu (jammy/noble/resolute), Debian
  (bookworm/trixie), EL ("9"/"10").
* Firewall (TCP/5403) is out of scope.
* Config surface is the SYNOPSIS-level flags only; no `-S` advanced
  settings exposed.
* `corosync_qnetd_tls` defaults to `"off"`.

Open questions
---------------

If a task touches one of these, leave a `# TODO(open-q):` comment:

* Should firewall rules for TCP/5403 be added as an opt-in variable
  (e.g. `corosync_qnetd_manage_firewall`) once a consuming playbook
  needs it, or should that always live in a separate firewall role?
* Should TLS trust automation be added later via a dedicated task that
  shells out to `corosync-qdevice-net-certutil`, gated behind a
  variable, once there's a concrete multi-cluster use case to design
  against and a safe secrets-distribution mechanism to use?
* Should the role optionally manage the daemon's own NSS certificate
  database (`corosync-qnetd-certutil -i`, idempotent, only when
  `corosync_qnetd_tls` is not `off` and the database is absent)? Not
  done now because no one has asked for `corosync_qnetd_tls: on` yet —
  revisit if/when someone does.
* Should `corosync_qnetd_address_family`, `_tls`, etc. become real
  argument_specs `choices` enforcement failures rather than relying on
  `dnf`/daemon-side rejection of bad values? (They already have
  `choices:` in `meta/argument_specs.yml` — this is about whether that's
  sufficient or whether a preflight assertion should double-check.)
