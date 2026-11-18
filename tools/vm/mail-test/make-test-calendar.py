#!/usr/bin/env python3
"""A test calendar (like a published Outlook calendar) for Kan-chan's reminders in the VM:
output/vm/test-calendar.ics with an appointment in N minutes (default 62), one tomorrow and a
weekly one. Serve the kantanos folder with `python -m http.server 8765 --bind 127.0.0.1`; the
VM reads it as http://10.0.2.2:8765/output/vm/test-calendar.ics (needs
KANTAN_TEST_CALENDAR_HTTP=1, since real calendar links must be https).

  make-test-calendar.py [minutes]
"""
import datetime
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
mins = int(sys.argv[1]) if len(sys.argv) > 1 else 62
utc = datetime.timezone.utc
soon = (datetime.datetime.now(utc) + datetime.timedelta(minutes=mins)).replace(second=0, microsecond=0)
tomorrow = soon + datetime.timedelta(days=1)
fmt = lambda d: d.strftime("%Y%m%dT%H%M%SZ")  # noqa: E731
ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//KantanOS test//EN
X-WR-CALNAME:Mary's calendar
BEGIN:VEVENT
UID:test-doctor
SUMMARY:Doctor's appointment
LOCATION:Riverside Surgery
DTSTART:{fmt(soon)}
DTEND:{fmt(soon + datetime.timedelta(minutes=20))}
END:VEVENT
BEGIN:VEVENT
UID:test-hair
SUMMARY:Hairdresser
DTSTART:{fmt(tomorrow)}
DTEND:{fmt(tomorrow + datetime.timedelta(hours=1))}
END:VEVENT
BEGIN:VEVENT
UID:test-choir
SUMMARY:Choir practice
DTSTART:{fmt(soon - datetime.timedelta(days=14, hours=-3))}
DTEND:{fmt(soon - datetime.timedelta(days=14, hours=-4))}
RRULE:FREQ=WEEKLY
END:VEVENT
END:VCALENDAR
"""
path = os.path.join(ROOT, "output", "vm", "test-calendar.ics")
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w", newline="\r\n") as f:
    f.write(ics)
print("wrote", path, "doctor at", soon.astimezone().strftime("%H:%M"))
