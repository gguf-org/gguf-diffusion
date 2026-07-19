#!/usr/bin/env python3
"""Copy the sibling ../diffusion engine checkout into vendor/diffusion.

Only needed to produce a self-contained sdist (`python -m build --sdist`);
regular local builds pick up the sibling checkout directly. Build artifacts
and VCS metadata are excluded.
"""

from __future__ import annotations

import argparse
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXCLUDE_DIRS = {".git", ".github", "build", ".cache", "__pycache__"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", default=str(ROOT.parent / "diffusion"),
                        help="path to the diffusion.cpp source tree (default: sibling ../diffusion)")
    args = parser.parse_args()

    src = pathlib.Path(args.engine).resolve()
    if not (src / "CMakeLists.txt").is_file():
        print(f"error: {src} does not look like the diffusion source tree", file=sys.stderr)
        return 1

    dest = ROOT / "vendor" / "diffusion"
    if dest.exists():
        print(f"removing existing {dest}")
        shutil.rmtree(dest)

    def ignore(dirpath, names):
        return [n for n in names if n in EXCLUDE_DIRS]

    print(f"copying {src} -> {dest} (this can take a while, the tree is large)")
    shutil.copytree(src, dest, ignore=ignore)
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
