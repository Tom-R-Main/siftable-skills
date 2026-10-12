# Third-party notices

Original skills and portable adaptations are maintained by Thomas Main.

`skills/human-writing/scripts/postprocess_output.py` adapts the deterministic Unicode-cleaning layer from [`guillaumemeyer/watermarks-remover`](https://github.com/guillaumemeyer/watermarks-remover), version 0.3.1, under the MIT License. The pinned upstream notice and license are preserved at [`skills/human-writing/references/watermarks-remover-license.txt`](skills/human-writing/references/watermarks-remover-license.txt).

The Tometo and pstack workflow adaptations derive from Lauren Tan's MIT-licensed
[pstack](https://github.com/cursor/plugins/tree/5bf2b1544db739998121a306340631963c2ff3de/pstack)
at commits `5bf2b1544db739998121a306340631963c2ff3de` and
`7022c81efb48d8b5eb15498ce6043a3bd74b694c`. Their source notes identify the
applicable revision. The [upstream MIT notice](third_party/pstack-LICENSE.txt)
is also bundled with each derived skill so individual installations retain it.

`playwright`, `gh-fix-ci`, and `terraform-gcp` retain their bundled Apache 2.0 licenses and notices
from the OpenAI skills collection. The portable changes do not grant tool access,
provider subscriptions, or permission to redistribute external runtime engines.

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
