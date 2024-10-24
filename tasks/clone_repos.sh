#!/bin/bash
# example usage:
# bash clone_repos.sh lab_bank github_usernames.csv

FRONT_URL="https://github.com/the-isf-academy/"
LAB_PREFIX="$1_"
BACK_URL=".git"
FOLDER="./~/Desktop/"
mkdir -p projects
grep . $2 | while read LINE ; do 
    #Strip new line from LINE
    # echo "$FRONT_URL$LAB_PREFIX${LINE//[$'\t\r\n ']}$BACK_URL" $FOLDER$LAB_PREFIX${LINE//[$'\t\r\n ']}
    cd projects
    git clone "$FRONT_URL$LAB_PREFIX${LINE//[$'\t\r\n ']}$BACK_URL"
    cd ..
done
