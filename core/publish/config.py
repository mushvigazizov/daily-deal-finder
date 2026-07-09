import os

AUTO_GIT_COMMIT = os.getenv("AUTO_GIT_COMMIT", "false").lower() == "true"
AUTO_GIT_PUSH = os.getenv("AUTO_GIT_PUSH", "false").lower() == "true"
AUTO_DEPLOY = os.getenv("AUTO_DEPLOY", "false").lower() == "true"

DEFAULT_BRANCH = os.getenv("GIT_DEFAULT_BRANCH", "main")
