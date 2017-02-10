tailosd
=======

Linux On Screen Display file tailer.

### Usage

Tail system logs file and display updates on the screen using OSD:
```bash
$ tailosd /var/log/syslog

or with systemd:
$ sudo tailosd systemd
```

Reload filters by sending SIGHUP to the tailosd process:
```bash
$ kill -HUP $(pgrep -lf tailosd |grep python |cut -d' ' -f1)
```

### Install

```bash
$ sudo python setup.py install
```
#### Dependencies

* libaosd
* python-aosd
* python-setproctitle
* python-multitail

