#!/usr/bin/env python3
"""Inspect or convert an exported QA document; never connects to a database.

Preview is the default. Apply writes a NEW output file only. Keep the
input export and use compensation receipts for a progressed live player;
replacing live state with this offline snapshot is not a rollback.
"""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from plugin_linear_ascent.engine import collection


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--mode", choices=("preview", "apply", "reconcile"), default="preview")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    p = json.loads(args.input.read_text())
    if args.mode == "reconcile":
        result = collection.reconcile(p)
    else:
        result = collection.preview(p)
        if args.mode == "apply":
            if not args.output:
                parser.error("Apply requires --output pointing to a new file")
            if result["result"]["status"] != "applied":
                parser.error(result["result"]["reason"])
            result = result["document"]
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        with args.output.open("x") as f:
            f.write(text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
