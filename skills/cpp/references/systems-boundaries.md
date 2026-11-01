# Systems, byte processing and native interfaces

Keep unchecked code behind a boundary that validates input and exposes explicit
ownership and failure. Read the pinned platform/API contract before translating
C examples into C++ wrappers.

## Bytes and arithmetic

- Validate sizes, offsets, element counts and total retained work before growth.
  For a validated `offset <= size`, compare `length <= size - offset` rather than
  trusting an overflowing `offset + length`. Check count × element-size before
  allocation. A per-buffer cap is not an aggregate budget.
- Do not reinterpret arbitrary bytes as live, aligned C++ objects. Account for
  lifetime, alignment, aliasing, representation and bounds separately. `memcpy`
  or supported `bit_cast` can solve limited representation transfers; neither
  validates an arbitrary external representation or serialized pointer.
- Signed overflow and invalid shifts can be undefined; unsigned wrap is defined
  but often invalid for a length. Define saturate/reject/wrap policy explicitly.
  Byte classification and indexing need the API's unsigned-char domain.
- Object padding, host endianness, bitfield layout and `sizeof(struct)` are not
  a portable wire format. Decode fields with explicit widths and byte order.
- A byte span is not necessarily text, UTF-8, terminated, or host-addressable.
  Validate the promised encoding and truncation rules. For framed streams, cover
  fragmented/coalesced input and a limit crossed by the delimiter-containing chunk.

Check canonical/minimal representation and intended byte consumption separately
from decoded values. A protocol may reject alternative encodings of the same
value. Disabling a size check for generic numeric use does not imply permission
to relax canonicality or other independent validation rules.

Fuzz/property tests should cover empty, exact-limit, over-limit, truncated,
malformed and recovery cases with bounded work. Preserve explicit refusal outcomes;
do not reinterpret failed decoding as successful raw data unless the API explicitly
reports that degraded result.

## Operating-system resources

Use the project's FD/handle/FILE/mapping/socket wrappers with the correct invalid
sentinel and deleter. Do not substitute `delete` for an API's release function or
`fclose` for an independently owned file descriptor. Descriptor reuse means an
integer alone is not durable identity.

Reads/writes may be partial; write-all needs an offset loop and a defined policy
for zero progress. Retry interruption only where the particular operation and
platform make retry correct; `close` and partially completed effects need special
care. Capture the error before cleanup. Report flush/finalization failure when
data persistence is promised; successful destruction does not establish durability.

Process code must handle failed spawn/exec, parent/child descriptor ownership,
redirection errors, interrupted waits and exit-versus-signal status. After fork in
a multithreaded process, only permitted async-signal-safe operations are safe
until exec; ordinary C++ allocation, logging and destructor paths are unsuitable.
Use the platform's spawn facilities or an established repository wrapper when
appropriate. A failed-exec child should use the intended immediate exit path
rather than running inherited buffered cleanup.

Signal handlers are not ordinary callbacks: use the platform's permitted
operations and notification pattern. Standard-library containers, streams,
allocation and arbitrary mutex use are not generic signal-safe operations.

Filesystem traversal needs a policy for symlinks, races, inaccessible entries,
depth/path limits and file identity. A fixed path buffer plus unchecked truncation
is not a robust traversal. Advisory locking works only with cooperating actors;
thread synchronization and atomic replacement address different contracts.

## Foreign and device code

Validate lengths, enum values, handles, nullability and ownership at the real
host boundary. Keep exceptions inside the established translation boundary.
Document who retains callback userdata and when a successful unregister/close
actually permits freeing it. GPU submission completion and CPU return are often
different events; retain buffers and backend state until the relevant fence/event
or runtime completion. Qualify platform/backend lanes on their actual host rather
than generalizing a CPU unit test to graphics, CUDA, or a foreign runtime.
