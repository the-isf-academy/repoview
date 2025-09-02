from github import Github, Repository, GithubException
import csv
from datetime import datetime
import settings as s
import sys
import argparse
import subprocess
import os

def get_org(org_name):
    "Looks up the GitHub Organization named in s.GITHUB_ORGANIZATION"
    g = authenticate()
    
    for org in g.get_user().get_orgs():
        if org.login == org_name:
            return org


def authenticate():
    if s.GITHUB_ACCESS_TOKEN is None:
        raise ValueError("You need a GITHUB ACCESS TOKEN. "
            "Go to https://github.com/settings/tokens, "
            "get one, and add it to tasks/settings.py."
        )
    return Github(s.GITHUB_ACCESS_TOKEN)

def create_repos(org_name,template_repo_name, new_repo_name, public=False, users=None, permission="admin"):
    """Create a new repository from a template repository
    """
    g=authenticate()
    owner = get_org(org_name)
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

def get_repo_info(org_name,repo_name, name):
    g = authenticate()
    owner_org = get_org(org_name).login
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

def clone_repo(org_name,lab_name, repo_name, full_directory):
    """
    Clones a GitHub repository to a specified local directory.

    Args:
        args (argparse.Namespace): The parsed command-line arguments.
    """
    try:
        g = authenticate()
        owner_org = get_org(org_name).login
        full_repo_name = f"{owner_org}/{repo_name}"
        
        repo = g.get_repo(full_repo_name)
        clone_url = repo.clone_url

        dir_repo = f"{full_directory}/{lab_name}/{repo_name}"

        print(f"Cloning '{repo_name}' into '{dir_repo}'...")

        if not os.path.exists(dir_repo):
            print(f"  -Creating directory '{dir_repo}'...")
            os.makedirs(dir_repo)
        else:
            print(f"  -Warning: Directory '{dir_repo}' already exists. Cloning into it.")
        
        # Run the git clone command using subprocess
        result = subprocess.run(
            ["git", "clone", clone_url, dir_repo],
            check=True,
            capture_output=True,
            text=True
        )

        print(f"  - Successfully cloned '{full_repo_name}'.")
        # print("Git output:\n", result.stdout)

    except subprocess.CalledProcessError as e:
        print(f"  - Error during git clone: {e}")
        print("  - Git stderr:\n", e.stderr)
    except GithubException as e:
        print(f"  - Failed to find repository '{repo_name}': {e}")
    except ValueError as e:
        print(f"  - Authentication error: {e}")
    except Exception as e:
        print(f"  - An unexpected error occurred: {e}")

def pull_all_repos(lab_name, full_directory):
    """
    Iterates through a directory and pulls the latest changes for each Git repository found.
    
    Args:
        args (argparse.Namespace): The parsed command-line arguments.
    """

    base_dir = f"{full_directory}/{lab_name}"

    if not os.path.isdir(base_dir):
        print(f"Error: Directory '{base_dir}' not found.")
        return

    original_dir = os.getcwd()
    try:
        print(f"Searching for repositories in '{base_dir}'...")
        repo_found = False
        for entry in os.scandir(base_dir):
            if entry.is_dir() and os.path.exists(os.path.join(entry.path, '.git')):
                repo_found = True
                repo_name = entry.name
                print(f"\n--- Pulling changes for '{repo_name}' ---")
                os.chdir(entry.path)
                
                try:
                    result = subprocess.run(
                        ["git", "pull"],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    print("Git output:\n", result.stdout)
                    if result.stderr:
                        print("Git stderr:\n", result.stderr)

                except subprocess.CalledProcessError as e:
                    print(f"Error during git pull for '{repo_name}': {e}")
                    print("Git stderr:\n", e.stderr)
                except Exception as e:
                    print(f"An unexpected error occurred for '{repo_name}': {e}")
                
                os.chdir(original_dir) # Change back to the original directory
        
        if not repo_found:
            print(f"No Git repositories found in '{base_dir}'.")
    
    except Exception as e:
        print(f"An error occurred while processing the directory: {e}")
    finally:
        os.chdir(original_dir) # Ensure we always change back to the original directory

def main():
    """
    Parses command-line arguments and runs the appropriate GitHub API function.

    python repo_management.py -csv year2-1.csv -lab lab_database --log
    """

    
    parser = argparse.ArgumentParser(description="GitHub Repository Management CLI")
    
    # required arguements
    parser.add_argument("-csv",  help="The csv with student github usernames")
    parser.add_argument("-lab", help="Lab template name")

    # arguement for selecting option
    
    parser.add_argument("--create", help="Create a new repository from a template.", action="store_true")
    parser.add_argument("--log", help="Print the commit log for a repository.", action="store_true")
    parser.add_argument("--delete", help="Delete repositories", action="store_true")
    parser.add_argument("--clone", help="Clone repostiories to directory.", action="store_true")
    parser.add_argument("--pull", help="Clone repostiories to directory.", action="store_true")

    parser.add_argument("--mwc", help="mwc shuyuan", action="store_true")
    parser.add_argument("--dp", help="dp", action="store_true")

    args = parser.parse_args()

    if args.mwc:
        org_name = "the-isf-academy"
        full_directory = f"{s.CLONE_DIRECTORY}/mwc"
    elif args.dp:
        org_name = "isf-dp-cs"
        full_directory = f"{s.CLONE_DIRECTORY}/dp"


    if args.csv:

        with open(args.csv, "r") as github_names:
            csvFile = csv.reader(github_names)

            for name in csvFile:
                repo_name = f"{args.lab}_{name[0]}"

                if args.log:
                    get_repo_info(org_name, repo_name, name)

                elif args.delete:
                    delete_repo(repo_name)
            
                elif args.create:
                    create_repos(repo_name, name)

                elif args.clone:
                    clone_repo(org_name, args.lab, repo_name, full_directory)

    if args.pull:
            pull_all_repos(args.lab, full_directory)

if __name__ == "__main__":
    main()

