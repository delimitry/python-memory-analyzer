#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A tool for finding specific objects in the python process
"""

from __future__ import print_function

import argparse
import errno
import logging
import re
import sys

__version__ = '0.0.1'

PY3 = sys.version_info[0] == 3

logging.basicConfig(format='[%(levelname)s] %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.WARNING)


def read_mem_maps(pid):
    """Read memory mapping"""
    filename = '/proc/{pid}/maps'.format(pid=pid)
    mem_maps = []
    with open(filename, 'rb') as in_file:
        for line in in_file:
            # get readable memory regions
            match = re.match('([0-9a-fA-F]+)-([0-9a-fA-F]+) r.* (.*)', line)
            if match:
                start, end, name = match.groups()
                mem_maps.append({
                    'start': int(start, 16),
                    'end': int(end, 16),
                    'name': name,
                })
    return mem_maps


def read_memory(pid, mem_maps=None):
    """Read memory by PID using known memory mapping"""
    if mem_maps is None:
        mem_maps = read_mem_maps(pid)
    filename = '/proc/{pid}/mem'.format(pid=pid)
    with open(filename, 'rb') as in_file:
        for mem_map in mem_maps:
            in_file.seek(mem_map['start'])
            chunk = in_file.read(mem_map['end'] - mem_map['start'])
            yield chunk, mem_map


def analyze(pid):
    """Analyze memory by PID"""
    for chunk, mem_map in read_memory(pid):
        pass


def main():
    """Main"""
    parser = argparse.ArgumentParser(description='Python memory analyzer v{}'.format(__version__))
    parser.add_argument(
        '-p', '--pid', dest='pid', type=int,
        help='process ID (requires root privileges)', required=True)
    parser.add_argument(
        '-d', '--debug',
        help='run in debug mode', action='store_true')
    parser.add_argument(
        '-v', '--version', action='version',
        version='Python memory analyzer v{}'.format(__version__))

    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    pid = args.pid
    try:
        analyze(pid)
    except IOError as e:
        if e[0] == errno.EACCES:
            print('Please run with root privileges to read process memory')
            sys.exit(1)


if __name__ == '__main__':
    main()
