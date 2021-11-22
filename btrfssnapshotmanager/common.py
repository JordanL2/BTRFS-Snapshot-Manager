#!/usr/bin/python3

from btrfssnapshotmanager.logging import *

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


def cmd(command, attempts=None, fail_delay=None, return_code=False):
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
                if return_code:
                    return (stdout, stderr, result.returncode)
                raise CommandException(command, result.returncode, stderr)
        else:
            if return_code:
                return (stdout, stderr, result.returncode)
            return stdout
