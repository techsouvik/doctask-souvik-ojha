"""CLI entry point for DocuMesh Engine."""

import sys
import argparse
import uvicorn
from src.graph.workflow import run_pipeline
from src.mcp.server import mcp


def main():
    parser = argparse.ArgumentParser(description="DocuMesh Agentic Document Reconciliation Engine")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Subcommand: run
    run_parser = subparsers.add_parser("run", help="Run document pile analysis CLI")
    run_parser.add_argument("--folder", default="/Users/souvikojha/doctask-souvik-ojha/test_data/greenfield_tech_park", help="Folder containing document pile")

    # Subcommand: serve
    serve_parser = subparsers.add_parser("serve", help="Start FastAPI REST server + UI")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to listen on")

    # Subcommand: mcp
    mcp_parser = subparsers.add_parser("mcp", help="Start MCP server")

    args = parser.parse_args()

    if args.command == "run" or args.command is None:
        folder = args.folder if hasattr(args, "folder") else "/Users/souvikojha/doctask-souvik-ojha/test_data/greenfield_tech_park"
        print(f"🚀 Running DocuMesh Engine on folder: {folder}")
        state = run_pipeline(doc_folder=folder)
        print("\n✅ Analysis complete!")
        print(f"Status: {state.status}")
        print(f"Findings: {len(state.findings)} ({len(state.pending_findings)} pending approval)")

    elif args.command == "serve":
        print(f"🌐 Starting FastAPI + Web UI on http://localhost:{args.port}")
        uvicorn.run("src.api.main:app", host="0.0.0.0", port=args.port, reload=True)

    elif args.command == "mcp":
        print("🤖 Starting DocuMesh MCP Server...")
        mcp.run()


if __name__ == "__main__":
    main()
