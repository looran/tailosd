tailosd
=======

Linux On Screen Display file tailer.

### Usage

Tail system logs file on your screen using OSD, using severity rules (coloration) from filters.txt:
```bash
$ tailosd -f filters.txt /var/log/syslog

or with systemd:
$ sudo tailosd -f filters.txt systemd
```

Reload filters by sending SIGHUP to the tailosd process:
```bash
$ kill -HUP $(pgrep -lf tailosd |grep python |cut -d' ' -f1)
```

Tail any file
```bash
$ tailosd file.log
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

