from github import Github, Repository, GithubException
import csv
from datetime import datetime
import settings as s
import sys
import argparse

def get_org():
    "Looks up the GitHub Organization named in s.GITHUB_ORGANIZATION"
    g = authenticate()
    
    for org in g.get_user().get_orgs():
        if org.login == s.GITHUB_ORGANIZATION:
            return org


def authenticate():
    if s.GITHUB_ACCESS_TOKEN is None:
        raise ValueError("You need a GITHUB ACCESS TOKEN. "
            "Go to https://github.com/settings/tokens, "
            "get one, and add it to tasks/settings.py."
        )
    return Github(s.GITHUB_ACCESS_TOKEN)

def create_repos(template_repo_name, new_repo_name, public=False, users=None, permission="admin"):
    """Create a new repository from a template repository
    """
    g=authenticate()
    owner = get_org()
    print(users)

    try:
        # Get the template repository from the organization
        template_repo = owner.get_repo(template_repo_name)

        new_repo = owner.create_repo_from_template(name=new_repo_name, repo=template_repo, private=not public)

        print(f"Successfully created new repository: {new_repo.full_name}")
        
        # Add collaborators to the new repository
        if users:
            print("Adding collaborators...")
            for user_login in users:
                try:
                    user_to_add = g.get_user(user_login)
                    new_repo.add_to_collaborators(user_to_add, permission=permission)
                    print(f"  - Added '{user_login}' with '{permission}' permission.")
                except GithubException as e:
                    print(f"  - Failed to add user '{user_login}': {e}")
                    continue
        
        return new_repo
    
    except GithubException as e:
        print(f"An error occurred during repository creation or collaborator addition: {e}")
        return None

def delete_repo(repo):   
    g=authenticate()
    owner = get_org().login

    full_repo_name = f"{owner}/{repo}"
    
    try:
        repo_to_delete = g.get_repo(full_repo_name)
        print(f"Found repository to delete: {repo_to_delete.full_name}")
        repo_to_delete.delete()
        print(f". - Successfully deleted repository: {full_repo_name}")
        return True
    except GithubException as e:
        print(f"Failed to delete repository '{full_repo_name}': {e}")
        return False

def get_repo_info(repo_name, name):
    g = authenticate()
    owner_org = get_org().login
    full_repo_name = f"{owner_org}/{repo_name}"
    
    try:
        repo = g.get_repo(full_repo_name)
        commits = repo.get_commits()
        commit_count = commits.totalCount-1

        print(f"{name[0]} has {commit_count} commits.")

        if commit_count > 0:
            for commit in commits[:commit_count]:
                print(f" [{commit.commit.author.date.strftime('%Y-%m-%d')}] {commit.stats.total} lines ({commit.stats.additions} additions, {commit.stats.deletions} deletions)")
                print(f"  - {commit.commit.message}")
                # print(f"  - Changes: {commit.stats.total} lines ({commit.stats.additions} additions, {commit.stats.deletions} deletions)")


        print()
        return commit_count
    
    except GithubException as e:
        print(f"Failed to get commit count for '{full_repo_name}': {e}")
        return -1
    
def main():
    """
    Parses command-line arguments and runs the appropriate GitHub API function.

    python repo_management.py -csv year2-1.csv -lab lab_database --log
    """

    
    parser = argparse.ArgumentParser(description="GitHub Repository Management CLI")
    
    # required arguements
    parser.add_argument("-csv",  help="The csv with student github usernames")
    parser.add_argument("-lab", help="The csv with student github usernames")
    
    # arguement for selecting option
    parser.add_argument("--create", help="Create a new repository from a template.", action="store_true")
    parser.add_argument("--template-repo", help="The name of the template repository to use with --create.", action="store_true")
    parser.add_argument("--log", help="Print the commit log for a repository.", action="store_true")
    parser.add_argument("--delete", help="Print the commit log for a repository.", action="store_true")

    args = parser.parse_args()

    with open(args.csv, "r") as github_names:
        csvFile = csv.reader(github_names)

        for name in csvFile:
            repo_name = f"{args.lab}_{name[0]}"

            if args.log:
                get_repo_info(repo_name, name)

            elif args.delete:
                delete_repo(repo_name)
           
            elif args.create:
                get_repo_info(repo_name, name)
    

if __name__ == "__main__":
    main()

