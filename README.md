tailosd
=======

*Tail files with On Screen Display output*

```bash
tailosd [-h] [-d] [-f CONFIG_FILE] [-l {info,low,unknown,medium,high}]
               [-p] [-P] [-r]
               [target [target ...]]

Tail files with On Screen Display output

positional arguments:
  target                File paths to monitor | systemd

optional arguments:
  -h, --help            show this help message and exit
  -d                    Debug mode
  -f CONFIG_FILE        Configuration file for severity filters and colors
  -l {info,low,unknown,medium,high}
                        Log level [default=info]
  -p                    Trigger pause of OSD display in running instance
  -P                    Trigger resume of OSD display in running instance
  -r                    Trigger reload of configuration in running instance
```

### Example: Tail system logs

```bash
$ tailosd -f tailosd_example.conf /var/log/syslog

or with systemd:
$ tailosd -f tailosd_example.conf systemd
```

The configuration file contains rules to filter severity, set color and timeout of messages.

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

When displaying system logs, it is often usefull to quicly edit the configuration rules at runtime, to ignore some new anoying messages for example. To achieve this, you could bind commands like the following to a keyboard shortcut.
```bash
$ kate /home/user/.tailosd.conf ; tailosd -r
```

When the screenlock is active, or when performing particular activities, you might want to stop displaying the logs, and be informed of the events later.
```bash
Bind the following to screenlock activation, to pause OSD display:
$ tailosd -p

Unpause OSD display and display buffered events (see configuration option "pause-buffer-severity"):
$ tailosd -P
```

### Install

From the git:

```bash
$ git clone https://github.com/looran/tailosd.git
$ cd tailosd/
$ sudo python setup.py install
```

You may copy and edit at your convenience the configuration file example, for example to your home directory:

```bash
$ cp tailosd_example.conf ~/.tailosd.conf
```

#### Dependencies

* libaosd
* python-aosd (in pip)
* python-multitail (in pip)

