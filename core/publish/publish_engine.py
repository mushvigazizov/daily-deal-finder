from core.publish.config import (
    AUTO_GIT_COMMIT,
    AUTO_GIT_PUSH,
    AUTO_DEPLOY,
)
from core.publish.git_layer import (
    has_changes,
    git_status,
    git_commit,
    git_push,
)

def publish_status():
    return {
        "auto_commit": AUTO_GIT_COMMIT,
        "auto_push": AUTO_GIT_PUSH,
        "auto_deploy": AUTO_DEPLOY,
        "has_changes": has_changes(),
        "git_status": git_status()["stdout"],
    }

def run_publish(commit_message="Automatic content update"):
    result = {
        "started": True,
        "has_changes": has_changes(),
        "commit": None,
        "push": None,
        "deploy": None,
    }

    if not result["has_changes"]:
        result["message"] = "No changes to publish"
        return result

    if AUTO_GIT_COMMIT:
        result["commit"] = git_commit(commit_message)

    if AUTO_GIT_PUSH:
        result["push"] = git_push()

    if AUTO_DEPLOY:
        result["deploy"] = {
            "status": "skipped",
            "reason": "Deploy layer not implemented yet",
        }

    result["message"] = "Publish flow completed"
    return result
