#!/usr/bin/env python3
"""
Run script for the FastAPI application
This avoids keyboard interrupt issues on Windows with reload mode
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8001,
        reload=False  # Set to False to avoid keyboard interrupt issues on Windows
    )