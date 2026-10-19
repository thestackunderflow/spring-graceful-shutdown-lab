#!/usr/bin/env bash
# Runs the JUnit tests in Docker (Maven + JDK 21), then the evidence tests. Maven's downloads are cached in a named volume.
# Usage: bash tests/run-tests.sh [log-file]
set -uo pipefail
cd "$(dirname "$0")/.."
LOG="${1:-tests/out/test-run.log}"
mkdir -p "$(dirname "$LOG")"
MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd -W 2>/dev/null || pwd):/lab" -v spring-graceful-m2:/root/.m2 -w /lab \
  maven:3.9-eclipse-temurin-21 mvn -q -B test 2>&1 | tail -30 | tee "$LOG"
grep -ho 'tests="[0-9]*" errors="[0-9]*" skipped="[0-9]*" failures="[0-9]*"' target/surefire-reports/TEST-*.xml 2>/dev/null \
  | sed 's/^/JUnit summary: /' | tee -a "$LOG"
python -m unittest discover -s tests -p "test_evidence.py" 2>&1 | tail -3 | tee -a "$LOG"
python -W ignore -m unittest discover -s tests -p "test_primer_panels.py" 2>&1 | tail -3 | tee -a "$LOG"
