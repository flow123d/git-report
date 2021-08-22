#!/usr/bin/python3

# Repositories: scan directory for repository subdirs
# Period: given by user
# make week summaries colected from all repositories and all branches
# Use author from git global configuration.

# Usage: git-report dir [aditional git log argumants]
# 
# dafault git log arguments: --author=<default> -- all --

import subprocess
import attr
import sys
import re
import os
import io

@attr.s(auto_attribs=True)
class Commit:
    date : str
    repository : str    
    message: str
    author: str
    commit: str


def git_config_author():
    name = subprocess.check_output(["git", "config", "user.name"])
    name = name.decode('utf-8').strip()
    return name


class Report:
    """
    1. Extract commits form git log output.
    2. determine week, message 
    3. group by the week
    """
    def __init__(self):
        self.weeks = {}   # key is week tuple: (year, week number)
                          # value is list of commits
    
    def add(self, git_log_stdout):
        print("FULL:", git_log_stdout)
        if (len(git_log_stdout) == 0 or 
           "Not a directory" in git_log_stdout or 
           "Not a git repository" in git_log_stdout):
            return
        
        # split by 'commit: <HASH>" 
        commits = re.split("commit ([0-9a-fA-F]+)\n", git_log_stdout)
        print("COMMITS:", commits)

#>>> datetime.date(2019, 12, 31).isocalendar()
#(2020, 1, 2)


def check_output(args, workdir):
    """
    Call git log, catch errors, in particular: not diercotry, and not git repository
    """
    error=""
    try:  
      with io.StringIO(error) as f:
        print("CMD: ", args)
        cmd = subprocess.Popen(args, 
                               cwd=workdir,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        cmd_out, cmd_err = cmd.communicate()
    except subprocess.CalledProcessError:
        commits = []
        print("Error: ", cmd_err)
    if cmd_err:
        print("Warning: ", cmd_err)

    return cmd_out.decode('utf-8')

author = git_config_author()
git_log_args=[f"--author={author}", "--date=short", "--all", "--since=9.months.ago"]
list_dir = os.getcwd()

try:
    list_dir = sys.argv[1]
    add_args = sys.argv[2:]
    git_log_args.extend(add_args)
except IndexError:
    pass

report = Report()
subdirs = os.listdir(list_dir)
for d in subdirs:
    print("\nList dir: ", d)
    full_path = os.path.join(list_dir, d)
    if not os.path.isdir(full_path):
        continue
    
    commits_out = check_output(["git", "log"] + git_log_args, full_path)
    report.add(commits_out)
    


