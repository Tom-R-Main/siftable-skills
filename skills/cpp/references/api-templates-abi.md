# API design, templates, headers and ABI

Preserve public source and binary compatibility according to the project's
release policy. A header edit can affect code outside the local link graph.
Search consumers and bindings before changing a public type or overload set.

## Design around the contract

Use values and concrete types where they express the boundary; borrow for
observation and transfer ownership for retained/consumed data. A span/view is
appropriate only when its lifetime, element mutability and supported standard
are clear. Preserve established nullable/optional and error conventions. Use
domain types for units or invalid states when they prevent an actual mistake;
avoid a new type hierarchy for an incidental conversion.

Choose templates for compile-time substitution and runtime interfaces/type
erasure for runtime heterogeneity. Account for instantiation, compile time,
binary size, diagnostics, ABI and inlining rather than calling one universally
faster. Virtual deletion through a base requires a suitable destruction contract;
use a virtual destructor where callers own derived objects through that base.

Constrain generic code to the operations it needs, using concepts only when the
selected language supports them. Preserve overload resolution and customization
points: forwarding references, `std::forward`, ADL, implicit conversions,
initializer-list preference and dependent names can alter behavior unexpectedly.
Read the full template diagnostic and reduce the failing instantiation under the
real flags before adding casts or broadening constraints. Don't make every input
a forwarding-reference template to avoid choosing an ownership contract.

## Headers and translation units

Make public headers self-contained under supported consumer settings; include
what declarations require and follow the repository's include/order policy.
Unity builds and precompiled headers can hide missing dependencies. Validate a
normal translation-unit/consumer lane when a header change warrants it.

Keep template definitions available at intended instantiation points or use the
project's explicit-instantiation design. Audit inline definitions, static data,
visibility and configuration macros for ODR consistency across translation units.
The same name compiling in two places does not prove identical definitions.
Do not turn an include fix into a module/PCH migration. C++ modules and header
units depend on the selected compiler, build graph and library support; module
artifacts are configuration-bound build outputs.

## Binary and host boundaries

Changes to class layout, virtual tables, exported symbols, calling conventions,
packing/alignment, enum representation, exceptions, RTTI or public template
instantiations may break binary consumers even when local tests compile. Standard
library types are not a portable cross-toolchain ABI. Match runtime/allocator and
debug modes; examples include MSVC CRT/iterator modes and libstdc++ dual-ABI
settings. Inspect platform policy rather than injecting a global compatibility
macro into one translation unit.

Use an intentional C ABI or the existing binding generator for foreign consumers.
An `extern "C"` name alone does not make C++ object layout, ownership, exceptions
or overloaded interfaces portable. Prefer opaque handles, fixed-width fields,
pointer-plus-length buffers and explicit version/error/ownership contracts where
the interface permits. Allocation and deallocation must use compatible owners;
an exported release function can keep allocation inside its originating module.

Validate an actual consumer, including shared-library load/link and lifetime/error
paths when changed. Symbol inspection or compilation alone cannot qualify callback
teardown, loader search behavior or a host's ABI assumptions.
