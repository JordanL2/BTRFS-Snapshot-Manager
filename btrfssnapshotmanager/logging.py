#!/usr/bin/python3

import sys


def log_output(level, messages):
    if LOG_CONFIG['level'] <= level:
        log_config = LOG_CONFIG['levels'][level]
        print(log_config['prefix']
              + ' '.join([str(m) for m in messages]), file=log_config['output'], flush=True)

def debug(*messages):
    log_output(0, messages)

def info(*messages):
    log_output(1, messages)

def warn(*messages):
    log_output(2, messages)

def error(*messages):
    log_output(3, messages)

def fatal(*messages, error_code=1):
    log_output(4, messages)
    sys.exit(error_code)


LOG_CONFIG = {
    'level': 0,
    'levels': [
        { 'name': 'debug', 'prefix': ''    , 'output': sys.stdout, },
        { 'name': 'info' , 'prefix': ''    , 'output': sys.stdout, },
        { 'name': 'warn' , 'prefix': '[!] ', 'output': sys.stderr, },
        { 'name': 'error', 'prefix': '[!] ', 'output': sys.stderr, },
        { 'name': 'fatal', 'prefix': '[!] ', 'output': sys.stderr, },
    ],
}
