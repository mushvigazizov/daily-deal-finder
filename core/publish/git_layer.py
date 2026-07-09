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
