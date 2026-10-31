# Services and Linux diagnosis

## systemd units and service lifecycle

First establish that systemd manages this workload, its version, and whether
the unit belongs to the system or user manager. Inspect the relevant unit and
drop-ins selectively; unit files and logs can contain secrets. An installed
unit, the manager's loaded definition, and the current process may differ.

- `After=`/`Before=` express ordering, while `Wants=`/`Requires=` pull units
  into the transaction with different dependency semantics. Neither alone
  proves another service is ready for an application request.
  The dependency's own startup contract determines what ordering waits for;
  changing the dependent application's `Type=` cannot create database readiness.
- Match `Type=` to the program's actual startup contract. `Type=notify` needs
  working notification support and the correct notification scope; it is not a
  substitute for implementing readiness. Socket activation needs intentional
  ownership and handling of inherited sockets.
- `ExecStart=` is not implicitly a shell command. Inspect executable paths,
  arguments, escaping/specifiers, working directory, identity, and environment
  sources without exposing secret values. Use the supported credential path
  where the deployment already provides one.
- Distinguish failed startup, crash, timeout, watchdog, dependency failure, and
  rate-limited restart. Restarting can hide the original evidence. A restart
  policy must fit durable state and idempotency; it does not fix the cause.
- Keep the manager's process/cgroup ownership intact. Check `KillMode=`, stop
  timeout, signal handling, and child reaping. A parent exit alone does not
  show that background children or resources were released.
  A coordinated `ExecStop=` must wait for shutdown; after it exits, remaining
  processes are subject to the manager's termination policy. It does not run
  after failed startup. Cleanup covering partial startup belongs in suitable
  `ExecStopPost=` logic that tolerates incomplete state and absent processes.
- Scope hardening to actual needs: service identity, permitted paths,
  capabilities, namespace and syscall restrictions. Verify the changed feature
  under those restrictions; do not copy a maximal hardening block or disable
  policy globally to make one operation succeed.
- Treat reload, restart, enablement, and `daemon-reload` as different actions.
  `daemon-reload` updates manager configuration; it does not restart the service
  or make a running process adopt all new settings. Activation requires the
  session's authority and a rollback appropriate to the target.

Validate with the target version's `systemd-analyze verify` where available,
then exercise readiness, a representative operation, failure/restart behavior
when changed, and graceful stop in an authorized test environment. Static
verification cannot prove deployment paths, secrets, permissions, or runtime
behavior. A successful TCP connect or active unit state is only one layer.

For systemd source changes, read its current scoped guidance and use configured
Meson targets and test names. In the reviewed tree, `meson test -C build -v
<test-name>` rebuilds prerequisites; the scoped agent guidance selects direct
Meson commands. Inspect the target revision before borrowing recipes from
`docs/HACKING.md`, which may describe a different environment. Use isolated
image/VM integration tests for manager, boot, or privileged behavior; do not
replace the host init to validate a source patch.

## Evidence-led diagnosis

Capture the symptom, time window, exact target, failing operation, and last
known working state. Form a testable hypothesis and choose the smallest probe
that distinguishes it. Preserve the failure before an authorized corrective
action; compare before/after using the same trigger.

Select probes rather than executing an exhaustive collection:

| Symptom | Useful evidence | Distinction to preserve |
| --- | --- | --- |
| Unit will not start | Selected unit/drop-ins, `systemctl show` properties, bounded unit journal | Parse/dependency failure versus failed process |
| Process hangs or leaks children | Relevant process state, wait path, cgroup membership, bounded trace if authorized | Parent, process group, reaper and descendants |
| CPU or latency regression | Representative load, CPU saturation, scheduler/I/O waits; targeted `perf`/trace if available | Work increased versus work waiting |
| Memory pressure or kill | Relevant cgroup limits/events, process memory, pressure and kernel log window | Application allocation, cgroup OOM and host OOM |
| Disk/full or slow writes | `df`, inode availability, relevant mounts, quotas, filesystem and device errors | Free blocks, inodes, quota, read-only/error state |
| Network failure | Namespace, routes, scoped socket state, DNS result, connection and application response | DNS, route, listener, policy, TLS and app readiness |
| Device or display failure | Device presence, driver binding, relevant kernel/session logs, seat/session state | Hardware/driver, permission, session and protocol |

Tools such as `journalctl -u <unit> --since <time> --no-pager`, `ss`, `ip`,
`vmstat`, or pressure/cgroup files are conditional on target availability,
permissions and the hypothesis. Keep time windows/output bounded and redact
sensitive fields. Broad tracing can capture payloads or change timing; choose
process/event filters and stop conditions before attaching.

Inspect the target's installed man pages, selected source, and distro docs for
version-specific commands or defaults. Do not install tracing tools, enable
kernel features, change sysctls, clear caches, kill processes, repair a mounted
filesystem, or reboot as part of read-only diagnosis. If correction needs new
authority, finish the evidence and a concrete proposed action first.

Report what each observation establishes. An open port does not prove TLS or
authentication, permission to read logs is not permission to restart, and a
quiet trace does not rule out a path it never observed.
