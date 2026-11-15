# Runs as root in the test VM: makes it look like a system the installer set to a UTC
# hardware clock, so the next boot shows whether kantanos-local-clock switches it back.
printf '0.0 0 0.0\n0\nUTC\n' > /etc/adjtime
rm -f /var/lib/kantanos/local-clock-set
echo "before restart:"; timedatectl show -p LocalRTC; date
