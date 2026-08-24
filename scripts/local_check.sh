#!/usr/bin/env bash
set -euo pipefail

rm -rf outputs
ruff check .
ruff format --check .
pytest
qfd-aviation-demo --output-dir outputs
python -m compileall -q src tests

echo
echo "LOCAL_CHECK=PASS"
echo "RETURN_CODE=0"
