#!/bin/bash
# example usage:
# bash many_template_repos.sh lab-bank github_usernames.csv
grep . $2 | while read line ; do inv create-from-template -n "$1-$line" -t $1 -u "$line"; done
