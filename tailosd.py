# tailosd - Tail files with On Screen Display output

# Copyright (c) 2014,2016 Laurent Ghigonis <laurent@gouloum.fr>
# Copyright (c) 2014,2015 Pierre-Olivier Vauboin <povauboin@gmail.com>

import sys
import os
import aosd
import time
import traceback
import collections
import shlex
import copy

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
	SEVERITY_LOW: {"color": "green", "timeout":6},
	SEVERITY_INFO: {"color": "blue", "timeout":6},
}
SEVERITY_PRINT = { SEVERITY_DROP: "DROP ", SEVERITY_INFO:   "INFO ", SEVERITY_LOW:    "LOW  ", SEVERITY_UNKNOWN: "UNKN ", SEVERITY_MEDIUM: "MED  ", SEVERITY_HIGH:   "HIGH " }
SEVERITY_PAUSE_BUFFER_DEFAULT = SEVERITY_MEDIUM

class Tailosd(object):
    def __init__(self, targets, conf_file, loglevel, debug=False):
        self.targets = targets
	self.conf_file = conf_file
        self.loglevel = loglevel
        if debug:
            print("loglevel: %d" % loglevel)
	self.debug = debug
        self.paused = False
        self.buffer = list()
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
        # self.conf[source]["cut-line-start"] = list((sevnum, match))
        # self.conf[source]["pause-buffer-severity"] = sevnum
        # self.conf[source][sevnum]["color"] = "colorname"
        # self.conf[source][sevnum]["timeout"] = timeoutvalue
        self.conf = { "filters": list() }
	self.conf["*"] = copy.deepcopy(SEVERITY_DEFAULT_VALUES)
        if self.conf_file is None:
	    self._print(SEVERITY_INFO, "tailosd: no configuration loaded")
            return
        nitem = 0
        with open(self.conf_file) as ffile:
            for nline, line in enumerate(ffile):
                if self.debug: print(line)
                if line == "\n" or line.startswith('#'): continue
                try:
                    e = shlex.split(line)
                    if len(e) < 3: raise Exception()
                    if e[CONF_SOURCE] not in self.conf: self.conf[e[CONF_SOURCE]] = dict()
                    if e[CONF_ACTION] in SEVERITY_CHOICES or e[CONF_ACTION] == "drop":
                        self.conf["filters"].append((e[CONF_ACTION], e[CONF_SOURCE], e[CONF_OPT]))
                    elif e[CONF_ACTION] == "cut-line-start":
                        self.conf[e[CONF_SOURCE]]["cut-line-start"] = int(e[CONF_OPT])
                    elif e[CONF_ACTION] == "pause-buffer-severity":
                        self.conf[e[CONF_SOURCE]]["pause-buffer-severity"] = SEVERITY_CHOICES[e[CONF_OPT]]
                    else:
                        sev, attr = e[CONF_ACTION].split("-")
                        sev = SEVERITY_CHOICES[sev]
                        if sev not in self.conf[e[CONF_SOURCE]]: self.conf[e[CONF_SOURCE]][sev] = dict()
                        self.conf[e[CONF_SOURCE]][sev][attr] = e[CONF_OPT]
                except:
                    self._print(SEVERITY_HIGH, "tailosd: configuration line %d invalid: %s" % (nline+1, line.rstrip()))
                    continue
                nitem += 1
        if self.debug:
            print("conf: %s" % self.conf)
	self._print(SEVERITY_INFO, "tailosd: conf loaded (%d items)" % nitem)

    def pause(self):
        if self.paused is True:
            return
        self._print(SEVERITY_INFO, "tailosd: pausing")
        self.paused = True

    def resume(self):
        if self.paused is False:
            return
        self.paused = False
        for l in self.buffer:
            self.osd.append(l[0], l[1], l[2])
        self._print(SEVERITY_INFO, "tailosd: resumed, %d events where buffered" % len(self.buffer))
        self.buffer = list()

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
                severity, msg = self._filter(entry['SYSLOG_IDENTIFIER'].encode('ascii', 'ignore'), entry['MESSAGE'].encode('ascii', 'ignore'), entry)
                self._print(severity, msg)
            except Exception, e:
                print(e)
                print(traceback.print_exc())

    def _filter(self, source, message, data=None):
        severity = SEVERITY_UNKNOWN
        if source not in self.conf:
            source = "*"
        cutstart = self._conf_get(source, "cut-line-start")
        if cutstart is not None:
	    message = message[cutstart:]
	for f in self.conf["filters"]:
            if f[CONF_SOURCE] == "*" or source == f[CONF_SOURCE]:
                if f[CONF_OPT] in message:
                    if f[CONF_ACTION] == "drop":
                        severity = SEVERITY_DROP
                    elif f[CONF_ACTION] in SEVERITY_CHOICES:
                        severity = SEVERITY_CHOICES[f[CONF_ACTION]]
        if severity == SEVERITY_UNKNOWN and source == "systemd" and data is not None:
            self._filter_systemd(source, message, data)
        return severity, message

    def _filter_systemd(self, source, message, sysd_dct):
	import warnings
	warnings.warn("XXX systemd ported from watchme without testing, needs testing !!!")
	warnings.warn("XXX the best would probably be some configuration file syntax for systemd instead of this code.")
        if not evt.sysd_dct:
            return evt # not for us
        # By default use PRIORITY field from systemd to set OSD severity color
        if 'PRIORITY' in sysd_dct:
            if sysd_dct['PRIORITY'] < 4:
                severity = SEVERITY_HIGH
            elif sysd_dct['PRIORITY'] < 5:
                severity = SEVERITY_MEDIUM
            elif sysd_dct['PRIORITY'] < 6:
                severity = SEVERITY_LOW
            else:
                severity = SEVERITY_INFO
        # Some services have dedicated priorities
        if '_SYSTEMD_UNIT' in sysd_dct:
            if 'dhcpcd@' in sysd_dct['_SYSTEMD_UNIT']:
                severity = SEVERITY_MEDIUM
        return evt

    def _print(self, severity, msg, source="*"):
        print "%s %s%s" % (time.strftime("%Y%m%d_%H%M"), SEVERITY_PRINT[severity], msg)
        if severity < self.loglevel:
            return
        if source not in self.conf or severity not in self.conf[source] or "color" not in self.conf[source][severity]:
            source = "*"
        color = self.conf[source][severity]["color"]
        timeout = self.conf[source][severity]["timeout"]
        if self.paused:
            if severity >= self._conf_get(source, "pause-buffer-severity", SEVERITY_PAUSE_BUFFER_DEFAULT):
                self.buffer.append((msg, color, timeout))
        else:
            self.osd.append(msg, color, timeout)

    def _conf_get(self, source, action, defaultval=None):
        val = None
        if source not in self.conf and source != '*':
            source = '*'
        if source in self.conf and action in self.conf[source]:
            return self.conf[source][action]
        return defaultval

