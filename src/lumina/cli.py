from __future__ import annotations

import argparse
import os

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(prog="lumina", description="Lumina visual runtime")
    sub = parser.add_subparsers(dest="command", required=True)
    serve = sub.add_parser("serve", help="run the HTTP API")
    serve.add_argument("--host", default=os.getenv("LUMINA_HOST", "127.0.0.1"))
    serve.add_argument("--port", type=int, default=int(os.getenv("LUMINA_PORT", "8000")))
    args = parser.parse_args()
    uvicorn.run("lumina.api:app", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
