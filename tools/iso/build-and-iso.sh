#!/bin/bash
# Rebuild the image, run the static checks, then build the installer ISO.
set -uo pipefail
T=/mnt/d/CLAUDE_Projects/kantanos/tools
bash $T/build-image.sh > /root/build.log 2>&1 || { echo BUILD FAILED; tail -30 /root/build.log; exit 1; }
grep -A6 "dnf5 repolist" /root/build.log | tail -6
bash $T/verify-image.sh | grep -E "FAIL" ; echo "verify finished (FAIL lines above, if any)"
bash $T/iso/make-iso.sh
