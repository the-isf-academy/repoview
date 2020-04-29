import json
from pathlib import Path
from collections import defaultdict
from github import Github, Repository
from tqdm import tqdm
import pandas as pd
from datetime import datetime
import tasks.settings as s
from tasks.errors import (
    NotFoundError,
    MultipleFoundError,
)

def authenticate():
    if s.GITHUB_ACCESS_TOKEN is None:
        raise ValueError("You need a GITHUB ACCESS TOKEN. "
            "Go to https://github.com/settings/tokens, "
            "get one, and add it to tasks/settings.py."
        )
    return Github(s.GITHUB_ACCESS_TOKEN)

def parse_date(datestring):
    """
    Flexibly parses dates from the following formats:

    - '2020'        -> 2020-01-01
    - '2020-02'     -> 2020-02-01
    - '2020-03-04'  -> 2020-03-04
    """
    year = "(?P<year>\d{4})"
    month = "(?P<month>\d{2})"
    day = "(?P<month>\d{2})"
    for pattern in [year, year+'-'+month, year+'-'+month+'-'+day]:
        match = re.match(pattern, datestring)
        if match:
            year = match.group('year')
            month = match.group('month') or 1
            day = match.group('day') or 1
            return datetime(year=year, month=month, day=day)

def get_student_repos(project_base_repo, user_logins, assignment_prefix, cached=False):
    "For each user, returns a list of the projects"
    if cached and Path(s.STUDENT_PROJECT_REPO_CACHE).exists():
        g = authenticate()
        cache = json.loads(Path(s.STUDENT_PROJECT_REPO_CACHE).read_text())
        if project_base_repo.name in cache:
            items = cache[project_base_repo.name].items()
            return {login: [g.get_repo(repo) for repo in repos] for login, repos in items}
    org = get_org()
    org_repos = org.get_repos()
    student_repos = defaultdict(list)
    num_org_repos = org.public_repos + org.total_private_repos
    for repo in tqdm(org.get_repos(), total=num_org_repos):
        if is_github_classroom_child(project_base_repo, repo, assignment_prefix):
            for collaborator in repo.get_collaborators():
                if collaborator.login in user_logins:
                    print("{} -> {}".format(collaborator.login, repo.name))
                    student_repos[collaborator.login].append(repo)

    if Path(s.STUDENT_PROJECT_REPO_CACHE).exists():
        cache = json.loads(Path(s.STUDENT_PROJECT_REPO_CACHE).read_text())
    else:
        cache = {}
    cache[project_base_repo.name] = {
        login: [r.full_name for r in repos] for login, repos in student_repos.items()
    }
    with open(s.STUDENT_PROJECT_REPO_CACHE, 'w') as cachefile:
        json.dump(cache, cachefile)
    return student_repos

def get_org():
    "Looks up the GitHub Organization named in s.GITHUB_ORGANIZATION"
    g = authenticate()
    for org in g.get_user().get_orgs():
        if org.login == s.GITHUB_ORGANIZATION:
            return org

def choose_from_options(options, prompt=None, reprompt=None):
    "Elicit a choice from the user and return the index of the choice"
    default_prompt = "Choose from the following:"
    default_reprompt = "Invalid choice. Please try again:"
    is_valid = lambda c: c.isdigit() and int(c) >= 0 and int(c) < len(options)
    print(prompt or default_prompt)
    for i, option in enumerate(options):
        print(" {}) {}".format(i, option))
    choice = input("> ")
    while not is_valid(choice):
        print(reprompt or default_reprompt)
        choice = input("> ")
    return int(choice)

def get_project_repo(identifier):
    """
    Flexibly gets a project repo; identifier may be an index or a string
    matching part of a project name or repo name (as specified in projects.csv)
    """
    g = authenticate()
    projects = pd.read_csv(s.PROJECT_FILE)
    if identifier.isdigit():
        repo_name = projects.iloc[int(identifier)].repo
    else:
        matches = projects[projects.project_name.str.contains(identifier)]
        if len(matches) > 0:
            if len(matches) == 1:
                choice = 0
            else:
                choices = ["{} ({})".format(row.project_name, row.repo) for i, row in matches.iterrows()]
                choice = choose_from_options(choices)
            repo_name = matches.iloc[choice].repo
        else:
            matches = projects[projects.repo.str.contains(identifier)]
            if len(matches) > 0:
                if len(matches) == 1:
                    choice = 0
                else:
                    choices = ["{} ({})".format(row.project_name, row.repo) for i, row in matches.iterrows()]
                    choice = choose_from_options(choices)
                repo_name = matches.iloc[choice].repo
            else:
                raise NotFoundError("No matching projects.")
    return g.get_repo(repo_name)

def is_github_classroom_child(parent, child, assignment_prefix):
    """
    Repos created through GitHub classroom are not forked from the parent repo,
    so we can't use repos' native parent/child relations. Instead, we rely on the
    (possibly-unstable) strategy of comparing repo names.
    """
    if assignment_prefix:
        return child.name.startswith(assignment_prefix)
    else:
        return child.name.startswith(parent.name)

def create_git_repo_from_template(user, new_owner, new_repo, template_owner, template_repo, private=True):
    """Creates a new github repository from a template
    
    Args:
        user (AuthenticatedUser): user object
        new_owner (string): owner of the new repository
        new_repo (string): name of the new repository
        template_owner (string): owner of the template repository
        template_repo (string): name of the template repository
        private (boolean): if the repo is private (default True)

    Returns:
        The new repository object
    """
    post_parameters = {
        "owner": new_owner,
        "name": new_repo,
        "private": private
    }
    headers, data = user._requester.requestJsonAndCheck(
        "POST",
         "/repos/" + template_owner + "/" + template_repo + "/generate",
         headers = {"Accept":"application/vnd.github.baptiste-preview+json"},   #required because templating api in preview
        input=post_parameters
    )
    return Repository.Repository(
        user._requester, headers, data, completed=True
    )

def set_repo_permission(repo, user, permission):
    """Sets the access level on the repo for the user
    
    Args:
        repo (Repository): object for the repository
        user (string or NamedUser): user to add as a collaborator
        permission (string): "pull", "push", or "admin"
    """
    repo.add_to_collaborators(user, permission)
