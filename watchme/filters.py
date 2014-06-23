import re

import watchme

class Watchme_filter_default_syslog(object):
    def __init__(self):
        pass

    def filter(self, evt):
        if evt.content.find("[sudo]") >= 0:
            evt.severity = watchme.SEVERITY_LOW
        return evt

class Watchme_filter_default_syslog_iptables(object):
    def __init__(self):
        pass

    def filter(self, evt):
        if evt.content.find("iptables-drop:") < 0 and evt.content.find("iptables-accept:") < 0:
            return evt # not for us

        if evt.content.find("iptables-drop:") >= 0:
            evt.severity = watchme.SEVERITY_HIGH
        elif evt.content.find("iptables-accept:") >= 0:
            evt.severity = watchme.SEVERITY_INFO

        m_ip = re.match(r".* iptables-(?P<action>[a-z]*): IN=(?P<iface_in>\w*) OUT=(?P<iface_out>\w*) MAC=(?P<mac>[0-9a-f:]*) SRC=(?P<ip_src>[0-9\.]*) DST=(?P<ip_dst>[0-9\.]*) LEN=(?P<len>[0-9]*) TOS=(?P<tos>[0-9a-zx]*) PREC=(?P<prec>[0-9a-zx]*) TTL=(?P<ttl>[0-9]*) ID=(?P<id>[0-9]*) .* PROTO=(?P<proto>[0-9A-Z]*)", evt.content)
        if m_ip:
            d_ip = m_ip.groupdict()
            d_ip['mac'] = "%s > %s" % (d_ip['mac'][18:35], d_ip['mac'][:17])
            if d_ip['proto'] == "TCP":
                m_tcp = re.match(r".* SPT=(?P<port_src>[0-9]*) DPT=(?P<port_dst>[0-9]*) WINDOW=(?P<win>[0-9]*) RES=(?P<res>[0-9a-zx]*) (?P<flags>[A-Z]*) URGP=(?P<urgp>[0-9]*)", evt.content)
                if m_tcp:
                    d = m_tcp.groupdict()
                    evt.content = "%s: %s %s %s:%s > %s:%s %s [%s] %s" % (
                        d_ip['action'], d_ip['iface_in'], d_ip['mac'], d_ip['ip_src'], d['port_src'], d_ip['ip_dst'], d['port_dst'], d['flags'], d_ip['len'], d_ip['ttl'])
            elif d_ip['proto'] == "UDP":
                m_udp = re.match(r".* SPT=(?P<port_src>[0-9]*) DPT=(?P<port_dst>[0-9]*) LEN=(?P<len>[0-9]*)", evt.content)
                if m_udp:
                    d = m_udp.groupdict()
                    evt.content = "%s: %s %s %s:%s > %s:%s UDP [%s] %s" % (
                        d_ip['action'], d_ip['iface_in'], d_ip['mac'], d_ip['ip_src'], d['port_src'], d_ip['ip_dst'], d['port_dst'], d_ip['len'], d_ip['ttl'])
            elif d_ip['proto'] == "ICMP":
                m_icmp = re.match(r".* TYPE=(?P<type>[0-9]*) CODE=(?P<code>[0-9]*) ID=(?P<id>[0-9]*) SEQ=(?P<seq>[0-9]*)", evt.content)
                if m_icmp:
                    d = m_icmp.groupdict()
                    evt.content = "%s: %s %s %s > %s ICMP %s-%s [%s] %s" % (
                        d_ip['action'], d_ip['iface_in'], d_ip['mac'], d_ip['ip_src'], d_ip['ip_dst'], d['type'], d['code'], d_ip['len'], d_ip['ttl'])
            else:
                evt.content = "%s: %s %s %s > %s %s [%s] %s" % (
                    d_ip['action'], d_ip['iface_in'], d_ip['mac'], d_ip['ip_src'], d_ip['ip_dst'], d_ip['proto'], d_ip['len'], d_ip['ttl'])
        return evt

