# Runs as root in the test VM after a restart: did the one-time clock switch run?
systemctl status kantanos-local-clock.service --no-pager 2>&1 | sed -n 1,4p
tail -1 /etc/adjtime; ls /var/lib/kantanos/local-clock-set
timedatectl show -p LocalRTC -p Timezone; date
