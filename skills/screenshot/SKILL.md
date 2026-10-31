---
name: screenshot
description: Capture a desktop, application, window, or pixel region when requested, or when an available tool-specific capture cannot observe the target surface.
license: Apache-2.0
---

# Screenshot capture

Prefer the target application's configured capture tool for browser, design, or document surfaces. Use the bundled OS helpers when a desktop capture is requested or the tool-specific route cannot observe the target. Resolve paths relative to this skill directory.

Save to the user's specified path. Otherwise use the authorized workspace's artifact directory for inspection captures, or the OS default screenshot location for a user-requested capture when that location is permitted. Capture only the requested application, window, or region where possible; avoid unrelated private windows and notifications.

Inspect supported options before capture:

```bash
python3 scripts/take_screenshot.py --help
```

On macOS, the helper needs Screen Recording access. If access is missing, explain the requirement before requesting it with `scripts/ensure_macos_permissions.sh`. Permission prompts and capture are separate from this package's installation. The helper uses a temporary Swift module cache; it does not install a compiler.

For Windows, use `scripts/take_screenshot.ps1`; Linux and macOS use `scripts/take_screenshot.py`. A missing display server, capture utility, or permission is a concrete capability gap. Do not install tools or change system settings automatically.

Open the saved image to verify that it shows the intended surface and provide its path. A screenshot proves visible state at capture time; it does not prove a preceding action succeeded or that the state remains current.
