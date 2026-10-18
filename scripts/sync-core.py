#!/usr/bin/env python3
"""Vendor a pinned copy of the core into an add-in's tree, or check one.

    scripts/sync-core.py DEST [--ref REF]   copy makepartsnow_cad/*.py at REF (default HEAD) into DEST
    scripts/sync-core.py --check DEST       verify DEST against its CORE_PIN.json; exit 1 on any difference

Run it from this repo. Files are read from the commit (``git show REF:...``),
never from the working tree, so uncommitted core edits can't be vendored.
DEST gets the package's ``.py`` files and ``CORE_PIN.json`` (the commit, the
core version and each file's SHA-256).

It refuses to overwrite a vendored copy that was edited in place: every file
must still match the pin, and no ``.py`` file may be added. Fix the core here,
commit, and sync again. ``--force`` overwrites anyway (and says what it threw
away). It also refuses a DEST that holds files but no pin.

Standard library only; Python 3.11 or newer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = "makepartsnow_cad"
PIN = "CORE_PIN.json"
REPO = "makepartsnow/makepartsnow-cad-core"


def git(*args: str) -> bytes:
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True, capture_output=True).stdout


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def vendored_files(dest: Path) -> list[str]:
    return sorted(p.name for p in dest.glob("*.py"))


def check(dest: Path) -> list[str]:
    """Differences between DEST and its pin; empty when it is a clean copy."""
    pin_path = dest / PIN
    if not pin_path.is_file():
        return [f"{dest} has no {PIN}"]
    try:
        pin = json.loads(pin_path.read_text(encoding="utf-8"))
        files = dict(pin["files"])
    except (ValueError, KeyError, TypeError):
        return [f"{pin_path} is not a valid pin"]
    problems = []
    for name in vendored_files(dest):
        if name not in files:
            problems.append(f"{name}: added in the vendored copy")
    for name, digest in sorted(files.items()):
        path = dest / name
        if not path.is_file():
            problems.append(f"{name}: missing")
        elif sha256(path.read_bytes()) != digest:
            problems.append(f"{name}: edited in the vendored copy")
    return problems


def sync(dest: Path, ref: str, force: bool) -> int:
    commit = git("rev-parse", "--verify", f"{ref}^{{commit}}").decode().strip()
    names = [
        line.rsplit("/", 1)[1]
        for line in git("ls-tree", "--name-only", commit, f"{PACKAGE}/").decode().splitlines()
        if line.endswith(".py")
    ]
    if not names:
        print(f"sync-core: {commit[:12]} has no {PACKAGE}/*.py", file=sys.stderr)
        return 2
    if dest.exists():
        if (dest / PIN).is_file():
            problems = check(dest)
            if problems and not force:
                print("sync-core: refusing, the vendored core was changed in place:", file=sys.stderr)
                for problem in problems:
                    print(f"  {problem}", file=sys.stderr)
                print("Make the change in makepartsnow-cad-core, commit it, and sync again (or pass --force to discard).", file=sys.stderr)
                return 1
            for problem in problems:
                print(f"sync-core: --force discards: {problem}", file=sys.stderr)
        elif any(dest.iterdir()):
            print(f"sync-core: refusing, {dest} has files but no {PIN}", file=sys.stderr)
            return 1
    dest.mkdir(parents=True, exist_ok=True)
    for name in vendored_files(dest):
        if name not in names:
            (dest / name).unlink()
    files = {}
    for name in sorted(names):
        data = git("show", f"{commit}:{PACKAGE}/{name}")
        (dest / name).write_bytes(data)
        files[name] = sha256(data)
    init = git("show", f"{commit}:{PACKAGE}/__init__.py").decode()
    version = next((line.split("=", 1)[1].strip().strip("\"'") for line in init.splitlines() if line.startswith("CORE_VERSION")), "")
    pin = {"repo": REPO, "commit": commit, "core_version": version, "files": files}
    (dest / PIN).write_text(json.dumps(pin, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    dirty = git("status", "--porcelain", "--", PACKAGE).decode().strip()
    print(f"sync-core: vendored {len(files)} files of core {version} at {commit[:12]} into {dest}")
    if dirty:
        print("sync-core: note: the core has uncommitted changes; they were not vendored", file=sys.stderr)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dest", type=Path)
    parser.add_argument("--ref", default="HEAD")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    dest = Path(os.path.abspath(args.dest))
    if args.check:
        problems = check(dest)
        for problem in problems:
            print(f"sync-core: {problem}", file=sys.stderr)
        if not problems:
            print(f"sync-core: {dest} matches its pin")
        return 1 if problems else 0
    return sync(dest, args.ref, args.force)


if __name__ == "__main__":
    sys.exit(main())
