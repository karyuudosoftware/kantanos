#!/bin/bash
# Publishes the already-built image to the test registry with a signature (no rebuild).
T="$(cd "$(dirname "$0")/.." && pwd)"
. "$T/update-test/env.sh"
bash "$T/publish.sh" 2>&1 | grep -E "^==|Published|rror"
curl -s http://10.0.2.2:5005/v2/kantanos/tags/list; echo
