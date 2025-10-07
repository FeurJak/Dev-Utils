#!/usr/bin/env python3
import subprocess
import argparse
import datetime
import sys

def run_command(command):
    """Runs a shell command and returns its output, handling errors."""
    try:
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        return result.stdout
    except FileNotFoundError:
        print(f"Error: Command '{command[0]}' not found. Is git installed and in your PATH?")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {' '.join(command)}")
        print(f"Stderr: {e.stderr}")
        sys.exit(1)

def get_changed_files(base_ref, feature_ref):
    """Gets lists of added, modified, deleted, and renamed files."""
    command = ['git', 'diff', '--name-status', f'{base_ref}..{feature_ref}']
    output = run_command(command)

    added_files = []
    modified_files = []
    deleted_files = []
    renamed_files = []

    for line in output.strip().split('\n'):
        if not line:
            continue
        parts = line.split('\t')
        status = parts[0]
        files = parts[1:]

        if status.startswith('A'):
            added_files.append(files[0])
        elif status.startswith('M'):
            modified_files.append(files[0])
        elif status.startswith('D'):
            deleted_files.append(files[0])
        elif status.startswith('R'):
            # Renamed files are represented as R<score>\t<old_path>\t<new_path>
            renamed_files.append((files[0], files[1]))

    return added_files, modified_files, deleted_files, renamed_files

def get_file_diff(base_ref, feature_ref, file_path):
    """Gets the diff for a single file."""
    # Use --unified=10 to get more context around changes
    command = ['git', 'diff', '--unified=10', f'{base_ref}..{feature_ref}', '--', file_path]
    return run_command(command)

def get_diff_stats(base_ref, feature_ref):
    """Gets line additions and deletions for each file."""
    command = ['git', 'diff', '--numstat', f'{base_ref}..{feature_ref}']
    output = run_command(command)

    stats = {}
    for line in output.strip().split('\n'):
        if not line:
            continue
        parts = line.split('\t')
        if len(parts) == 3:
            added, deleted, file_path = parts
            # Handle binary files, which are represented with '-' for additions/deletions
            added_val = 0 if added == '-' else int(added)
            deleted_val = 0 if deleted == '-' else int(deleted)
            stats[file_path] = (added_val, deleted_val)
    return stats
def generate_tree_structure(files):
    """Builds a tree structure from a list of files and their stats."""
    tree = {'children': {}, 'stats': {}}
    for file_path, file_info in files.items():
        parts = file_path.split('/')
        current_level = tree['children']
        for part in parts[:-1]:
            if part not in current_level:
                current_level[part] = {'children': {}, 'stats': {}}
            current_level = current_level[part]['children']

        file_name = parts[-1]
        # Store file info directly, including its own stats for sorting
        additions = file_info.get('additions', 0)
        deletions = file_info.get('deletions', 0)
        file_info['total_changes'] = additions + deletions
        current_level[file_name] = file_info
    return tree

def calculate_and_sort_tree_stats(node):
    """Recursively calculates stats for directories and sorts their children."""
    if not isinstance(node, dict) or 'children' not in node:
        return 0, 0, 0

    total_additions = 0
    total_deletions = 0

    # Recurse first
    for name, content in node['children'].items():
        calculate_and_sort_tree_stats(content)

    # Calculate stats for the current node
    for name, content in node['children'].items():
        if isinstance(content, dict) and 'status' in content: # It's a file
            total_additions += content.get('additions', 0)
            total_deletions += content.get('deletions', 0)
        elif isinstance(content, dict) and 'stats' in content: # It's a directory
            total_additions += content['stats'].get('additions', 0)
            total_deletions += content['stats'].get('deletions', 0)

    node['stats'] = {
        'additions': total_additions,
        'deletions': total_deletions,
        'total_changes': total_additions + total_deletions
    }

    # Sort children by total_changes
    sorted_children = sorted(
        node['children'].items(),
        key=lambda item: (item[1].get('total_changes', 0) if 'status' in item[1] else item[1]['stats'].get('total_changes', 0))
    )
    node['children'] = dict(sorted_children)

def format_tree(tree, indent=""):
    """Formats the tree structure into a markdown string."""
    lines = []
    items = list(tree.items())
    for i, (name, content) in enumerate(items):
        connector = "└── " if i == len(items) - 1 else "├── "

        is_file = isinstance(content, dict) and 'status' in content

        if is_file:
            status = content['status']
            additions = content.get('additions', 0)
            deletions = content.get('deletions', 0)

            if status == 'Renamed':
                old_path = content['old_path']
                lines.append(f"{indent}{connector}`{name}` -> `{old_path}` (Renamed)")
            else:
                lines.append(f"{indent}{connector}`{name}` ({status}, +{additions}, -{deletions})")
        elif isinstance(content, dict): # It's a directory
            stats = content['stats']
            additions = stats.get('additions', 0)
            deletions = stats.get('deletions', 0)
            lines.append(f"{indent}{connector}{name}/ (Modified, +{additions}, -{deletions})")
            lines.extend(format_tree(content['children'], indent + ("    " if i == len(items) - 1 else "│   ")))
    return lines

def generate_markdown(base_ref, feature_ref, output_file):
    """Generates the full markdown documentation."""
    print("Gathering file changes...")
    added, modified, deleted, renamed = get_changed_files(base_ref, feature_ref)
    stats = get_diff_stats(base_ref, feature_ref)

    print(f"Found {len(added)} added, {len(modified)} modified, {len(deleted)} deleted, and {len(renamed)} renamed files.")

    all_files = {}
    for f in added:
        additions, deletions = stats.get(f, (0, 0))
        all_files[f] = {'status': 'Added', 'additions': additions, 'deletions': deletions}
    for f in modified:
        additions, deletions = stats.get(f, (0, 0))
        all_files[f] = {'status': 'Modified', 'additions': additions, 'deletions': deletions}
    for old, new in renamed:
        additions, deletions = stats.get(new, (0, 0))
        all_files[new] = {'status': 'Renamed', 'old_path': old, 'additions': additions, 'deletions': deletions}
    for f in deleted:
        all_files[f] = {'status': 'Deleted', 'additions': 0, 'deletions': 0} # Deletions are not tracked for deleted files in numstat

    # Start building the markdown content
    md_content = []
    md_content.append(f"# Code Changes from `{base_ref}` to `{feature_ref}`\n")
    md_content.append(f"> _Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S AEST')}_\n")
    md_content.append("This document outlines the code modifications, additions, and deletions\n")

    # --- Summary Section ---
    md_content.append("## Summary of Changes\n")

    if all_files:
        tree = generate_tree_structure(all_files)
        calculate_and_sort_tree_stats(tree)
        md_content.append("```")
        md_content.extend(format_tree(tree['children']))
        md_content.append("```\n")
    else:
        md_content.append("No changes detected.\n")

    # --- Detailed Changes Section ---
    md_content.append("---\n")
    md_content.append("## Detailed File Changes\n")

    files_to_diff = sorted(added + modified + [new for old, new in renamed])

    if not files_to_diff:
        md_content.append("No files with content changes to display.")
    else:
        print("Generating detailed diffs for each file...")
        for i, file_path in enumerate(files_to_diff):
            print(f"  ({i+1}/{len(files_to_diff)}) Processing: {file_path}")
            try:
                diff_output = get_file_diff(base_ref, feature_ref, file_path)
                md_content.append(f"### `{file_path}`\n")
                md_content.append("```diff")
                # Clean up the diff output slightly for better rendering
                md_content.append(diff_output.strip())
                md_content.append("```\n")
            except Exception as e:
                md_content.append(f"### `{file_path}`\n")
                md_content.append(f"Could not generate diff. Error: {e}\n")

    # --- Write to file ---
    final_output = "\n".join(md_content)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_output)

    print(f"\n✅ Successfully generated documentation at: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Markdown documentation from a git diff between two branches or commits.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'base_ref',
        type=str,
        help="The base branch or commit hash to compare against (e.g., 'v1.16.3' or 'a1b2c3d')."
    )
    parser.add_argument(
        'feature_ref',
        type=str,
        help="The feature branch or commit hash with the new changes (e.g., 'v1.16.3 or 'e4f5g6h')."
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='CHANGES.md',
        help="The name of the output markdown file (default: CHANGES.md)."
    )

    args = parser.parse_args()

    generate_markdown(args.base_ref, args.feature_ref, args.output)
