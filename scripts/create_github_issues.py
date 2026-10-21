#!/usr/bin/env python3
"""
CodeAtlas Comprehensive GitHub Issue Automation Script
Parses all 118 structured issues from `docs/issues/*.md` and can create them via `gh issue create`.

Usage:
    python scripts/create_github_issues.py --dry-run
    python scripts/create_github_issues.py --phase 0
    python scripts/create_github_issues.py --all
"""

import argparse
import glob
import os
import re
import subprocess
import sys


def parse_issue_files(issues_dir: str, target_phase: str | None = None) -> list[dict]:
    pattern = os.path.join(issues_dir, "0[0-5]-phase-*.md")
    files = sorted(glob.glob(pattern))
    all_issues = []

    for file_path in files:
        filename = os.path.basename(file_path)
        if target_phase is not None:
            if f"phase-{target_phase}" not in filename:
                continue

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Split on headers like: ### Issue #001: `[FEAT]: ...`
        issue_blocks = re.split(r"\n(?=### Issue #\d+:)", content)
        for block in issue_blocks:
            if not block.strip().startswith("### Issue #"):
                continue

            lines = block.strip().split("\n")
            title_line = lines[0]
            # Match title
            m_title = re.search(r"### Issue #(\d+):\s*`?([^`\n]+)`?", title_line)
            if not m_title:
                continue

            issue_num = m_title.group(1)
            raw_title = m_title.group(2).strip()

            labels = []
            milestone = ""
            component = ""
            status = "ready"
            body_lines = []

            in_metadata = True
            for line in lines[1:]:
                if in_metadata:
                    if line.startswith("- **Labels**:") or line.startswith("**Labels**:"):
                        label_text = re.sub(r"-\s*\*\*Labels\*\*:\s*", "", line)
                        labels = [lbl.strip("` ") for lbl in label_text.split(",") if lbl.strip()]
                    elif line.startswith("- **Milestone**:") or line.startswith("**Milestone**:"):
                        milestone = re.sub(r"-\s*\*\*Milestone\*\*:\s*", "", line).strip("` ")
                    elif line.startswith("- **Component**:") or line.startswith("**Component**:"):
                        component = re.sub(r"-\s*\*\*Component\*\*:\s*", "", line).strip("` ")
                    elif line.startswith("- **Status**:") or line.startswith("**Status**:"):
                        status = re.sub(r"-\s*\*\*Status\*\*:\s*", "", line).strip("` ")
                    elif line.startswith("- **Problem Statement**:") or line.startswith("### Problem Statement"):
                        in_metadata = False
                        body_lines.append(line)
                    elif line.startswith("---") or line.strip() == "":
                        continue
                    else:
                        in_metadata = False
                        body_lines.append(line)
                else:
                    body_lines.append(line)

            all_issues.append({
                "number": int(issue_num),
                "title": f"#{issue_num}: {raw_title}",
                "labels": labels,
                "milestone": milestone,
                "component": component,
                "status": status,
                "body": "\n".join(body_lines).strip(),
                "source_file": filename,
            })

    return all_issues


def check_gh_cli() -> bool:
    try:
        res = subprocess.run(["gh", "--version"], capture_output=True, text=True)
        return res.returncode == 0
    except FileNotFoundError:
        return False


def main():
    parser = argparse.ArgumentParser(description="CodeAtlas GitHub Issue Automation")
    parser.add_argument("--dry-run", action="store_true", help="Print parsed issues without executing gh CLI")
    parser.add_argument("--phase", type=str, default=None, help="Filter by phase number (0, 1, 2, 3, 4, 5)")
    parser.add_argument("--all", action="store_true", help="Create all parsed issues in GitHub")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of issues to process")

    args = parser.parse_args()

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    issues_dir = os.path.join(repo_root, "docs", "issues")

    if not os.path.exists(issues_dir):
        print(f"Error: Directory not found: {issues_dir}")
        sys.exit(1)

    issues = parse_issue_files(issues_dir, target_phase=args.phase)
    if args.limit:
        issues = issues[:args.limit]

    print(f"Found {len(issues)} issues across docs/issues/.")

    if args.dry_run or not args.all:
        print("\n--- Dry Run Sample (first 5 issues) ---")
        for iss in issues[:5]:
            print(f"\nIssue #{iss['number']}: {iss['title']}")
            print(f"  Labels:    {', '.join(iss['labels'])}")
            print(f"  Component: {iss['component']}")
            print(f"  File:      {iss['source_file']}")
            print(f"  Body length: {len(iss['body'])} chars")
        print("\nTo create issues on GitHub via gh CLI, run with `--all`.")
        return

    if not check_gh_cli():
        print("Error: GitHub CLI (`gh`) is not installed or not authenticated.")
        print("Please install gh and run `gh auth login` before executing.")
        sys.exit(1)

    print(f"Proceeding to create {len(issues)} issues on GitHub...")
    for iss in issues:
        cmd = ["gh", "issue", "create", "--title", iss["title"], "--body", iss["body"]]
        if iss["labels"]:
            cmd.extend(["--label", ",".join(iss["labels"])])

        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                print(f"  [OK] Created Issue #{iss['number']} -> {res.stdout.strip()}")
            else:
                print(f"  [FAIL] #{iss['number']}: {res.stderr.strip()}")
        except Exception as e:
            print(f"  [ERROR] #{iss['number']}: {e}")


if __name__ == "__main__":
    main()
