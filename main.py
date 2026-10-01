"""
Friday — Main Entry Point
Starts both the LiveKit worker and the token API server concurrently.

Usage:
  python main.py              # runs both worker + API server
  python main.py --worker     # runs only the LiveKit agent worker
  python main.py --api        # runs only the token API server
"""
import argparse
import asyncio
import logging
import sys

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("friday")


async def run_api():
    """Start the FastAPI token server via uvicorn."""
    import uvicorn
    from friday.config import get_settings
    cfg = get_settings()

    logger.info(f"🌐 Token API starting on http://0.0.0.0:{cfg.api_port}")
    config = uvicorn.Config(
        "api.server:app",
        host="0.0.0.0",
        port=cfg.api_port,
        log_level="warning",   # uvicorn stays quiet, our logger handles noise
        reload=False,
    )
    server = uvicorn.Server(config)
    await server.serve()


def run_worker_sync():
    """Sync wrapper for the LiveKit worker (it manages its own event loop)."""
    from livekit.agents import WorkerOptions, cli
    from friday.agent import entrypoint
    from friday.config import get_settings
    import sys

    # Default to 'dev' unless user passed a real LiveKit subcommand.
    # Rebuild argv so our own flags (--worker/--api) never reach LiveKit's CLI parser.
    if len(sys.argv) <= 1 or sys.argv[1] not in ["dev", "start", "connect", "download-files", "console"]:
        sys.argv[1:] = ["dev"]

    cfg = get_settings()
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            api_key=cfg.livekit_api_key,
            api_secret=cfg.livekit_api_secret,
            ws_url=cfg.livekit_url,
            port=8081,   # built-in worker health server: GET / and GET /worker
        )
    )


def run_api_thread():
    """Sync wrapper to run the FastAPI server in a background thread."""
    import uvicorn
    from friday.config import get_settings
    cfg = get_settings()

    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    config = uvicorn.Config(
        "api.server:app",
        host="0.0.0.0",
        port=cfg.api_port,
        log_level="warning",
        reload=False,
    )
    server = uvicorn.Server(config)
    loop.run_until_complete(server.serve())


def main():
    parser = argparse.ArgumentParser(description="Friday — Tanish's AI voice agent")
    group  = parser.add_mutually_exclusive_group()
    group.add_argument("--worker", action="store_true", help="Run only the LiveKit agent worker")
    group.add_argument("--api",    action="store_true", help="Run only the token API server")
    args = parser.parse_args()

    # Trigger Pydantic validation (this loads .env automatically)
    try:
        from friday.config import get_settings
        get_settings()
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    if args.worker:
        logger.info("Starting in WORKER-ONLY mode")
        run_worker_sync()
    elif args.api:
        logger.info("Starting in API-ONLY mode")
        asyncio.run(run_api())
    else:
        logger.info("Starting FULL mode (worker + API server)")
        # Run API in a background thread, worker on the main thread
        import threading
        api_thread = threading.Thread(target=run_api_thread, daemon=True)
        api_thread.start()

        # The worker MUST run on the main thread to register plugins correctly
        run_worker_sync()


if __name__ == "__main__":
    main()
