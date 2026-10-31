# Colophon adapter contract

The adapter is original standard-library integration code. It calls the separately installed [Colophon](https://github.com/Tom-R-Main/Colophon) CLI; it does not vendor that runtime, its dependencies, a corpus, or a writing model. A compatible runtime provides native `voice profiles list`, `voice profiles resolve`, and `voice prompt --receipt` commands.

## Private registry

Colophon owns registry discovery, validation, and profile resolution. The adapter forwards `--registry` when supplied. Native precedence is:

1. An explicit registry path.
2. `COLOPHON_PROFILES_FILE`.
3. `$XDG_CONFIG_HOME/colophon/profiles.json`, or `$HOME/.config/colophon/profiles.json` when XDG configuration is unset.

The [registry example](../assets/profiles.example.json) is a schema example, not a usable profile. Copy it to an authorized private location and replace the path with an existing local `VoiceProfile`. Paths are absolute or use home expansion; they are not resolved against whichever application repository happens to be current. Aliases use lowercase letters, digits, hyphens, and underscores, up to 64 characters.

Registry and profile files must be external to Git checkouts or untracked and Git-ignored. Tracked or nonignored files are refused, including resolved locations. Keep actual profiles, source works, annotations, extracted text, and derived prompts private. Ignore rules do not remove already tracked files and do not establish publication rights.

The registry explicitly names profiles. Listing does not recursively inspect directories, enumerate source works, or print passages. Resolving validates the selected multi-document `VoiceProfile` and returns its identity, hash, and limited metadata. The runtime is the authority on schema compatibility; the adapter verifies the returned identity before export.

## Public CLI

Set `COLOPHON_BIN` to a trusted executable when `colophon` is not on `PATH`, or pass `--runtime`. No shell command string or automatic installation is used.

```bash
python3 scripts/colophon_adapter.py --help
python3 scripts/colophon_adapter.py doctor
python3 scripts/colophon_adapter.py profiles
python3 scripts/colophon_adapter.py --registry "$PRIVATE_REGISTRY" \
  prompt my-voice --output "$PRIVATE_PROMPT" --mode numeric --task rewrite
python3 scripts/colophon_adapter.py check-candidate README.md README.candidate.md
```

Run these from the installed skill directory, or use its script's full path. Set the private registry and output paths deliberately; the adapter does not create a seeded library or configure credentials. The original document and candidate remain separate.

`doctor` checks the required local command interface. It does not qualify extraction quality, a provider, or a profile's suitability. A missing registry can be reported as `not_configured` with no profiles. Configuration and resolution errors remain explicit failures.

The adapter accepts files up to 16 MiB and runtime responses up to 256 KiB per stream. Prompt operations default to a 30-second timeout, configurable with `--timeout` up to 300 seconds. These are adapter bounds, not qualified Colophon corpus or document-capacity claims.

## Prompt export and readback

The adapter resolves the selected alias and invokes the native equivalent of:

```bash
colophon voice prompt "$RESOLVED_PROFILE" --task rewrite --mode numeric \
  -o "$PRIVATE_PROMPT" --receipt
```

Supported tasks are `rewrite` and `generate`; modes are `numeric`, `qualitative`, `exemplars`, and `hybrid`. Numerical guidance describes measurements. Qualitative guidance describes supported observations. Exemplar and hybrid guidance can contain source passages. Treat every exported prompt as private and review what would be disclosed before any authorized external generation.

Verify a native receipt's `status: written`, source profile ID/hash, and artifact byte count/hash against the actual files. A successful export establishes **prompt artifact only**. It does not establish that a writing model ran or that an output preserved facts, resembled a voice, read naturally, or avoided copying.

The adapter writes a separate new prompt output after its checks and refuses existing outputs. A failure, timeout, malformed receipt, identity mismatch, or uncertain readback must remain a failure or unresolved result; do not infer absence of an effect or automatically replay it. Read the returned recovery information and inspect retained artifacts where necessary.

Use a physical private output directory with no symlink components. The adapter checks the original output path before resolution and again before publication; an indirect path is refused even when its final target looks private. Native registry/profile path validation remains Colophon's responsibility.

## Markdown candidate checks

`check-candidate` compares protected technical structures in the source and candidate and leaves both files untouched. The guard covers fenced and indented code, inline code, and supported link/image/reference syntax. It uses a conservative Markdown subset and can refuse harmless reformatting. It is deliberately separate from generating prose. Full Markdown semantics, factual equivalence, quotations, and literary judgments still need source and diff review.

## Qualification

Bundled tests use synthetic profiles and an isolated fake runtime to challenge command dispatch, identity/readback failures, privacy boundaries, and candidate preservation. Real-runtime integration should use Colophon's synthetic corpus in task-owned temporary storage. No test requires a personal profile, author corpus, provider credential, or model call. Report fixture, installed-runtime, provider, and writing-quality results separately.
