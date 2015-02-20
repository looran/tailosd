# watchme - Displays system logs on screen using OSD

# Copyright (c) 2014 Laurent Ghigonis <laurent@gouloum.fr>
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

# TODO
# * move user configuration (colors, fonts, ...) to ~/.config/watchme/conf
# * click on text makes text disappear
# * longer timeout for higher severity
# * number of critical events displayed in system tray (timeout 5 min)

# OLD TODO
# * linewrap: display multiline entries
# * main process multitail: open (r) file then droppriv
# * ability to start as normal user, and not droppriv
# * subprocess defunct handling
# * quick terminal UI: npyscreen, interactive log scroll, actions

import sys
import os
import aosd
import logging
import multiprocessing
import setproctitle
import time
import traceback
import imp
import inspect
import pwd

import aosd_text_scroll
import utils

SEVERITY_UNINITIALIZED = -1
SEVERITY_INFO = 0
SEVERITY_LOW = 1
SEVERITY_MEDIUM = 2
SEVERITY_HIGH = 3
SEVERITY = {
    SEVERITY_UNINITIALIZED: "?",
    SEVERITY_INFO:   "INFO",
    SEVERITY_LOW:    "LOW ",
    SEVERITY_MEDIUM: "MED ",
    SEVERITY_HIGH:   "HIGH",
}
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

EXIT_JOIN_WAIT = 2

class Watchme_event(object):
    """ Event object, exchanged between processes
    For example, can be a new line in a monitored file """
    def __init__(self, severity, source, content, sysd_dct=None):
        utils.init_from_args(self)
        self.evt_id = time.time()

    def __str__(self):
        s = ""
        s += "Event %s\n" % self.evt_id
        s += "    Severity : %s\n" % SEVERITY[self.severity]
        s += "    Source   : %s\n" % self.source
        s += "    %s" % self.content
        return s

class Watchme_conf(object):
    def __init__(self, filters_enabled):
        utils.init_from_args(self)

class Watchme_user(multiprocessing.Process):
    """ Where the events are filtered, displayed on terminal and OSD
    Runs as normal user (from env SUDO_USER) """
    def __init__(self, logger, usergroup, conf, queue):
        """WARNING: this function runs as root"""
        super(Watchme_user, self).__init__()
        utils.init_from_args(self)

    def run(self):
        title = setproctitle.getproctitle()
        setproctitle.setproctitle(title + " filter")
        utils.droppriv(int(self.usergroup[0]), int(self.usergroup[1]))
        self.logger.info("after droppriv")
        self._init_filters()
        self._init_term()
        self._init_osd()

        while True:
            evt = self.queue.get()
            evt = self._filter(evt)
            self._print(evt)

    def _filter(self, evt):
        for f in self.filters:
            try:
                severity = self._filter_severity(evt, f)
                if severity is not None:
                    evt.severity = severity
                if 'filter' in dir(f):
                    evt = f.filter(evt)
                    if not evt:
                        return None # drop event
            except Exception, e:
                print e
                self.logger.warn(traceback.print_exc())
                evt_expt=Watchme_event(SEVERITY_HIGH, "Watchme", "Watchme EXCEPTION: filter %s failed to handle the following event:" % f)
                self._print(evt_expt)
                self._print(evt)
                continue
        return evt

    def _filter_severity(self, evt, filter_obj):
        for severity_str in [ "SEVERITY_HIGH", "SEVERITY_MEDIUM", "SEVERITY_LOW", "SEVERITY_INFO" ]:
            severity = globals()[severity_str]
            if severity_str in dir(filter_obj):
                for it in filter_obj.__getattribute__(severity_str):
                    if type(it) is list:
                        el1 = it[0]
                        el2 = it[1]
                        if type(el2) is list:
                            if el1 in evt.content and any(x in evt.content for x in el2):
                                return severity
                        else:
                            if el1 in evt.content and el2 in evt.content:
                                return severity
                    elif it in evt.content:
                                return severity
        return None

    def _print(self, evt):
        self._print_term(evt)
        if evt.severity == SEVERITY_LOW and os.environ.get('WATCHME_CONF_NOPRINTOSD_SEVERITY_LOW'):
            return
        self._print_osd(evt)

    def _print_term(self, evt):
        print "%s %s %s" % (SEVERITY[evt.severity], evt.source, evt.content)

    def _print_osd(self, evt):
        txt = "%s" % (evt.content)
        color = SEVERITY_COLORS[evt.severity]
        timeout = SEVERITY_TIMEOUT[evt.severity]
        self.osd.append(txt, color, timeout=timeout)

    def _init_filters(self):
        self.filters = list()
        for p in [os.path.dirname(__file__) + '/filters.py',
                  os.path.expanduser("~%s" % pwd.getpwuid(int(self.usergroup[0]))[0]) + '/.watchme/filters.py']:
            try:
                m = imp.load_source("filters", p)
                for name, class_ref in inspect.getmembers(m, inspect.isclass):
                    if name[:15] not in self.conf.filters_enabled:
                        continue
                    try:
                        class_obj = class_ref()
                        self.filters.append(class_obj)
                        self.logger.info("Initialised filter %s (file %s)" % (name, p))
                    except Exception, e:
                        self.logger.warn(traceback.print_exc())
                        self.logger.info("Could not initialise filter %s (file %s)" % (name, p))
            except Exception, e:
                self.logger.warn(traceback.print_exc())
                self.logger.warn("could not load filter file %s" % p)

    def _init_term(self):
        pass

    def _init_osd(self):
        self.osd = aosd_text_scroll.Aosd_text_scroll_thread()
        self.osd.start()

class Watchme(object):
    """ Where the log tail happpends
    Runs as root """
    def __init__(self, loglevel=logging.DEBUG):
        utils.init_from_args(self)
        if os.getuid() != 0:
            raise Exception("Must be root")
        if 'SUDO_USER' not in os.environ:
            raise Exception("Cannot get SUDO_USER. You must use sudo from a normal user.")
        self.user = os.environ.get('SUDO_UID')
        self.group = os.environ.get('SUDO_GID')
        self._conf_init()
        self._logger_init()
        self._user_process_init()
        self.logger.info("Watchme init ok")

    def _mode_multitail(self):
        import multitail
        for fn, line in multitail.multitail(['/var/log/everything/current']):
            evt = Watchme_event(SEVERITY_UNINITIALIZED, fn, line[16:])
            #self.logger.info("EVENT : %s %s %s" % (evt.severity, evt.source, evt.content))
            self.user_q.put_nowait(evt)

    def _mode_systemd(self):
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
                evt = Watchme_event(
                    SEVERITY_UNINITIALIZED,
                    entry['SYSLOG_IDENTIFIER'].encode('ascii', 'ignore'),
                    entry['MESSAGE'].encode('ascii', 'ignore'),
                    sysd_dct=entry
                )
                self.user_q.put_nowait(evt)
            except Exception, e:
                self.logger.warn(e)
                self.logger.warn(traceback.print_exc())

    def run(self, args):
        self.logger.info("Watchme started")
        self.user_q.put_nowait(Watchme_event(SEVERITY_INFO, "Watchme", "Watchme started"))

        if args.systemd:
            self._mode_systemd()
        else:
            self._mode_multitail()

        self.logger.info("Watchme exiting, waiting for user process for %d seconds" % EXIT_JOIN_WAIT)
        if self.user_p.is_alive():
            self.user_p.join(timeout=EXIT_JOIN_WAIT)
            if self.user_p.is_alive():
                self.logger.info("exit: user process still alive after %d seconds, terminating" % (EXIT_JOIN_WAIT))
                self.user_p.kill()
        else:
            self.logger.info("exit: user process already dead when exiting !")
        self.logger.info("Watchme exiting ok")

    def _conf_init(self):
        self.conf = Watchme_conf(filters_enabled=['Watchme_filter_'])

    def _logger_init(self):
        self.logger = multiprocessing.log_to_stderr() # XXX implement process-safe logger
        self.logger.setLevel(self.loglevel)

    def _user_process_init(self):
        self.user_q = multiprocessing.Queue()
        self.user_p = Watchme_user(self.logger, (self.user, self.group), self.conf, self.user_q)
        self.user_p.start()
