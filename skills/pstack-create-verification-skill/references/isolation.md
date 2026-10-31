# Verify the run's isolation

Use when a verification recipe starts processes, seeds or resets state, or can reach shared storage or services. Determine the relevant effects from the real application and configuration schema. A separate branch, clone, worktree, port, or database does not by itself isolate file paths, devices, or outbound connections.

Before creating directories, seeding fixtures, or driving a mutable flow, establish the effective targets:

- Resolve writable roots and existing path ancestors, including symlinks. Require test-owned data and scratch paths to remain inside the designated run root; reject escaping links or aliases before any write through them. A path spelling that starts with the run directory is insufficient. Explicitly approved fixtures outside that root need independently enforced access limits.
- Bind database, profile, storage, sockets, devices, and service endpoints to this run's resources. Check effective application configuration, including defaults and inherited overrides, without printing secrets or reading secret files. A loopback service can still control the user's live hardware or app.
- Reject accidental fallback to live/shared resources. Disable or replace unrelated integrations with task-owned fixtures or stubs; exercise a real integration only within its explicit effect scope. Stub results cover the stub boundary, not the live integration.

Make launch/doctor enforce the relevant restrictions and read back the running instance's actual targets where possible. Do not infer ownership solely from a checkout name or a flag that another process can omit. If the harness can enforce only part of the boundary, record the remaining gap before driving effects.

Challenge a new or changed guard with a task-owned escaping-path fixture or disallowed endpoint and prove refusal before a write or connection. Use a run-owned sentinel or local decoy to observe this; do not probe a user's real files, devices, or service to test isolation. Match the checks to the application's actual effects rather than imposing unrelated infrastructure.

If containment or endpoint identity cannot be established, stop that affected drive and report the concrete unverified boundary. Correct owned harness drift within existing scope; product changes or broader integration access retain their own authorization. Preserve evidence after cleanup.

Source: Matt Pocock's CVM [scratch containment fix](https://github.com/mattpocock/course-video-manager/commit/89245b3099e6807026edf6a1eb799eac2555df1b), [storage guard](https://github.com/mattpocock/course-video-manager/commit/9354dd7e0a4252c68ba6e09677103fe08480b1ac), and [recorder endpoint guard](https://github.com/mattpocock/course-video-manager/commit/73d62e2d7cd77913cd5d365efb1d50545ed20571). Adapt the mechanism to the project; `/mnt` and recorder ports are not global rules.
