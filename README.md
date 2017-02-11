tailosd
=======

*Tail files with On Screen Display output*

```bash
tailosd [-h] [-d] [-f CONFIG_FILE] [-r]
               [-l {info,low,unknown,medium,high}]
               [target [target ...]]

OSD file tailer

positional arguments:
  target                File paths to monitor | 'systemd'

optional arguments:
  -h, --help            show this help message and exit
  -d                    Debug mode
  -f CONFIG_FILE        Configuration file for severity filters and colors
  -r                    Trigger reload of filter rules in running instance
  -l {info,low,unknown,medium,high}
                        Log level [default=info]
```

### Example: Tail system logs

```bash
$ tailosd -f tailosd_example.conf /var/log/syslog

or with systemd:
$ tailosd -f tailosd_example.conf systemd
```

The configuration file contains rules to categorise severity, set color and timeout of messages.

See [tailosd_example.conf](tailosd_example.conf) for example syntax.

Trigger reload of configuration in running tailosd instance:
```bash
$ tailosd -r
```

### Example: Tail an arbitrary file:

```bash
$ tailosd file.log
```

### Notes on tailing system logs

When displaying system logs, it can be usefull to quicly edit the configuration rules at runtime, to ignore some anoying messages for example. To achieve this, you could bind commands like the following to a keyboard shortcut.
```bash
kate /home/user/.tailosd.conf ; tailosd -r
```

### Install

From the git:

```bash
$ git clone https://github.com/looran/tailosd.git
$ cd tailosd/
$ sudo python setup.py install
```

The copy and edit the configuration file example, for example to your home directory:

```bash
$ cp tailosd_example.conf ~/.tailosd.conf
```

#### Dependencies

* libaosd
* python-aosd (in pip)
* python-multitail (in pip)

