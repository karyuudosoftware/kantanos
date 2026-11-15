# Runs as root in the test VM: installs the new clock script as an override of the image's
# service, and sets the clock to UTC like the installer does, ready for a restart.
install -m 0755 /tmp/local-clock /etc/kantan-local-clock
chcon -t bin_t /etc/kantan-local-clock 2>/dev/null
mkdir -p /etc/systemd/system/kantanos-local-clock.service.d
printf '[Service]\nExecStart=\nExecStart=/etc/kantan-local-clock\n' > /etc/systemd/system/kantanos-local-clock.service.d/test.conf
printf '0.0 0 0.0\n0\nUTC\n' > /etc/adjtime
rm -f /var/lib/kantanos/local-clock-set
systemctl daemon-reload
echo "prepared: $(tail -1 /etc/adjtime)"
