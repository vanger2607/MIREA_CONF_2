import argparse
import os
import re
import sys
from urllib.parse import urlparse

ALLOWED_TEST_MODES = {"none", "local", "mock"}

def is_url(s: str) -> bool:
    try:
        p = urlparse(s)
        return p.scheme in ("http", "https")
    except Exception:
        return False

def validate_args(args):
    errors = []

    if not args.package or not args.package.strip():
        errors.append("package: Package name is required.")
    else:
        if not re.match(r"^[A-Za-z0-9_.-]+$", args.package):
            errors.append("package: Invalid package name (allowed: letters, digits, '_', '-', '.').")

    if args.repo:
        if is_url(args.repo):
            pass
        else:
            # treat as path
            if not os.path.exists(args.repo):
                errors.append(f"repo: Path not found: {args.repo}")

    if args.test_mode not in ALLOWED_TEST_MODES:
        errors.append(f"test_mode: Unknown mode '{args.test_mode}'. Allowed: {', '.join(ALLOWED_TEST_MODES)}")

    if args.version:
        if not re.match(r"^[0-9A-Za-z_.+-:]+$", args.version):
            errors.append("version: Unusual version format. Use semantic-ish format like '1.2.3' or a tag.")

    return errors

def main(argv=None):
    parser = argparse.ArgumentParser(description="DepVis Stage 1 — minimal CLI prototype")
    parser.add_argument("-p", "--package", required=True, help="Name of analyzed package (e.g. express)")
    parser.add_argument("-r", "--repo", default="", help="Repository URL or path to test repo")
    parser.add_argument("--test-mode", default="none", help="Test repo mode: none|local|mock")
    parser.add_argument("-v", "--version", default="", help="Package version (optional)")
    parser.add_argument("--ascii-tree", action="store_true", help="Print dependencies as ASCII tree")

    args = parser.parse_args(argv)

    errors = validate_args(args)
    if errors:
        for e in errors:
            print("Error:", e, file=sys.stderr)
        sys.exit(2)

    # Requirement 3: print all user-configurable parameters as key=value
    params = {
        "package": args.package,
        "repo": args.repo,
        "test_mode": args.test_mode,
        "version": args.version if args.version else "latest",
        "ascii_tree": str(args.ascii_tree),
    }

    for k, v in params.items():
        print(f"{k}={v}")

    if args.test_mode == "mock":
        print("# running in mock mode: using embedded test data")
    elif args.repo:
        print(f"# would scan repository: {args.repo}")
    else:
        print("# no repo provided")

    
    if args.ascii_tree:
        print("\n# ASCII dependency tree (placeholder)")
        print(f"{args.package}@{params['version']}")
        print("└─ dependencies not implemented")

if __name__ == "__main__":
    main()
