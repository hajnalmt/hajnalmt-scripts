---
description: Probe which GitHub Copilot models work and sync the whitelist
agent: build
---
I ran the Copilot model probe below. It calls each candidate model through
`opencode run`, classifies them as working / blocked / flaky, and with
`--write` updates `provider.github-copilot.whitelist` in
~/.config/opencode/opencode.json:

!`~/Github/hajnalmt-scripts/opencode/copilot-model-check.sh --write 2>&1`

Based on the output above:
1. Summarise which models are working, blocked, and flaky.
2. Show the resulting `provider.github-copilot.whitelist` from the config file.
3. Remind me to restart opencode for the change to take effect.
