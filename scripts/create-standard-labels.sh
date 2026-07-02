#!/usr/bin/env bash
# create-standard-labels.sh — apply the shared cross-project label taxonomy.
#
# The fruit-agent-orchestrate skill keys off these labels, and they are meant to
# be IDENTICAL across every project (a shared convention, not per-project config).
# Run this verbatim in any repo so the taxonomy stays in lockstep.
#
# SEMANTIC RULE (do not drift): `severity:*` is for DEFECTS ONLY (bugs) — it
# describes the impact of a defect. Features/enhancements get `enhancement` and
# NO severity (they rank below triaged bugs by design). Use `blocked` for real
# dependencies; never fake severity to express feature priority. See a project's
# RULES.md.
#
# Usage:
#   scripts/create-standard-labels.sh                 # current repo (gh default)
#   scripts/create-standard-labels.sh owner/name      # an explicit repo
#
# Idempotent: `gh label create --force` updates color/description if the label
# already exists, and never errors on a duplicate.
set -euo pipefail

REPO_ARG=()
if [[ "${1:-}" != "" ]]; then
  REPO_ARG=(-R "$1")
fi

# name|color(hex, no #)|description
LABELS=(
  "severity:high|b60205|Severe defect: data corruption, broken output, or blocking misbehaviour"
  "severity:medium|d93f0b|Real defect with visible impact, but not catastrophic"
  "severity:low|fbca04|Latent, cosmetic, or low-impact issue"
  "blocked|e11d48|Waiting on another issue"
  "proposal|D4E157|Proposed future feature, not yet scheduled"
  "wontfix|ffffff|This will not be worked on"
  "humans-only|bc749f|A task for humans only, not meant for AI agents"
  "decision|5319e7|Needs a human architectural/design decision before code work"
  "research|BFD4F2|Investigation or scoping ticket; produces a follow-up or closure"
  "bug|d73a4a|Something isn't working"
  "enhancement|a2eeef|New feature or request"
  "documentation|0075ca|Improvements or additions to documentation"
)

for entry in "${LABELS[@]}"; do
  IFS='|' read -r name color desc <<<"$entry"
  echo "  label: $name"
  gh label create "$name" --color "$color" --description "$desc" --force "${REPO_ARG[@]}"
done

echo "done — $(printf '%s\n' "${LABELS[@]}" | wc -l) labels ensured."
