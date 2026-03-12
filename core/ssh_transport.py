import os
import subprocess


class SSHTransport:
    def __init__(self, host, username, port=22, private_key=None):
        self.host = host
        self.username = username
        self.port = port
        self.private_key = private_key

    def _base_args(self):
        null_device = "NUL" if os.name == "nt" else "/dev/null"
        args = [
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            f"UserKnownHostsFile={null_device}",
            "-o",
            "ConnectTimeout=10",
            "-p",
            str(self.port),
        ]
        if self.private_key:
            args.extend(["-i", self.private_key])
        return args

    def exec(self, command, timeout=60):
        proc = subprocess.run(
            ["ssh", *self._base_args(), f"{self.username}@{self.host}", command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()

    def copy_to_guest(self, local_path, remote_path, timeout=120):
        remote = f"{self.username}@{self.host}:{remote_path}"
        proc = subprocess.run(
            ["scp", *self._base_args(), os.path.abspath(local_path), remote],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
