# Kernel development

Use the target tree's `Documentation/`, subsystem conventions, Kconfig,
Makefiles, nearby callers, and tests. Paths in this reference refer to that
tree; exact evidence snapshots are in [sources](sources.md).

## Build and configuration

Identify branch/base, downstream patches, `ARCH`, toolchain and cross-toolchain,
output directory, configuration provenance, and whether the feature is built-in,
modular, or disabled. Record relevant dependencies and `CONFIG_*` values without
dumping unrelated configuration. An object build with the feature disabled does
not cover the changed code.

- Use Kbuild rather than compiling a `.c` file with a host command. Match the
  tree's compiler requirements and its choice of GCC or Clang/LLVM, linker,
  assembler, and Rust tooling where applicable. Keep the same selection during
  configuration and compilation.
- Use an authorized output directory (`O=`) consistently when the project uses
  one. Configuration updates such as `olddefconfig` write files; preserve the
  seed and inspect the resulting relevant changes. Do not casually replace a
  working target configuration with `defconfig`, `allmodconfig`, or the host's
  `localmodconfig`.
- For an external module, use the intended kernel's prepared build tree and
  its module workflow, not whichever headers happen to be installed. Check
  symbol/versioning, configuration, signing, and loading requirements. A module
  compilation alone does not prove it can load or operate on the target.
  `modules_prepare` does not generate `Module.symvers`; with
  `CONFIG_MODVERSIONS`, use matching symbol/version artifacts from the intended
  kernel build rather than suppressing modpost errors.
- Inspect repository scripts before running them. Build targets may generate
  artifacts or call tools; test targets may boot VMs or manipulate devices.
  Keep installs, initramfs updates, module loads, and bootloader edits separate
  from compilation and within the user's authorization.

For an already configured tree, explicitly select `build_dir`, `target_arch`,
and `subsystem_target` (for example, `drivers/usb/serial/`), and retain its
toolchain selection. These command shapes are conditional examples:

```sh
make O="$build_dir" ARCH="$target_arch" W=1 "$subsystem_target"
make O="$build_dir" ARCH="$target_arch" C=1 "$subsystem_target"
"$KERNEL_TREE/scripts/checkpatch.pl" /path/to/change.patch
```

`C=1` needs Sparse installed. Checkpatch is a review aid; neither tool proves
runtime correctness. Do not automatically fix every warning or reformat
unrelated code to satisfy a generic style recipe.

## Execution context, ownership, and ordering

Before selecting an allocation, lock, or wait, establish the actual context:
process, workqueue, softirq, hard IRQ, timer, RCU read-side section, or another
subsystem-specific callback. Check preemption/IRQ state and held locks.

- A sleepable context is a prerequisite for blocking locks, waits, and
  allocations that can reclaim. `GFP_ATOMIC` is not a general repair for
  blocking code: redesign context or lifetime when needed. Check RT-specific
  locking behavior rather than assuming every spinlock has identical semantics.
- Match each API's failure convention: an error pointer needs `IS_ERR` and
  `PTR_ERR`, while `NULL` can mean failure or an absent optional resource.
  Do not collapse those states or translate `-EPROBE_DEFER` into a permanent
  failure; follow the driver's dependency and probe/unwind contract.
- Bound user-triggered allocations and use overflow-aware size helpers such as
  `struct_size`, `kmalloc_array`, or `kcalloc` instead of open-coded size
  arithmetic. Select accounting/reclaim flags from allocation ownership and
  context, and preserve an explicit allocation-failure path.
- State lock order and what each lock protects. Use the subsystem's existing
  IRQ-safe or bottom-half-safe variants when required. Account for callback
  reentrancy and teardown; moving work outside a lock also changes lifetime.
- Keep object existence, references, publication, and field synchronization
  separate. A refcount does not by itself synchronize every field. RCU needs
  the tree's publication/access primitives and appropriate deferred reclamation.
- `volatile`, `READ_ONCE`, and `WRITE_ONCE` do not substitute for the ordering
  contract of a lock or acquire/release operation. Use the kernel memory model
  and a litmus test where the ordering argument is the change.
- Track partial initialization and unwind each acquired resource once. Managed
  device resources simplify release, but do not establish that IRQs, work,
  timers, DMA, or external references are quiescent before their data disappears.
  Check synchronous cancellation rules and deadlocks with locks held at teardown.
- Keep virtual addresses, physical addresses, and DMA addresses distinct.
  Follow the subsystem's DMA mapping, cache coherency, and device ordering
  APIs; CPU memory ordering alone cannot establish a device contract.

## Userspace boundaries

Treat UAPI as a compatibility commitment even when an internal helper changes.
For ioctl and shared structures, check fixed-width fields, alignment and
padding, 32/64-bit compat behavior, endianness where specified, reserved fields,
unknown flags/commands, lengths, arithmetic overflow, and initialized output.
Avoid exposing kernel pointers or copying uninitialized padding to userspace.

Use the appropriate user-access helpers rather than dereferencing `__user`
pointers. `copy_from_user` and `copy_to_user` return bytes **not copied**, unlike
helpers that return a negative errno. They may fault and sleep; verify context
and the subsystem's partial-copy semantics. Keep validation tied to the data
actually used, including mutation between separate user-memory reads.

Do not break established ioctls to fit a new structure. Follow the subsystem's
extension scheme and preserve old command behavior. Kernel error conventions,
libc's `-1` plus `errno`, and subsystem-specific returns are distinct contracts.
For new ioctl commands, use the appropriate `_IO*` encoding and pass the
pointed-to **type**, not `sizeof(type)`, where a data-type parameter is required
(`_IO` has none). An unknown command should return `-ENOTTY` or `-ENOIOCTLCMD`
from the handler, yielding `ENOTTY` at the userspace boundary; do not use a
generic `-EINVAL` fallback.

For a new or changed interface, update its ABI/subsystem documentation and
affected consumers. For exported header changes, use the selected tree's UAPI
checker where supported, with the correct base/architecture and prerequisites;
a compatible header layout does not prove compatible behavior.

## Validation choices

- KUnit exercises in-kernel functions and internal state. kselftest exercises
  interfaces from userspace, sometimes with supporting kernel modules. Inspect
  the selected suite's configuration, command, privileges, and machine effects.
  Inspect build and TAP/KTAP results: this tree's multi-target selftest build can
  succeed when only one target builds. Use `FORCE_TARGETS=1` when all selected
  targets must build, and report runtime skips separately from passing cases.
- Build relevant architecture/configuration combinations: built-in/module,
  optional features, compat ABI, or alternate compiler only when affected or
  required by the project. Avoid a universal expensive matrix.
- For Kconfig changes, inspect dependency/default/help semantics and compile
  affected disabled and modular consumers. For Device Tree changes, run both
  the relevant `dt_binding_check` and `dtbs_check` lanes when available:
  `dtbs_check` can skip schemas that contain errors.
- Choose targeted diagnostics for the hypothesis: lockdep and atomic-sleep
  checks for locking/context; KASAN for memory safety; KCSAN for races; fault
  injection for unwind paths; subsystem tracing for lifecycle and timing.
  Configuration and overhead affect which failure a run can reveal.
- Confirm tests ran on the **built kernel**, record config and test counts,
  and inspect warnings/oopses as well as exit status. A VM can cover many
  kernel paths; hardware power, DMA, IRQ, suspend/resume, and hotplug claims
  often need the actual device.

If preparing an upstream patch, consult that tree's submission and maintainer
guidance. Produce reviewable material within scope; documentation about mailing
lists or tracker workflows is not authorization to contact anyone.
