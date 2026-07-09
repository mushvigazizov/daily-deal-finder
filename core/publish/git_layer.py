import subprocess

def run_git_command(args):
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
    )

    return {
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }

def git_status():
    return run_git_command(["status", "--short"])

def has_changes():
    status = git_status()
    return bool(status["stdout"])

import subprocess

def git_commit(message="Automatic content update"):
    subprocess.run(
        ["git", "add", "-A"],
        capture_output=True,
        text=True,
    )

    result = subprocess.run(
        ["git", "commit", "-m", message],
        capture_output=True,
        text=True,
    )

    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }

def git_push(remote="origin", branch="main"):
    result = subprocess.run(
        ["git", "push", remote, branch],
        capture_output=True,
        text=True,
    )

    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
