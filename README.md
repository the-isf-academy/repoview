# RepoView

Scripts for managing student submissions to GitHub Classroom. 

## Installation

Clone this repo. Create a virtual env or use system Python. Install
dependencies with `pip install -r requirements.txt`.

### Secrets
Create or update `tasks/settings.py` with your `GITHUB_ORGANIZATION`.

Before you can use these scripts, you need a GitHub access token with 
appropriate permissions. You can create one [here](https://github.com/settings/tokens)
Update `tasks/secrets.py` with your token. Required permissions:

  - repo (Full control of private repositories)
  - admin:org / read:org (Read org and team membership, read org projects)

### Data files
Next, you need to create two data files: `roster.csv` with columns: 
  
  - `login`: Student's GitHub username
  - `name`: Any name you want for the student
  - `section`: Any string to designate the student's section

Also create `projects.csv` with columns:

  - `project_name`: Your name for the project
  - `repo`: Full name of the repository (like `username/reponame`)

### Check your settings

Once this is complete, `inv check` should run with no errors.

## Usage

Usage is available via `inv --list` and `inv --help [command]`:

    $ inv --list

    Available tasks:
    
    check           Check settings and configurations
    clear-cache     Delete the student project repo names cache file, if it exists
    latest-commit   Show each student's most recent commit
    roster          Show the roster

    $ inv --help latest-commit

    Usage: inv[oke] [--core-opts] latest-commit [--options] [other tasks here ...]
    
    Docstring:
        Show each student's most recent commit

    Options:
        -a, --message-length
        -c, --[no-]cached             Use cached copy of students' project repo names
        -e, --repo                    Display repo names
        -h, --hash                    Display commit hashes
        -m, --message                 Display commit message
        -o STRING, --outfile=STRING   Save results to file instead of displaying
        -p STRING, --project=STRING   Project index, or part of project name, or part of project repo name
        -r STRING, --order=STRING     Column by which to sort results
        -s STRING, --section=STRING   Filter by section
        -t, --stats                   Display commit stats (addition, deletion line counts)
        -u, --url                     Display html url for commit
    

### Caching
Unfortunately, there is not yet an easy way to find students' versions of
assignments distributed via GitHub Classroom using the API. Instead, we need to
iterate over all repos in the organization, comparing their names. This is slow,
so the results are cached. (Note: Students' latest commits are not cached, so
you will always get fresh results unless students abandon a project and re-start
an assignment.) If you run into errors, try clearing the cache.

## Roadmap

- Let's add more tasks to this system as the need arises.
  [Here](http://docs.pyinvoke.org/en/stable/index.html) is the documentation for
  Invoke, the framework we are using. 
- Keep an eye on [this issue](https://github.com/education/classroom/issues/1679);
the Classroom API is in active development.
