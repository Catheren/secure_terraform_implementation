#!/usr/bin/env python3
"""
Very simple Terraform security scanner.

Checks every .tf file in the current folder (and subfolders) for 5 problems:
  1. Missing required tags
  2. Resource names not following project-env-purpose pattern
  3. Regions outside us-east-1 / us-west-2
  4. Hardcoded 12-digit AWS account IDs
  5. S3 buckets with no logging resource

Usage:
  python simple_scanner.py
"""

import re
import sys
from pathlib import Path

REQUIRED_TAGS = ["Environment", "Owner", "Project", "DataClassification"]
APPROVED_REGIONS = ["us-east-1", "us-west-2"]

problem_count = 0
serious_problem_count = 0  # CRITICAL or HIGH — these should fail the pipeline


def report(level, message, filename):
    """Print one problem and keep count."""
    global problem_count, serious_problem_count
    problem_count += 1
    if level in ("CRITICAL", "HIGH"):
        serious_problem_count += 1
    print(f"[{level}] {filename}: {message}")


def check_file(text, filename):
    """Run all 5 checks against one file's text."""

    # 1. Tags — just look for each required word anywhere in the file
    if 'resource "aws_' in text:
        for tag in REQUIRED_TAGS:
            if tag not in text:
                report("HIGH", f"missing tag '{tag}'", filename)

    # 2. Naming convention — resource name should split into 3 pieces by "-"
    for name in re.findall(r'resource\s+"[\w]+"\s+"([\w-]+)"', text):
        if len(name.split("-")) != 3:
            report("MEDIUM", f"resource name '{name}' should look like project-env-purpose", filename)

    # 3. Regions — anything shaped like "xx-xxxx-1" that isn't on the approved list
    for region in re.findall(r'"([a-z]+-[a-z]+-\d)"', text):
        if region not in APPROVED_REGIONS:
            report("HIGH", f"region '{region}' is not approved", filename)

    # 4. Hardcoded account IDs — any quoted 12-digit number
    for account_id in re.findall(r'"\d{12}"', text):
        report("CRITICAL", f"hardcoded account ID {account_id}", filename)

    # 5. S3 logging — every bucket needs a logging resource somewhere in the file
    if 'resource "aws_s3_bucket"' in text and "aws_s3_bucket_logging" not in text:
        report("MEDIUM", "S3 bucket has no logging resource", filename)


def main():
    # allow an optional folder argument, otherwise scan current folder
    folder = sys.argv[1] if len(sys.argv) > 1 else "."

    tf_files = list(Path(folder).rglob("*.tf"))
    if not tf_files:
        print(f"No .tf files found in {folder}")
        return

    for tf_file in tf_files:
        text = tf_file.read_text(encoding="utf-8", errors="ignore")
        check_file(text, str(tf_file))

    print(f"\n{problem_count} total problem(s), {serious_problem_count} serious (CRITICAL/HIGH)")

    # fail the pipeline (non-zero exit code) if anything serious was found
    if serious_problem_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
