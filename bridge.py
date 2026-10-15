#!/usr/bin/env python3
import argparse, json, sys, urllib.request

LISTENER = "http://localhost:8500/trigger"

# If Member 3 sends private IPs (like 10.0.1.10), add them here, e.g. "10.0.1.10": "mumbai_worker"
EXTRA = {}


def load_nodes(path="inventory/hosts.ini"):
    nodes = {}
    for line in open(path):
        line = line.strip()
        if not line or line.startswith(("#", "[")) or "instance_id=" not in line:
            continue
        name = line.split()[0]
        kv = dict(p.split("=", 1) for p in line.split()[1:] if "=" in p)
        nodes[name] = {"instance_id": kv["instance_id"], "region": kv["region"], "ip": kv["ansible_host"]}
    by_host = {n["ip"]: n for n in nodes.values()}
    for host, name in EXTRA.items():
        by_host[host] = nodes[name]
    return by_host


NODES = load_nodes()

ACTIONS = {
    "scale_up": "resize_up",
    "scale_down": "resize_down",
    "resize_up": "resize_up",
    "resize_down": "resize_down",
    "load_shift": "load_shift",
    "load_restore": "load_restore",
}


def post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.loads(r.read().decode())


def build_trigger(resp):
    job = resp.get("automation_job", resp)
    if not job or "node_id" not in job:
        sys.exit("No automation job found: the threshold was not matched, so nothing to do.")
    if job.get("status", "PENDING") != "PENDING":
        sys.exit("Job status is %s, not PENDING. Skipping." % job.get("status"))

    host = job["node_id"].split(":")[0]
    if host not in NODES:
        sys.exit("Unknown node_id '%s'. Check inventory/hosts.ini." % job["node_id"])
    action = ACTIONS.get(job.get("action"))
    if not action:
        sys.exit("Unknown action '%s'. Add it to ACTIONS in bridge.py." % job.get("action"))

    trig = dict(NODES[host])
    trig.update({"action": action, "metric": "cpu"})
    if "predicted_value" in resp:
        trig["predicted_value"] = resp["predicted_value"]
    return job, trig


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="JSON file with a Member 3 response or automation_job")
    ap.add_argument("--url", help="Member 3 API base URL, e.g. http://192.168.1.5:8000")
    ap.add_argument("--node", help="node_id to predict for (used with --url)")
    ap.add_argument("--threshold", type=float, default=80)
    ap.add_argument("--listener", default=LISTENER)
    ap.add_argument("--print", dest="only_print", action="store_true", help="show the trigger, do not send")
    a = ap.parse_args()

    if a.file:
        resp = json.load(open(a.file))
    elif a.url and a.node:
        resp = post(a.url.rstrip("/") + "/api/v1/predict/live", {
            "node_id": a.node,
            "rule": {"rule_id": "cpu-high-01", "metric": "predicted_value",
                     "operator": ">", "threshold": a.threshold, "action": "scale_up"}})
    else:
        sys.exit("Give --file, or --url together with --node.")

    job, trig = build_trigger(resp)
    print("Member 3 job :", json.dumps(job))
    print("Trigger      :", json.dumps(trig))
    if a.only_print:
        return
    print("Listener says:", json.dumps(post(a.listener, trig), indent=2))


if __name__ == "__main__":
    main()
