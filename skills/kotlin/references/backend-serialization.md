# Backends, framework boundaries, and serialization

Use this reference when the repository already uses the framework or the user
asks to select it. Kotlin alone does not imply Spring, Ktor, JPA, or a particular
layered architecture.

## Runtime ownership and framework wiring

For Ktor, follow the pinned server/client APIs and configured plugins. Use
`testApplication` or the version's supported harness to verify route wiring,
status, response body, negotiation, validation, and relevant failures. An
in-process application test does not prove deployment configuration or real
database behavior.

For Spring, inspect compiler plugins, reflection/Jackson modules, annotation
targets, and proxy configuration. Kotlin classes and members are final by
default; the supported `kotlin-spring`/all-open setup may provide necessary
proxyability. Do not make every class open or give domain constructors fake
defaults to fix framework instantiation.

Trace the actual proxy/transaction boundary, especially self-invocation and
framework-managed versus manually created instances. Coroutine/reactive
transaction integration depends on the framework and driver version: verify
that propagation and thread/context assumptions remain valid across suspension.
Do not run blocking JDBC on an event-loop dispatcher or assume a suspend keyword
made database access nonblocking.

Treat entity identity, lazy loading, persistence lifecycle, and constructor
requirements independently of DTO convenience. Generated data-class equality or
toString may touch mutable/lazy properties. Use the repository's entity mapping
and no-arg/all-open configuration; test with the actual persistence adapter when
the changed contract depends on it.

## Wire contract

Distinguish the Kotlin serialization compiler plugin (aligned with its compiler)
from the independently versioned kotlinx serialization runtime. Generated
serializer failures may come from plugin application, source-set placement, or
version compatibility. Regenerate through the configured build; do not patch
generated serializers.

For kotlinx.serialization or Jackson, read the actual codec configuration and
annotations. Check:

- missing fields versus explicit nulls and constructor defaults;
- unknown keys, enum evolution, and malformed values;
- serialized names, discriminator names, and supported polymorphic subtypes;
- `encodeDefaults`, `explicitNulls`, contextual serializers and registered modules
  where used;
- stable representation of IDs, dates/times, numbers, and value classes.

Changing a nullable Kotlin property does not by itself define a compatible JSON
change. Test exact fixtures in the relevant producer/consumer direction; a
same-codec round trip can conceal an incompatible wire format. Preserve the
project's unknown-field policy instead of enabling leniency to hide a failure.
Translate expected decoding/validation failures at the API boundary without
swallowing cancellation or exposing payloads and credentials in diagnostics.

## Sources

- [Spring projects in Kotlin](https://docs.spring.io/spring-framework/reference/languages/kotlin/spring-projects-in.html)
- [Ktor server testing](https://ktor.io/docs/server-testing.html)
- [Kotlin serialization and independent library versions](https://kotlinlang.org/docs/serialization.html)
- [JsonBuilder options](https://kotlinlang.org/api/kotlinx.serialization/kotlinx-serialization-json/kotlinx.serialization.json/-json-builder/)
