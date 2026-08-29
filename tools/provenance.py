#!/usr/bin/env python3
"""Which voicings came off the paper, and which this pipeline invented.

The distinction matters: a transcribed shape is a player's choice and gets
left alone, while a generated one is the tool's best guess and should be
redone whenever the generator's judgment improves.

It used to be tracked with a `derived: true` flag on each entry, and that
kept getting lost -- revert.py stripped it, refresh then skipped the
entries it should have regenerated, and stale shapes survived several
rounds of improvement. So the record lives in data/notebook-source.yaml,
which is frozen, and the flag is derived from it rather than trusted.

    tools/provenance.py --sync    rewrite the flags to match the record
    tools/provenance.py           report agreement
"""

import argparse
import glob
import os
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
RECORD = os.path.join(HERE, os.pardir, "data", "notebook-source.yaml")


def load_record(path=RECORD):
    with open(path) as fh:
        return yaml.safe_load(fh)["instruments"]


def from_notebook(record, instrument, key, chord):
    return chord in record.get(instrument, {}).get(key, [])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sync", action="store_true")
    args = ap.parse_args()

    record = load_record()
    total = {"notebook": 0, "generated": 0, "corrected": 0}

    for path in sorted(glob.glob(os.path.join(HERE, os.pardir,
                                              "data", "voicings", "*.yaml"))):
        doc = yaml.safe_load(open(path))
        name = doc["instrument"]
        if name not in record:
            continue
        changed = 0
        for kb in doc["keys"]:
            for entry in kb["chords"]:
                book = from_notebook(record, name, kb["key"], entry["chord"])
                want = None if book else True
                have = entry.get("derived")
                if have != want:
                    changed += 1
                    if want:
                        entry["derived"] = True
                    else:
                        entry.pop("derived", None)
                total["notebook" if book else "generated"] += 1
        total["corrected"] += changed
        if args.sync and changed:
            head = open(path).readline()
            with open(path, "w") as fh:
                fh.write(head)
                yaml.safe_dump(doc, fh, sort_keys=False,
                               allow_unicode=True, width=100)
        print("%-9s %d flags %s" % (name, changed,
                                    "corrected" if args.sync else "wrong"))

    print("\n%d from the notebook, %d generated"
          % (total["notebook"], total["generated"]))
    return 1 if (total["corrected"] and not args.sync) else 0


if __name__ == "__main__":
    sys.exit(main())
