# Git Trust Boundary Hooks

This is a Python utility which uses git hooks (https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks) to detect bad symbols in:

1. Commit messages
2. File names
3. File contents
4. Commit author metadata

## Installation

Do this per development environment:

```bash
# Someonewhere sensible
mkdir -p ~/projects/github/open-security-tools
cd ~/projects/github/open-security-tools

# Clone 
git clone https://github.com/Open-Security-Tools/git_trust_boundary_hooks
cd open-security-tools

# Prepare virtual python environment
python3 -mvenv env
source env/bin/activate
pip install --upgrade pip
pip install -e .

# Install the hooks and set up the global git template
tbh-setup

# This utility downloads the bad symbol list from a Minio instance.
# Adapt to your needs...

```

## Usage

Any git repositories you initialise or clone after installing the global template will hook the following git operations:

1. `commit-msg`
2. `pre-commit`
3. `pre-push`

If the checks against bad symbols fail then the operation is blocked.

In addition, you can scan history, cached and untracked files manually using:

```bash
.git/tbh-utils scan
```

