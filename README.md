# Dev-Utils

This repository contains a collection of useful utilities, scripts, tools for dev workflows.

# Python Scripts:

# generate_diff_doc.py

This script allows you to format the diffs between 2 branches & commits as a nicely formatted markdown document.
It will produce a `Summary of Changes` section which outlines modified / new files as a path-tree with statistics:

```markdown
# Code Changes from `41714b4975845b1d6e3277b7b92e80c66a584d2b` to `a4b92a6b15071fb8da2f5250de399585f909d2be`

> _Generated on: 2025-10-07 15:12:59 AEST_

This document outlines the code modifications, additions, and deletions

## Summary of Changes

├── node/ (Modified, +4, -2)
│ └── `database.go` (Modified, +4, -2)
├── internal/ (Modified, +19, -18)
│ └── flags/ (Modified, +19, -18)
│ └── `categories.go` (Modified, +19, -18)
├── eth/ (Modified, +39, -3)
│ ├── `handler.go` (Modified, +1, -1)
│ ├── `api_backend.go` (Modified, +5, -0)
│ ├── `backend.go` (Modified, +4, -2)
│ └── ethconfig/ (Modified, +29, -0)
│ ├── `config.go` (Modified, +8, -0)
│ └── `gen_config.go` (Modified, +21, -0)
├── cmd/ (Modified, +80, -2)
│ ├── geth/ (Modified, +16, -2)
│ │ ├── `config.go` (Modified, +3, -0)
│ │ ├── `chaincmd.go` (Modified, +6, -1)
│ │ └── `dbcmd.go` (Modified, +7, -1)
│ └── utils/ (Modified, +64, -0)
│ └── `flags.go` (Modified, +64, -0)
└── core/ (Modified, +120, -28)
├── `txindexer_test.go` (Modified, +3, -4)
├── history/ (Modified, +11, -0)
│ └── `historymode.go` (Modified, +11, -0)
├── `blockchain.go` (Modified, +22, -1)
├── `txindexer.go` (Modified, +22, -18)
└── rawdb/ (Modified, +62, -5)
├── `freezer_table.go` (Modified, +2, -1)
├── `database.go` (Modified, +3, -1)
├── `ancient_scheme.go` (Modified, +22, -0)
└── `chain_freezer.go` (Modified, +35, -3)
```

## Usage

To run the script, you need to provide the base and feature references (branches, commits, or tags) for comparison.

```bash
python3 python/generate_diff_doc.py <base_ref> <feature_ref> [options]
```

**Arguments:**

- `base_ref`: The base branch or commit hash to compare against (e.g., `main`, `v1.2.0`, `a1b2c3d`).
- `feature_ref`: The feature branch or commit hash with the new changes (e.g., `my-feature-branch`, `e4f5g6h`).

**Options:**

- `-o, --output`: The name of the output markdown file. Defaults to `TOOL_CHANGES.md`.

**Example:**

```bash
python3 python/generate_diff_doc.py main my-feature-branch -o diff_documentation.md
```

This will generate a file named `diff_documentation.md` containing the diff between the `main` and `my-feature-branch` branches.

## Prerequisites and Caveats

- **Git Requirement:** The script relies on the `git` command-line tool. You must have Git installed and accessible in your system's PATH.
- **Repository Context:** The script must be run from within a Git repository.
- **Error Handling:** The script includes basic error handling. It will exit if the `git` command is not found or if any of the `git` commands fail (e.g., if you provide an invalid reference).
