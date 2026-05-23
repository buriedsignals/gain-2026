#!/bin/bash
# data-detective :: end-to-end pipeline runner
#
# Usage:
#   ./scripts/run_pipeline.sh --profile <profile.py> --data-root <corpus> --case <case_dir>
#
# Runs the full data-detective pipeline: ingest -> entity resolution -> FARA pull
# (if applicable) -> all anomaly detectors. Stops on first failure.
#
# Skip individual phases with:
#   --skip-ingest, --skip-resolve, --skip-fara, --skip-detectors

set -euo pipefail

PROFILE=""
DATA_ROOT=""
CASE_DIR=""
SKIP_INGEST=0
SKIP_RESOLVE=0
SKIP_FARA=0
SKIP_DETECTORS=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)        PROFILE="$2"; shift 2 ;;
    --data-root)      DATA_ROOT="$2"; shift 2 ;;
    --case)           CASE_DIR="$2"; shift 2 ;;
    --skip-ingest)    SKIP_INGEST=1; shift ;;
    --skip-resolve)   SKIP_RESOLVE=1; shift ;;
    --skip-fara)      SKIP_FARA=1; shift ;;
    --skip-detectors) SKIP_DETECTORS=1; shift ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# //; s/^#//'
      exit 0
      ;;
    *) echo "unknown flag: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$PROFILE" || -z "$DATA_ROOT" || -z "$CASE_DIR" ]]; then
  echo "Required: --profile, --data-root, --case" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$SCRIPT_DIR/skills"
DB="$CASE_DIR/index.duckdb"
mkdir -p "$CASE_DIR/anomalies" "$CASE_DIR/fara/cache"

echo "==> Pipeline: data-detective"
echo "    profile:   $PROFILE"
echo "    data-root: $DATA_ROOT"
echo "    case-dir:  $CASE_DIR"
echo "    db:        $DB"
echo

if [[ $SKIP_INGEST -eq 0 ]]; then
  echo "==> [1/4] Ingest"
  uv run "$SKILLS_DIR/ingest/scripts/ingest.py" \
    --profile "$PROFILE" \
    --data-root "$DATA_ROOT" \
    --db "$DB" \
    --manifest "$CASE_DIR/manifest.json"
  echo
fi

if [[ $SKIP_RESOLVE -eq 0 ]]; then
  echo "==> [2/4] Resolve entities"
  uv run "$SKILLS_DIR/resolve/scripts/resolve_entities.py" \
    --db "$DB" \
    --out "$CASE_DIR"
  echo
fi

if [[ $SKIP_FARA -eq 0 && -f "$SKILLS_DIR/external-data/scripts/fara.py" ]]; then
  echo "==> [3/4] Pull FARA + load"
  uv run "$SKILLS_DIR/external-data/scripts/fara.py" \
    --db "$DB" \
    --cache "$CASE_DIR/fara/cache"
  echo
fi

if [[ $SKIP_DETECTORS -eq 0 ]]; then
  echo "==> [4/4] Anomaly detectors"
  uv run "$SKILLS_DIR/detect/scripts/query.py" \
    --db "$DB" \
    --detector all \
    --out "$CASE_DIR/anomalies"
fi

echo
echo "==> Done."
echo "    Inspect:  $CASE_DIR/anomalies/*.csv"
echo "    Manifest: $CASE_DIR/manifest.json"
echo "    Cards:    uv run $SKILLS_DIR/evidence-cards/scripts/evidence_card.py --db $DB --source <kind> --id <id> --out $CASE_DIR/cards"
