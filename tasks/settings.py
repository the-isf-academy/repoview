try:
    from tasks.secrets import (
        GITHUB_ORGANIZATION,
        GITHUB_ACCESS_TOKEN,
    )
except ImportError:
    pass

ROSTER_FILE = "roster.csv"
PROJECT_FILE = "projects.csv"
STUDENT_PROJECT_REPO_CACHE = "cached_student_project_repos.json"
