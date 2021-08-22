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
import datetime

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
    
    def add(self, repository, git_log_stdout):
        if (len(git_log_stdout) == 0 or 
           "Not a directory" in git_log_stdout or 
           "Not a git repository" in git_log_stdout):
            return
        
        # split by 'commit: <HASH>" 
        commits = re.split("commit ([0-9a-fA-F]+)\n", git_log_stdout)
        for hash, log_item in zip(commits[1::2], commits[2::2]):
            #print("ITEM: ", log_item)
            match = re.match("(?:Merge: ([ 0-9a-fA-F]+)\n)?Author: (.*)\nDate:   ([0-9]+)-([0-9]+)-([0-9]+)\n\n(.*)", log_item)

            assert(match)
            #print(match.groups())
            _, author, year, month, day, message = match.groups()
            date = datetime.date(int(year), int(month), int(day))
            self.add_commit(Commit(date, repository, message, author, hash))
        #print("COMMITS:", commits)

    def add_commit(self, commit):
        year, i_week, day = commit.date.isocalendar()
        week = (year, i_week, 0)
        week_list = self.weeks.setdefault(week, list())
        week_list.append(commit)

    def print(self):
        for week in sorted(self.weeks.keys()):
            commits = self.weeks[week]
            month = min([c.date.month for c in commits])
            commits.sort(key=lambda x: x.repository )
            print(f"\n==== WEEK {week} ,month {month}")
            for c in commits:
                print(f"  {c.repository:12} : {c.message.strip()}")


def check_output(args, workdir):
    """
    Call git log, catch errors, in particular: not diercotry, and not git repository
    """
    error=""
    try:  
      with io.StringIO(error) as f:
        cmd = subprocess.Popen(args, 
                               cwd=workdir,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        cmd_out, cmd_err = cmd.communicate()
    except subprocess.CalledProcessError:
        commits = []
        print("Error: ", cmd_err)
    if cmd_err:
        if not re.match(b"fatal: not a git repository", cmd_err):
            print("Warning: ", cmd_err)

    #print("FULL:", cmd_out)
    return cmd_out.decode('utf-8')

author = git_config_author()
git_log_args=[f"--author={author}", "--date=short", "--all", "--since=15.months.ago"]
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
    # print("\nList dir: ", d)
    full_path = os.path.join(list_dir, d)
    if not os.path.isdir(full_path):
        continue
    
    commits_out = check_output(["git", "log"] + git_log_args, full_path)
    report.add(d, commits_out)

report.print()


