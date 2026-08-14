# Source grounding

This skill is an original synthesis of practical Zig implementation and review work. External sources establish language behavior, document versioned APIs, or provide examples that informed a convention. They do not replace the pinned compiler, the target repository, or direct measurement.

## Authoritative versioned sources

- [Zig 0.16.0 language reference](https://ziglang.org/documentation/0.16.0/) grounds language semantics, build modes, `comptime`, error unions, `defer`/`errdefer`, and allocator selection.
- [Zig 0.16.0 standard library](https://ziglang.org/documentation/0.16.0/std/) grounds concrete standard-library types and signatures.
- [Zig 0.16.0 release notes](https://ziglang.org/download/0.16.0/release-notes.html) ground the `std.Io`, container, build-system, and migration guidance specific to that release.
- [Zig build-system documentation](https://ziglang.org/learn/build-system/) grounds modules, dependencies, artifacts, and build steps.

Use the matching versioned documentation when a project pins another Zig release. Use master documentation only as migration input.

## Adopted convention

The `_count`, `_index`, `_size`, and `_offset` naming guidance is adapted as an optional low-level review convention from [TigerBeetle's style guide](https://github.com/tigerbeetle/tigerbeetle/blob/main/docs/TIGER_STYLE.md#off-by-one-errors). TigerBeetle treats indexes, counts, and byte sizes as conceptually distinct units to make conversions and off-by-one risks visible. This skill generalizes that convention but does not require it when a project has clearer established terminology.

## Community inputs

These Ziggit discussions informed questions and failure modes, not normative rules:

- [Error recovery and old-school try/catch expectations](https://ziggit.dev/t/idiom-for-an-old-school-try-catch-block/3821)
- [`anytype` contract and tooling tradeoffs](https://ziggit.dev/t/discussion-a-potential-solution-to-the-anytype-problem/16259)
- [`std.Io` design discussion](https://ziggit.dev/t/discussion-about-io-and-zig/14033)
- [Local and external dependency structure](https://ziggit.dev/t/best-practices-for-structuring-zig-projects-with-external-dependencies/3723)
- [Devirtualization and specialization limits](https://ziggit.dev/t/the-limits-of-devirtualization/14015)
- [Community code-smell survey](https://ziggit.dev/t/zig-code-smells/2928)

Forum consensus is evidence of practitioner experience, not proof of language behavior. Cross-check it against the pinned compiler, official documentation, local code, and tests.

## Original synthesis boundary

The workflow ordering, host-versus-Zig decision boundary, ownership review, semantic error-boundary guidance, validation ladder, FFI containment, and measurement rules are this skill's synthesis. No third-party code or copied corpus is bundled in the Zig package.
