#!/usr/bin/env bash
set -euo pipefail

SKILLS=(ex re arch impl qa sec devops orch)

for skill in "${SKILLS[@]}"; do
  echo "Installing $skill..."
  npx skills add "$skill"
done

echo "All skills installed."
