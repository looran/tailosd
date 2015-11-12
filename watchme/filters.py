import re

import watchme

class Watchme_filter_default_syslog(object):
    SEVERITY_HIGH = [
        ["[sudo]", ["incorrect password", "pam_unix(sudo:auth)"]],
        "Kernel panic",
        "Hardware Error",
        "segfault",
        "grsec",
        "Out of memory",
        "Killed process",
        "Malformed Packet"
    ]
    SEVERITY_MEDIUM = [
        ["[sudo]", "session opened"],
        "New USB device found",
        "USB disconnect",
        "adding default route",
        "authenticated",
        "authenticated", "associated", "carrier acquired", "deauthenticating from", "carrier lost",
    ]
    SEVERITY_LOW = [
        ["[sudo]", "session opened"],
    ]

class Watchme_filter_default_syslog_iptables(object):
    def __init__(self, debug=False):
        self.debug = debug

    def filter(self, evt):
        if "iptables-drop:" in evt.content:
            if self.debug: print "Watchme_filter_default_syslog_iptables: action drop"
            action="drop"
        elif "iptables-accept:" in evt.content:
            if self.debug: print "Watchme_filter_default_syslog_iptables: action accept"
            action="accept"
        else:
            return evt # not for us

        # Content rewording
        m_ip = re.match(r".* iptables-(?P<action>[a-z]*): IN=(?P<iface_in>\w*) OUT=(?P<iface_out>\w*) MAC=(?P<mac>[0-9a-f:]*) SRC=(?P<ip_src>[0-9\.]*) DST=(?P<ip_dst>[0-9\.]*) LEN=(?P<len>[0-9]*) TOS=(?P<tos>[0-9a-zx]*) PREC=(?P<prec>[0-9a-zA-Zx]*) TTL=(?P<ttl>[0-9]*) ID=(?P<id>[0-9]*).* PROTO=(?P<proto>[0-9A-Z]*)", evt.content)
        if m_ip:
            if self.debug: print "Watchme_filter_default_syslog_iptables: m_ip"
            d_ip = m_ip.groupdict()
            mac_src = d_ip['mac'][18:35]
            mac_dst = d_ip['mac'][:17]
            d_ip['mac'] = "%s > %s" % (mac_src, mac_dst)
            if d_ip['proto'] == "TCP":
                if self.debug: print "Watchme_filter_default_syslog_iptables: TCP"
                m_tcp = re.match(r".* SPT=(?P<port_src>[0-9]*) DPT=(?P<port_dst>[0-9]*) WINDOW=(?P<win>[0-9]*) RES=(?P<res>[0-9a-zx]*) (?P<flags>.*) URGP=(?P<urgp>[0-9]*)", evt.content)
                if m_tcp:
                    d = m_tcp.groupdict()
                    evt.content = "%s: %s %s %s:%s > %s:%s %s [%s] %s" % (
                        action, d_ip['iface_in'], d_ip['mac'], d_ip['ip_src'], d['port_src'], d_ip['ip_dst'], d['port_dst'], d['flags'], d_ip['len'], d_ip['ttl'])
            elif d_ip['proto'] == "UDP":
                if self.debug: print "Watchme_filter_default_syslog_iptables: UDP"
                m_udp = re.match(r".* SPT=(?P<port_src>[0-9]*) DPT=(?P<port_dst>[0-9]*) LEN=(?P<len>[0-9]*)", evt.content)
                if m_udp:
                    d = m_udp.groupdict()
                    evt.content = "%s: %s %s %s:%s > %s:%s UDP [%s] %s" % (
                        action, d_ip['iface_in'], d_ip['mac'], d_ip['ip_src'], d['port_src'], d_ip['ip_dst'], d['port_dst'], d_ip['len'], d_ip['ttl'])
            elif d_ip['proto'] == "ICMP":
                if self.debug: print "Watchme_filter_default_syslog_iptables: ICMP"
                m_icmp = re.match(r".* TYPE=(?P<type>[0-9]*) CODE=(?P<code>[0-9]*) ID=(?P<id>[0-9]*) SEQ=(?P<seq>[0-9]*)", evt.content)
                if m_icmp:
                    d = m_icmp.groupdict()
                    evt.content = "%s: %s %s %s > %s ICMP %s-%s [%s] %s" % (
                        action, d_ip['iface_in'], d_ip['mac'], d_ip['ip_src'], d_ip['ip_dst'], d['type'], d['code'], d_ip['len'], d_ip['ttl'])
            else:
                if self.debug: print "Watchme_filter_default_syslog_iptables: Unknown proto"
                evt.content = "%s: %s %s %s > %s %s [%s] %s" % (
                    action, d_ip['iface_in'], d_ip['mac'], d_ip['ip_src'], d_ip['ip_dst'], d_ip['proto'], d_ip['len'], d_ip['ttl'])

        # Severity
        if action == "drop":
            if m_ip:
                if mac_dst == "ff:ff:ff:ff:ff:ff": evt.severity = watchme.SEVERITY_LOW
                elif d_ip['ip_dst'].endswith("255"): evt.severity = watchme.SEVERITY_LOW
                elif d_ip['ip_dst'].startswith("224.0.0"): evt.severity = watchme.SEVERITY_LOW
            if evt.severity == watchme.SEVERITY_UNINITIALIZED:
                evt.severity = watchme.SEVERITY_HIGH
        elif action == "accept":
            evt.severity = watchme.SEVERITY_INFO

        return evt

class Watchme_filter_default_arpwatch(object):
    def filter(self, evt):
        # Severity
        if not "[arpwatch]" in evt.content:
            return evt # not for us
        if any(x in evt.content for x in ["Wrote pid", "Running as", "listening on"]):
            return evt # not interesting
        if "new station" in evt.content:
            evt.severity = watchme.SEVERITY_MEDIUM
        else:
            evt.severity = watchme.SEVERITY_HIGH

        return evt

class Watchme_filter_default_systemd(object):
    def filter(self, evt):
        if not evt.sysd_dct:
            return evt # not for us

        # By default use PRIORITY field from systemd to set OSD severity color
        if 'PRIORITY' in evt.sysd_dct:
            if evt.sysd_dct['PRIORITY'] < 4:
                evt.severity = watchme.SEVERITY_HIGH
            elif evt.sysd_dct['PRIORITY'] < 5:
                evt.severity = watchme.SEVERITY_MEDIUM
            elif evt.sysd_dct['PRIORITY'] < 6:
                evt.severity = watchme.SEVERITY_LOW
            else:
                evt.severity = watchme.SEVERITY_INFO

        # Some services have dedicated priorities
        if '_SYSTEMD_UNIT' in evt.sysd_dct:
            if 'dhcpcd@' in evt.sysd_dct['_SYSTEMD_UNIT']:
                evt.severity = watchme.SEVERITY_MEDIUM

        return evt
