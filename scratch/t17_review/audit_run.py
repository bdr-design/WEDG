#!/usr/bin/env python3
"""Run a build script under an audit hook: log every file it opens for reading outside the Python install,
every socket connect and subprocess. usage: blendenv/bin/python audit_run.py LOG script.py [args...]"""
import sys, runpy, os
log_path = sys.argv[1]; script = sys.argv[2]; sys.argv = sys.argv[2:]
skip = (sys.prefix, sys.base_prefix, '/usr/lib', '/usr/local/lib', '/proc', '/dev', '/sys', '/etc')
log = open(log_path, 'w', buffering=1)
def hook(ev, args):
    if ev == 'open':
        p = str(args[0]); mode = str(args[1]) if len(args) > 1 else 'r'
        if not p.startswith(skip): log.write(f'open {mode} {p}\n')
    elif ev in ('socket.connect', 'socket.getaddrinfo', 'urllib.Request', 'subprocess.Popen', 'os.system'):
        log.write(f'{ev} {args!r:.300}\n')
sys.addaudithook(hook)
runpy.run_path(script, run_name='__main__')
