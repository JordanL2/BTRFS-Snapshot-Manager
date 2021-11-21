#!/usr/bin/python3

import subprocess
import sys
import time


class CommandException(Exception):

    def __init__(self, command, code, error):
        self.command = command
        self.code = code
        self.error = error
        super().__init__(self, "Command `{}` returned code {} - {}".format(command, code, error))


class SnapshotException(Exception):

    def __init__(self, error):
        self.error = error
        super().__init__(self, error)


def cmd(command, attempts=None, fail_delay=None):
    attempt = 0
    while attempt == 0 or (attempts is not None and attempt < attempts):
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout = result.stdout.decode('utf-8').rstrip("\n")
        stderr = result.stderr.decode('utf-8').rstrip("\n")
        if result.returncode != 0:
            if attempts is not None:
                attempt += 1
                warn("Command failed, waiting before retrying...")
                time.sleep(fail_delay)
                warn("Retrying...")
            else:
                raise CommandException(command, result.returncode, stderr)
        else:
            return stdout

def log_output(level, messages):
    if GLOBAL_CONFIG['log']['level'] <= level:
        log_config = GLOBAL_CONFIG['log']['levels'][level]
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


GLOBAL_CONFIG = {
    'log': {
        'level': 0,
        'levels': [
            { 'name': 'debug', 'prefix': ''    , 'output': sys.stdout, },
            { 'name': 'info' , 'prefix': ''    , 'output': sys.stdout, },
            { 'name': 'warn' , 'prefix': '[!] ', 'output': sys.stderr, },
            { 'name': 'error', 'prefix': '[!] ', 'output': sys.stderr, },
            { 'name': 'fatal', 'prefix': '[!] ', 'output': sys.stderr, },
        ],
    },
}
