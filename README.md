tailosd
=======

Linux On Screen Display file tailer.

```bash
usage: tailosd [-h] [-f FILTERS] [-l {info,low,medium,high}]
               target [target ...]

OSD file tailer

positional arguments:
  target                File paths to monitor | 'systemd'

optional arguments:
  -h, --help            show this help message and exit
  -f FILTERS            Filtering rules file
  -l {info,low,medium,high}
                        Log level [default=info]
```

### Examples

Tail system logs file on your screen using OSD:
```bash
$ tailosd -f filters_example.txt /var/log/syslog

or with systemd:
$ sudo tailosd -f filters.txt systemd
```
See [filters_example.txt](filters_example.txt) for filters rules examples.

Reload filters by sending SIGHUP to the tailosd process:
```bash
$ kill -HUP $(pgrep -lf tailosd |grep python |cut -d' ' -f1)
```

Tail any file:
```bash
$ tailosd file.log
```

### Install

```bash
$ sudo python setup.py install
```
#### Dependencies

* libaosd
* python-aosd (in pip)
* python-multitail (in pip)

