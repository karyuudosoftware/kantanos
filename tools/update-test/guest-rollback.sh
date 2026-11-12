# Runs inside the test VM: undo the last update (what "ujust kantan-undo-update" does).
bootc rollback 2>&1 | tail -3
