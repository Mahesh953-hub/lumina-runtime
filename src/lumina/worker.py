from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

from .jobs import JobStore, VisualJobWorker


def main() -> None:
    parser = argparse.ArgumentParser(prog="lumina-worker")
    parser.add_argument("--output-dir", default=os.getenv("LUMINA_OUTPUT_DIR", "./output"))
    parser.add_argument("--poll-seconds", type=float, default=1.0)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    store = JobStore(Path(args.output_dir) / "jobs.sqlite3")
    worker = VisualJobWorker(store, args.output_dir)
    while True:
        if worker.run_once() is None and args.once:
            return
        if args.once:
            continue
        time.sleep(max(0.1, args.poll_seconds))


if __name__ == "__main__":
    main()
