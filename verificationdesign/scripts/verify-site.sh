#!/usr/bin/env bash
set -euo pipefail

npm run build
npm run check
npm run lint:cards
npm run a11y
