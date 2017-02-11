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

CONF_ACTION = 0
CONF_SOURCE = 1
CONF_OPT = 2

SEVERITY_DROP = -2
SEVERITY_INFO = -1
SEVERITY_LOW = 0
SEVERITY_UNKNOWN = 1
SEVERITY_MEDIUM = 2
SEVERITY_HIGH = 3
SEVERITY_CHOICES = collections.OrderedDict([("info", SEVERITY_INFO), ("low", SEVERITY_LOW), ("unknown", SEVERITY_UNKNOWN), ("medium", SEVERITY_MEDIUM), ("high", SEVERITY_HIGH)])
SEVERITY_DEFAULT = "info"
SEVERITY_DEFAULT_VALUES = {
	SEVERITY_HIGH: {"color": "red", "timeout": 12},
	SEVERITY_MEDIUM: {"color": "orange", "timeout":9},
	SEVERITY_UNKNOWN: {"color": "white", "timeout": 6},
	SEVERITY_LOW: {"color": "blue", "timeout":7},
	SEVERITY_INFO: {"color": "green", "timeout":6},
}
SEVERITY_PRINT = { SEVERITY_DROP: "DROP ", SEVERITY_INFO:   "INFO ", SEVERITY_LOW:    "LOW  ", SEVERITY_UNKNOWN: "UNKN ", SEVERITY_MEDIUM: "MED  ", SEVERITY_HIGH:   "HIGH " }

class Tailosd(object):
    def __init__(self, targets, conf_file, loglevel, debug=False):
        self.targets = targets
	self.conf_file = conf_file
        self.loglevel = loglevel
        if debug:
            print("loglevel: %d" % loglevel)
	self.debug = debug
        self.osd = aosd_text_scroll.Aosd_text_scroll_thread()
        self.osd.start()
	self.reload_conf()

    def run(self):
        if "systemd" in self.targets:
            self._run_systemd()
        else:
            self._run_multitail()

    def reload_conf(self):
        # self.conf["filters"] = list((sevnum, source, match))
        # self.conf[source]["drop-line-start"] = list((sevnum, match))
        # self.conf[source][sevnum]["color"] = "colorname"
        # self.conf[source][sevnum]["timeout"] = toval
        self.conf = { "filters": list() }
	self.conf["*"] = SEVERITY_DEFAULT_VALUES
        if self.conf_file is None:
	    self._print(SEVERITY_INFO, "tailosd: no configuration loaded")
            return
        nitem = 0
        with open(self.conf_file) as ffile:
            for nline, line in enumerate(ffile):
                if line == "\n" or line.startswith('#'): continue
                e = shlex.split(line)
                if len(e) != 3:
                    self._print(SEVERITY_HIGH, "tailosd: configuration line %d invalid: %s" % (nline+1, line.rstrip()))
                    continue
                if e[CONF_SOURCE] not in self.conf: self.conf[e[CONF_SOURCE]] = dict()
                if e[CONF_ACTION] in SEVERITY_CHOICES or e[CONF_ACTION] == "drop":
                    self.conf["filters"].append((e[CONF_ACTION], e[CONF_SOURCE], e[CONF_OPT]))
                elif e[CONF_ACTION] == "drop-line-start":
                    self.conf[e[CONF_SOURCE]]["drop-line-start"] = e[CONF_OPT]
                else:
                    sev, attr = e[CONF_ACTION].split("-")
                    if sev not in self.conf[e[CONF_SOURCE]]: self.conf[e[CONF_SOURCE]][sev] = dict()
                    self.conf[e[CONF_SOURCE]][sev][attr] = e[CONF_OPT]
                nitem += 1
        if self.debug:
            print("conf: %s" % self.conf)
	self._print(SEVERITY_INFO, "tailosd: conf loaded (%d items)" % nitem)

    def _run_multitail(self):
        import multitail
        for fn, line in multitail.multitail(self.targets["files"]):
            severity, msg = self._filter(fn, line.rstrip())
            self._print(severity, msg, fn)

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

    def _filter(self, source, message):
        severity = SEVERITY_UNKNOWN
        if source not in self.conf:
            source = "*"
        if "drop-line-start" in self.conf[source]:
	    message = message[int(self.conf[source]["drop-line-start"]):]
	for f in self.conf["filters"]:
            if f[CONF_SOURCE] == "*" or source == f[CONF_SOURCE]:
                if f[CONF_OPT] in message:
                    if f[CONF_ACTION] == "drop":
                        severity = SEVERITY_DROP
                    elif f[CONF_ACTION] in SEVERITY_CHOICES:
                        severity = SEVERITY_CHOICES[f[CONF_ACTION]]
        return severity, message

    def _print(self, severity, msg, source="*"):
        print "%s %s%s" % (time.strftime("%Y%m%d_%H%M"), SEVERITY_PRINT[severity], msg)
        if severity < self.loglevel:
            return
        if source not in self.conf or severity not in self.conf[source] or "color" not in self.conf[source][severity]:
            source = "*"
        color = self.conf[source][severity]["color"]
        timeout = self.conf[source][severity]["timeout"]
        self.osd.append(msg, color, timeout=timeout)

