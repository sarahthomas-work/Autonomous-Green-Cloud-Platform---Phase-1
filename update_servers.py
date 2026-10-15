#!/usr/bin/env python3
import argparse, glob, re, sys

ap = argparse.ArgumentParser()
ap.add_argument("--mumbai-ip"); ap.add_argument("--mumbai-id")
ap.add_argument("--virginia-ip"); ap.add_argument("--virginia-id")
a = ap.parse_args()

old = {}
for line in open("inventory/hosts.ini"):
    m = re.match(r"(mumbai|virginia)_worker\s+ansible_host=(\S+)\s+instance_id=(\S+)", line.strip())
    if m:
        old[m.group(1)] = {"ip": m.group(2), "id": m.group(3)}
if set(old) != {"mumbai", "virginia"}:
    sys.exit("Could not read both workers from inventory/hosts.ini")

pairs = []
for who in ("mumbai", "virginia"):
    for key in ("ip", "id"):
        new = getattr(a, f"{who}_{key}")
        if new and new != old[who][key]:
            pairs.append((old[who][key], new))
if not pairs:
    sys.exit("Nothing to change. Give at least one new value.")

files = ["inventory/hosts.ini", "README.md", "member3_sample_job.json", "bridge.py"] + glob.glob("sample_trigger*.json")
for f in files:
    try:
        t = open(f).read()
    except FileNotFoundError:
        continue
    n = t
    for o, new in pairs:
        n = n.replace(o, new)
    if n != t:
        open(f, "w").write(n)
        print("updated", f)
print("Changes:", ", ".join(f"{o} -> {n}" for o, n in pairs))
