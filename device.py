#!/usr/bin/python

import sys
import os
import configparser

if len(sys.argv) != 2:
    print("""
    Usage: %s <device>
    """ % sys.argv[0], file=sys.stderr)
    sys.exit(1)

appname, device = sys.argv

root = os.path.dirname(__file__)
devices = configparser.ConfigParser()
devices.read([os.path.join(root, 'doc', 'devices.ini')])

if device not in devices.sections():
    print('Unknown device:', device)
    sys.exit(2)

files_to_update = ['panucci.conf', 'default.conf']
files_to_update = [os.path.join(root, 'data', x) for x in files_to_update]

def config_from_file(filename):
    parser = configparser.ConfigParser()
    parser.read([filename])
    return parser

parsers = list(map(config_from_file, files_to_update))

for key, value in devices.items(device):
    for parser in parsers:
        parser.set('options', key, value)

for parser, filename in zip(parsers, files_to_update):
    parser.write(open(filename, 'w'))

