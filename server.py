"""
Entry point to run the KOM-Forecast web application with uvicorn.

Usage:
    uv run server.py
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8020, reload=True)
