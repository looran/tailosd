#!/usr/bin/env python

import argparse

import watchme

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--multitail', dest='multitail', action='store_true', default=True,
        help='Take logs from /var/log (syslog). This is the default.'
    )
    group.add_argument(
        '--systemd', dest='systemd', action='store_true', default=False,
        help='Take logs from systemd (journald).'
    )

    args = parser.parse_args()
    w = watchme.Watchme()
    w.run(args)
