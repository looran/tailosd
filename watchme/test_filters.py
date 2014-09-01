import watchme
from watchme import Watchme_event
from filters import Watchme_filter_default_syslog_iptables

if __name__ == "__main__":
    # test_default_syslog_iptables
    f = Watchme_filter_default_syslog_iptables(debug=True)
    LOG_ENTRIES = [
        (watchme.SEVERITY_LOW, "[kernel] [ 3109.964303] iptables-drop: IN=wlp3s0 OUT= MAC=ff:ff:ff:ff:ff:ff:00:88:65:3f:52:4e:08:00 SRC=10.0.95.173 DST=255.255.255.255 LEN=229 TOS=0x00 PREC=0x00 TTL=64 ID=50435 PROTO=UDP SPT=17500 DPT=17500 LEN=209"),
        (watchme.SEVERITY_LOW, "Jul 09 14:29:58 [kernel] [ 4537.453518] iptables-drop: IN=wlp3s0 OUT= MAC=ff:ff:ff:ff:ff:ff:74:27:ea:41:e6:da:08:00 SRC=10.0.97.25 DST=255.255.255.255 LEN=215 TOS=0x00 PREC=0x00 TTL=64 ID=0 DF PROTO=UDP SPT=17500 DPT=17500 LEN=195"),
        (watchme.SEVERITY_LOW, "Jul 09 14:29:58 [kernel] [ 4537.453975] iptables-drop: IN=wlp3s0 OUT= MAC=ff:ff:ff:ff:ff:ff:74:27:ea:41:e6:da:08:00 SRC=10.0.97.25 DST=10.0.255.255 LEN=215 TOS=0x00 PREC=0x00 TTL=64 ID=0 DF PROTO=UDP SPT=17500 DPT=17500 LEN=195"),
        (watchme.SEVERITY_LOW, "[kernel] [32202.574658] iptables-drop: IN=wlp3s0 OUT= MAC=01:00:5e:00:00:01:00:17:31:b4:24:68:08:00 SRC=0.0.0.0 DST=224.0.0.1 LEN=32 TOS=0x00 PREC=0xC0 TTL=1 ID=0 DF PROTO=2"),
    ]

    # Generic testing function
    for expected_severity, content in LOG_ENTRIES:
        evt = Watchme_event(watchme.SEVERITY_UNINITIALIZED, "test", content)
        evt_res = f.filter(evt)
        if evt_res.severity != expected_severity:
            print "ERROR: %s" % content
            print "Returned severity: %s" % watchme.SEVERITY[evt_res.severity]
            print "Expected severity: %s" % watchme.SEVERITY[expected_severity]
            print
