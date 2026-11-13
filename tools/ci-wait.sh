#!/bin/bash
# Waits for the newest GitHub build of KantanOS to finish, then prints each step's result.
REPO=karyuudosoftware/kantanos
API=https://api.github.com/repos/$REPO
RUN=$(curl -s "$API/actions/runs?per_page=1" | python -c "import json,sys; print(json.load(sys.stdin)['workflow_runs'][0]['id'])")
echo "run $RUN  https://github.com/$REPO/actions/runs/$RUN"
for i in $(seq 1 60); do
    S=$(curl -s "$API/actions/runs/$RUN" | python -c "import json,sys; d=json.load(sys.stdin); print(d.get('status'), d.get('conclusion'))")
    case "$S" in completed*) break;; esac
    sleep 100
done
echo "result: $S"
curl -s "$API/actions/runs/$RUN/jobs" | python -c "
import json,sys
for j in json.load(sys.stdin)['jobs']:
    for s in j['steps']: print(' ', s['conclusion'] or s['status'], '-', s['name'], s.get('started_at','')[11:19], s.get('completed_at','')[11:19] if s.get('completed_at') else '')"
