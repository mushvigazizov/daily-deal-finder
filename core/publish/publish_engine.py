from core.publish.config import (
    AUTO_GIT_COMMIT,
    AUTO_GIT_PUSH,
    AUTO_DEPLOY,
)
from core.publish.git_layer import has_changes, git_status

def publish_status():
    return {
        "auto_commit": AUTO_GIT_COMMIT,
        "auto_push": AUTO_GIT_PUSH,
        "auto_deploy": AUTO_DEPLOY,
        "has_changes": has_changes(),
        "git_status": git_status()["stdout"],
    }
