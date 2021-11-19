#!/usr/bin/python3

import subprocess
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
                info("! Command failed, waiting before retrying...")
                time.sleep(fail_delay)
                info("! Retrying...")
            else:
                raise CommandException(command, result.returncode, stderr)
        else:
            return stdout

def info(*messages):
    print(' '.join([str(m) for m in messages]), flush=True)

def warn(*messages):
    print('[WARNING]', ' '.join([str(m) for m in messages]), flush=True)
