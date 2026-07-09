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
from core.publish.report import (
    now_iso,
    make_step,
    make_publish_report,
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
    started_at = now_iso()
    steps = []

    changes = has_changes()

    if not changes:
        steps.append(
            make_step(
                "changes",
                "skipped",
                "No changes to publish",
            )
        )
        return make_publish_report(started_at, steps)

    steps.append(
        make_step(
            "changes",
            "success",
            "Changes detected",
        )
    )

    if AUTO_GIT_COMMIT:
        commit_result = git_commit(commit_message)
        commit_status = "success" if commit_result["returncode"] == 0 else "failed"

        steps.append(
            make_step(
                "commit",
                commit_status,
                "Git commit completed" if commit_status == "success" else "Git commit failed",
                commit_result,
            )
        )

        if commit_status != "success":
            return make_publish_report(started_at, steps)
    else:
        steps.append(
            make_step(
                "commit",
                "skipped",
                "Auto commit disabled",
            )
        )

    if AUTO_GIT_PUSH:
        push_result = git_push()
        push_status = "success" if push_result["returncode"] == 0 else "failed"

        steps.append(
            make_step(
                "push",
                push_status,
                "Git push completed" if push_status == "success" else "Git push failed",
                push_result,
            )
        )

        if push_status != "success":
            return make_publish_report(started_at, steps)
    else:
        steps.append(
            make_step(
                "push",
                "skipped",
                "Auto push disabled",
            )
        )

    if AUTO_DEPLOY:
        steps.append(
            make_step(
                "deploy",
                "skipped",
                "Deploy layer not implemented yet",
            )
        )
    else:
        steps.append(
            make_step(
                "deploy",
                "skipped",
                "Auto deploy disabled",
            )
        )

    return make_publish_report(started_at, steps)
