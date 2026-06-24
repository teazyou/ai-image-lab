#!/usr/bin/env python3
"""comfyui_run.py — headless ComfyUI client for the lab.

Submit an API-format workflow to a running ComfyUI server, wait for it to
finish, and save the produced images. This is the lab's standard way to pilot
ComfyUI from a script (no browser, no SDK — just HTTP).

Run with the ComfyUI venv so `requests` is present:
    lab/downloads/tools/comfyui/.venv/bin/python lab/scripts/comfyui_run.py ...

Usage:
    comfyui_run.py WORKFLOW.json [options]

Options:
    --server HOST:PORT   ComfyUI address (default 127.0.0.1:8188)
    --out DIR            where to save result images (default ./)
    --upload NAME=PATH   upload PATH into the server input dir as NAME before
                         submitting; repeatable (a LoadImage node references NAME)
    --timeout SEC        max wait for completion (default 600)

WORKFLOW.json must be API format (UI: Dev Mode -> "Save (API Format)"), i.e. a
flat object  {node_id: {class_type, inputs}}  — NOT the UI graph format.

Exit 0 and prints saved paths on success; non-zero with the server error on
failure (so callers can branch on it).
"""
import argparse
import json
import os
import sys
import time

import requests


def upload_image(base, name, path):
    """Upload PATH to the server's input dir under filename NAME."""
    with open(path, "rb") as f:
        r = requests.post(
            f"{base}/upload/image",
            files={"image": (name, f, "image/png")},
            data={"overwrite": "true"},
        )
    r.raise_for_status()
    return r.json()["name"]


def submit(base, workflow, client_id):
    r = requests.post(f"{base}/prompt",
                      json={"prompt": workflow, "client_id": client_id})
    if r.status_code != 200:
        # ComfyUI returns a JSON body describing the validation error
        sys.exit(f"submit rejected ({r.status_code}): {r.text}")
    return r.json()["prompt_id"]


def wait(base, prompt_id, timeout):
    """Poll /history until PROMPT_ID completes. Returns its history entry."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        h = requests.get(f"{base}/history/{prompt_id}").json()
        if prompt_id in h:
            entry = h[prompt_id]
            status = entry.get("status", {})
            if status.get("status_str") == "error" or status.get("completed") is False:
                # surface the failing node / message
                for kind, *rest in status.get("messages", []):
                    if kind == "execution_error":
                        sys.exit(f"execution error: {json.dumps(rest, indent=2)}")
                sys.exit(f"execution failed: {json.dumps(status, indent=2)}")
            if entry.get("outputs"):
                return entry
        time.sleep(1)
    sys.exit(f"timeout after {timeout}s waiting for {prompt_id}")


def fetch_images(base, entry, out_dir):
    saved = []
    for node in entry["outputs"].values():
        for img in node.get("images", []):
            params = {"filename": img["filename"], "type": img.get("type", "output")}
            if img.get("subfolder"):
                params["subfolder"] = img["subfolder"]
            data = requests.get(f"{base}/view", params=params).content
            dest = os.path.join(out_dir, img["filename"])
            with open(dest, "wb") as f:
                f.write(data)
            saved.append(dest)
    return saved


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workflow")
    ap.add_argument("--server", default="127.0.0.1:8188")
    ap.add_argument("--out", default=".")
    ap.add_argument("--upload", action="append", default=[],
                    metavar="NAME=PATH")
    ap.add_argument("--timeout", type=int, default=600)
    args = ap.parse_args()

    base = f"http://{args.server}"
    client_id = f"lab-{os.getpid()}"
    os.makedirs(args.out, exist_ok=True)

    for spec in args.upload:
        name, path = spec.split("=", 1)
        print(f"upload {path} -> {upload_image(base, name, path)}")

    with open(args.workflow) as f:
        workflow = json.load(f)

    pid = submit(base, workflow, client_id)
    print(f"submitted prompt_id={pid}")
    entry = wait(base, pid, args.timeout)
    for p in fetch_images(base, entry, args.out):
        print(f"saved {p}")


if __name__ == "__main__":
    main()
