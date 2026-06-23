# TODO — realtime.corosync_qnetd build session 2026-06-23

This role did not exist before this session — the directory was empty, no
upstream project by this name was found, and the role was built from
scratch as an **original** role (not a fork) per user confirmation.

## What was done

### Step 1 — Config files synced from _template
- `.ansible-lint`, `.gitignore`, `.pre-commit-config.yaml`, `.yamllint`,
  `ruff.toml` — copied verbatim, no modifications needed.

### Step 1b — Legacy CI files
N/A — brand-new role, nothing to remove.

### Step 2 — CLAUDE.md generated
New file. No `{{UPSTREAM_NOTICE}}` (original role). Settled decisions
section records the four scope choices confirmed via clarifying questions
(original role, daemon+service-only scope, standard platform matrix, no
firewall management). Open questions cover future cert-trust automation,
firewall variable, and config templating.

### meta/main.yml + meta/argument_specs.yml
- GitLab issue tracker (original role convention), Bob Tanner sole author,
  `min_ansible_version: "2.20"`.
- Platforms: Ubuntu (jammy/noble/resolute), Debian (bookworm/trixie),
  EL ("9"/"10").
- Two variables documented end-to-end: `corosync_qnetd_enable_service`,
  `corosync_qnetd_extra_packages`.

### defaults/ and vars/
- `defaults/main.yml` — the two user-overridable variables.
- `vars/Debian.yml`, `vars/RedHat.yml` — `__corosync_qnetd_packages`;
  `vars/RedHat.yml` also sets `__corosync_qnetd_enablerepo:
  highavailability` (EL ships the package in a repo that's disabled by
  default).
- `vars/main.yml` — intentionally empty `first_found` fallback.

### tasks/preflight.yml + tasks/main.yml
- `preflight.yml`: asserts `ansible_version.full >= 2.20`.
- `main.yml`: include_vars (OS-specific) → preflight → `apt` install
  (Debian) → `dnf` install with `enablerepo` (RedHat) →
  `systemd_service` enable+start, gated on `corosync_qnetd_enable_service`.

### README.md
Requirements, supported-platforms table, both variable tables
(`defaults/` and `vars/`), task flow, a dedicated manual
certificate-trust section (`corosync-qdevice-net-certutil`), a firewall
section noting TCP/5403 is unmanaged, and two example playbooks.

### Steps 9–13 — Molecule scenario + testinfra suite
- `molecule/default/molecule.yml` — 7-platform matrix (ubuntu-jammy,
  ubuntu-noble, ubuntu-resolute, debian-bookworm, debian-trixie, el-9,
  el-10), testinfra verifier, full `destroy/create/converge/idempotence/
  verify/destroy` sequence.
- `molecule/default/converge.yml` — apt/dnf cache pre_tasks, role
  invoked via `MOLECULE_PROJECT_DIRECTORY`. No variable overrides: the
  role's own defaults (service enabled+started) are exercised directly,
  unlike `ansible-role-nut`, which has to disable service management
  because NUT needs UPS hardware. corosync-qnetd has no such hardware
  dependency — see Open items below for the one real unknown.
- `molecule/default/tests/`: `__init__.py`, `_data.py` (OS-family sets,
  package lists, service name), `conftest.py` (placeholder — no fixtures
  needed yet), `test_packages.py` (OS-aware package install checks),
  `test_service.py` (service enabled + running).
- `molecule/requirements.txt` — pinned tool versions, matching every
  other role in this repo.

### Step 8/9 — Config templating (added after initial build)

Follow-up feature request: template the daemon's command-line options
into its env file, scoped via two clarifying questions (common
SYNOPSIS-level flags only; `corosync_qnetd_tls` defaults `"off"`, no
automated cert-init task). Full rationale in `DESIGN.md`.

- `defaults/main.yml` + `meta/argument_specs.yml` — seven new variables:
  `corosync_qnetd_listen_address`, `_listen_port`, `_address_family`,
  `_tls`, `_client_cert_required`, `_max_clients`, `_debug`.
- `templates/corosync-qnetd.j2` — builds `COROSYNC_QNETD_OPTIONS` from
  those variables. Verified two ways: a local jinja2 mock harness, and a
  real `ansible-playbook` run via `ansible.builtin.template` against
  both the pure-defaults case and a fully-customized case — output was
  clean and byte-correct in both.
- `vars/Debian.yml` / `vars/RedHat.yml` — `__corosync_qnetd_env_file`
  (`/etc/default/corosync-qnetd` vs `/etc/sysconfig/corosync-qnetd`),
  confirmed against the upstream `corosync/corosync-qdevice` systemd
  unit and sysconfig example.
- `handlers/main.yml` — new `Restart corosync-qnetd` handler, gated on
  `corosync_qnetd_enable_service`.
- `tasks/main.yml` — new templating task between package install and
  service-enable, notifying the restart handler.
- `README.md` / `CLAUDE.md` — updated variable tables, task flow, and
  settled decisions.
- `DESIGN.md` — new file; the role's first, written specifically to
  carry this feature's scope rationale (see Open items below — it was
  previously missing entirely).
- `molecule/default/tests/_data.py` + `conftest.py` + `test_config.py` —
  env-file path fixture plus four tests (exists, owner, mode, default
  rendered content).
- Lint: `yamllint --strict`, `ansible-lint`, `ruff check`/`ruff format
  --check`, `ansible-playbook --syntax-check` all clean on first pass —
  no findings to fix this round.

### realtime.corosync_qnetd symlink
Added at the roles root, pointing at
`git_repository/ansible-role-corosync_qnetd`, matching the convention
every other role in this repo follows.

### Lint / syntax verification
Ran in this sandbox (no Docker available — see Open items):
- `yamllint --strict .` — clean.
- `ansible-lint .` — 0 failures, 0 warnings, production profile.
- `ruff check .` / `ruff format --check .` — clean. One real finding
  fixed along the way: `test_packages.py` originally took a boolean
  fixture (`is_redhat: bool`) as a parameter, which `ruff`'s `FBT001`
  rule (boolean positional trap) correctly flagged — this repo's
  `ruff.toml` selects `ALL` and does not exempt it. Fixed by inlining
  the OS-family check instead, matching `ansible-role-nut`'s
  `test_packages.py` pattern exactly. The unused fixture was removed
  from `conftest.py` accordingly.
- `ansible-playbook --syntax-check` against a throwaway playbook that
  invokes the role — passed.

The sandbox's pip-installed `ansible-core` is 2.17.14, below this role's
own `min_ansible_version: "2.20"` — `--syntax-check` doesn't execute
tasks so the version preflight assertion was never actually exercised
here. Not a defect in the role; just a ceiling on what this sandbox
can verify.

---

## Open items / TODOs

### High priority

- **Delete the stray nested `.git/` directory in this role folder before
  committing.** Running `ansible-lint`/`git status` in this session's
  sandbox auto-initialized an empty `.git/` here (no commits — just
  `git init` scaffolding) as a side effect of ansible-lint's `.gitignore`
  discovery logic. This sandbox's file-delete permission for that path
  was declined, so it's still present. If left in place, this role
  directory will look like a nested git repo to the parent
  `ansible-playbooks` checkout, and `git add` from the parent repo would
  try to track it as a broken submodule reference instead of as normal
  files. Remove it directly on your machine: `rm -rf
  ansible-role-corosync_qnetd/.git`.

- **`molecule test` has never actually been run.** This sandbox has no
  Docker, so the entire 7-platform matrix — package install, the
  `enablerepo` path on EL, the service-start behavior, and now the new
  `test_config.py` env-file assertions — is untested beyond static
  lint/syntax checks and one real (non-Molecule) `ansible-playbook`
  template-render check. Run `molecule test` locally before trusting
  this role in production.

- ~~Whether `corosync-qnetd.service` starts cleanly out of the box on
  EL is unconfirmed.~~ **Resolved/moot.** This was about whether EL's
  package auto-creates the daemon's NSS certificate database the way
  Debian's postinst does. Now moot: `corosync_qnetd_tls` defaults to
  `"off"`, which needs no certificate database on any platform, so the
  role's default config no longer depends on that unconfirmed packaging
  detail. See `DESIGN.md`'s "Config templating" section. Still worth
  confirming `molecule test` is green on el-9/el-10, but no longer a
  blocking unknown.

- **No `LICENSE` file.** `README.md`'s license badge links to `LICENSE`,
  which doesn't exist — this mirrors an existing inconsistency already
  present in `ansible-role-serial_console` (also linked, also missing).
  Add a LICENSE file or drop the badge link; this is a repo-wide
  decision, not unique to this role.

### Medium priority

- **`ubuntu-resolute` and `rockylinux10` geerlingguy images** were
  marked "confirmed May 2026" in `_template/platform-eol.md` at the time
  this role was written. `ansible-role-serial_console`'s scenario still
  has resolute commented out pending image availability; this role
  assumes both images exist (matching `ansible-role-nut`, the most
  recently updated sibling role). Spot-check
  `docker pull geerlingguy/docker-ubuntu2604-ansible:latest` and
  `docker pull geerlingguy/docker-rockylinux10-ansible:latest` before
  relying on CI green for those two platforms.

- **No test exercises `corosync_qnetd_enable_service: false`.** The
  current scenario only covers the default (`true`) path. Adding a
  second value would currently require either a second Molecule
  scenario or per-platform `group_vars`, which felt like more
  complexity than this role's current scope justifies — revisit if a
  real use case needs the disabled-service path verified in CI.

### Low priority

- **`corosync_qnetd_extra_packages` is untested.** It's a thin
  passthrough appended to the OS package list; no converge fixture sets
  it, so no test asserts an extra package actually installs.

- **`-S` advanced settings are not exposed.** Deliberate — see
  `DESIGN.md`'s "Config templating" section. Revisit only if a concrete
  need for one specific advanced setting shows up; don't add a
  catch-all advanced-settings dict.

- **TLS-on path (`corosync_qnetd_tls: on`/`required`) is untested.**
  No converge fixture sets it, so no test confirms the daemon actually
  starts with TLS enabled — that also requires the daemon's own NSS
  certificate database to exist first, which this role still doesn't
  create (by design; see `DESIGN.md`). Revisit if/when someone sets
  `corosync_qnetd_tls` to something other than `"off"`.
