# Third-party notices

Original skills and portable adaptations are maintained by Thomas Main.

`skills/human-writing/scripts/postprocess_output.py` adapts the deterministic Unicode-cleaning layer from [`guillaumemeyer/watermarks-remover`](https://github.com/guillaumemeyer/watermarks-remover), version 0.3.1, under the MIT License. The pinned upstream notice and license are preserved at [`skills/human-writing/references/watermarks-remover-license.txt`](skills/human-writing/references/watermarks-remover-license.txt).

The Tometo and pstack workflow adaptations derive from Lauren Tan's MIT-licensed
[pstack](https://github.com/cursor/plugins/tree/5bf2b1544db739998121a306340631963c2ff3de/pstack)
initially at commits `5bf2b1544db739998121a306340631963c2ff3de` and
`7022c81efb48d8b5eb15498ce6043a3bd74b694c`, with later selective refreshes
identified by immutable revisions in each package's source notes. The [upstream MIT notice](third_party/pstack-LICENSE.txt)
is also bundled with each derived skill so individual installations retain it.

`emil-design-eng` and `break-ui` adapt Emil Kowalski's MIT-licensed
[skills](https://github.com/emilkowalski/skills/tree/2d228630ba1446365f614a108cb8252f1feda202)
at `2d228630ba1446365f614a108cb8252f1feda202`. Each package retains the
upstream license and a source/adaptation record.

`playwright`, `gh-fix-ci`, `terraform-gcp`, `pdf`, `screenshot`, `sentry`, and `transcribe` retain their bundled Apache 2.0 licenses and notices
from the OpenAI skills collection. The portable changes do not grant tool access,
provider subscriptions, or permission to redistribute external runtime engines.
The screenshot package retains the upstream OS helpers. PDF, Sentry, and
transcription entrypoints are portable adaptations without bundled provider
clients or a preferred machine-local parser.

`cloud-environment-runtime` is an original routing guide linked to official
documentation. It does not redistribute the managed-environment plugin's code,
network policy, credentials, or connector registration.

The current `c-systems-programming` skill is original repository material.
An earlier review-branch revision (`c087fd1`) briefly included a local tutorial
originating from The Bushido Collective's Han project. That historical tutorial
is attributable to The Bushido Collective and subject to its
[FSL-1.1-ALv2 terms](https://github.com/TheBushidoCollective/han/blob/main/LICENSE),
not this repository's MIT license. The current skill replaces that tutorial and
does not retain its text, examples, or installer metadata.
