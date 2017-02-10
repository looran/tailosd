# tailosd - OSD file tailer

# Copyright (c) 2014,2016 Laurent Ghigonis <laurent@gouloum.fr>
# Copyright (c) 2014,2015 Pierre-Olivier Vauboin <povauboin@gmail.com>

# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

# OLD TODO
# * move user configuration (colors, fonts, ...) to ~/.config/watchme/conf
# * click on text makes text disappear
# * longer timeout for higher severity
# * number of critical events displayed in system tray (timeout 5 min)

# OLD OLD TODO
# * linewrap: display multiline entries
# * main process multitail: open (r) file then droppriv
# * ability to start as normal user, and not droppriv
# * subprocess defunct handling
# * quick terminal UI: npyscreen, interactive log scroll, actions

import sys
import os
import aosd
import time
import traceback
import collections
import shlex

import aosd_text_scroll

SEVERITY_UNINITIALIZED = -1
SEVERITY_INFO = 0
SEVERITY_LOW = 1
SEVERITY_MEDIUM = 2
SEVERITY_HIGH = 3
SEVERITY = {
    SEVERITY_UNINITIALIZED: "",
    SEVERITY_INFO:   "INFO ",
    SEVERITY_LOW:    "LOW  ",
    SEVERITY_MEDIUM: "MED  ",
    SEVERITY_HIGH:   "HIGH ",
}
SEVERITY_CHOICES = collections.OrderedDict([("info", 0), ("low", 1), ("medium", 2), ("high", 3)])
SEVERITY_DEFAULT = "info"
SEVERITY_COLORS = {
    SEVERITY_UNINITIALIZED: "white",
    SEVERITY_INFO:   "green",
    SEVERITY_LOW:    "blue",
    SEVERITY_MEDIUM: "orange",
    SEVERITY_HIGH:   "red",
}
SEVERITY_TIMEOUT = {
    SEVERITY_UNINITIALIZED: 6,
    SEVERITY_INFO:   6,
    SEVERITY_LOW:    7,
    SEVERITY_MEDIUM: 9,
    SEVERITY_HIGH:   12,
}

FILTER_ACTION = 0
FILTER_SOURCE = 1
FILTER_OPT = 2

class Tailosd(object):
    def __init__(self, targets, filters_file, loglevel):
        self.targets = targets
	self.filters_file = filters_file
        self.loglevel = loglevel
        self.osd = aosd_text_scroll.Aosd_text_scroll_thread()
        self.osd.start()
	self.reload_filters()

    def run(self):
        if "systemd" in self.targets:
            self._run_systemd()
        else:
            self._run_multitail()

    def reload_filters(self):
        self.filters = list()
        if self.filters_file is None:
	    self._print(SEVERITY_INFO, "tailosd: no filters loaded")
            return
        with open(self.filters_file) as ffile:
            for nline, line in enumerate(ffile):
                if line == "\n" or line.startswith('#'): continue
                filt = shlex.split(line)
                if len(filt) != 3:
                    self._print(SEVERITY_HIGH, "tailosd: filter invalid: [line %d] %s" % (nline+1, line.rstrip()))
                    continue
                self.filters.append(filt)
	self._print(SEVERITY_INFO, "tailosd: filters loaded (%d)" % len(self.filters))

    def _run_multitail(self):
        import multitail
        for fn, line in multitail.multitail(self.targets["files"]):
            severity, msg = self._filter(fn, line.rstrip())
            self._print(severity, msg)

    def _run_systemd(self):
        import select
        import systemd.journal
        journal = systemd.journal.Reader()
        journal.seek_tail()
        journal.get_previous() # See https://bugs.freedesktop.org/show_bug.cgi?id=64614
        poll = select.poll()
        poll.register(journal.fileno(), journal.get_events())
        while True:
            poll.poll()
            entry = journal.get_next()
            if not entry:
                journal.process() # This is necessary to reset fd readable state
                continue
            try:
                severity, msg = self._filter(entry['SYSLOG_IDENTIFIER'].encode('ascii', 'ignore'), entry['MESSAGE'].encode('ascii', 'ignore'))
                self._print(severity, msg)
            except Exception, e:
                print(e)
                print(traceback.print_exc())

    def _print(self, severity, msg):
        print "%s%s" % (SEVERITY[severity], msg)
        if severity < self.loglevel:
            return
        color = SEVERITY_COLORS[severity]
        timeout = SEVERITY_TIMEOUT[severity]
        self.osd.append(msg, color, timeout=timeout)

    def _filter(self, source, message):
        severity = SEVERITY_UNINITIALIZED
	for f in self.filters:
            if f[FILTER_SOURCE] == "*" or source == f[FILTER_SOURCE]:
                if f[FILTER_ACTION] == "drop-line-start":
                    message = message[int(f[FILTER_OPT]):]
                elif severity == SEVERITY_UNINITIALIZED and f[FILTER_ACTION] in SEVERITY_CHOICES:
		    if f[FILTER_OPT] in message:
			severity = SEVERITY_CHOICES[f[FILTER_ACTION]]
        return severity, message

    def _NOTUSED_led_blink(self):
        with open("/sys/devices/platform/thinkpad_acpi/leds/tpacpi::power/brightness", 'w') as f: f.write("0")
        time.sleep(0.1)
        with open("/sys/devices/platform/thinkpad_acpi/leds/tpacpi::power/brightness", 'w') as f: f.write("1")

