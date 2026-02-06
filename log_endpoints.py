"""
API Endpoints for Log Viewing
Add these to your main.py file
"""

from fastapi import Query
from fastapi.responses import HTMLResponse
from datetime import datetime
from typing import Optional
from log_handler import log_capture, setup_log_capture

# Add this near the top of your main.py, after creating the logger
# setup_log_capture(logger)

@app.get("/logs", response_class=HTMLResponse)
async def serve_logs_page():
    """Serve the log viewer HTML page"""
    import os
    logs_html_path = os.path.join(os.path.dirname(__file__), "logs.html")
    
    if os.path.exists(logs_html_path):
        with open(logs_html_path, 'r') as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(
            content="<h1>Log viewer not found</h1><p>Please ensure logs.html exists in the same directory as main.py</p>",
            status_code=404
        )

@app.get("/api/logs")
async def get_logs(
    limit: Optional[int] = Query(100, ge=1, le=1000, description="Maximum number of logs to return"),
    level: Optional[str] = Query(None, description="Filter by log level (INFO, WARNING, ERROR, SUCCESS, DEBUG)"),
    since: Optional[str] = Query(None, description="ISO timestamp - only return logs after this time")
):
    """
    Get application logs with optional filtering
    
    Query Parameters:
    - limit: Maximum number of logs to return (1-1000, default 100)
    - level: Filter by log level (INFO, WARNING, ERROR, SUCCESS, DEBUG)
    - since: ISO timestamp - only return logs after this time
    """
    try:
        since_dt = None
        if since:
            since_dt = datetime.fromisoformat(since)
        
        logs = log_capture.get_logs(limit=limit, level=level, since=since_dt)
        
        return {
            "success": True,
            "count": len(logs),
            "logs": logs
        }
    except Exception as e:
        logger.error(f"Error fetching logs: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "logs": []
        }

@app.get("/api/logs/stats")
async def get_log_stats():
    """
    Get statistics about application logs
    
    Returns counts by level, total logs, and timestamp range
    """
    try:
        stats = log_capture.get_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error fetching log stats: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@app.delete("/api/logs")
async def clear_logs():
    """
    Clear all captured logs
    
    This is useful for testing or when the log buffer gets too large
    """
    try:
        log_capture.clear()
        logger.info("Logs cleared via API")
        return {
            "success": True,
            "message": "All logs cleared successfully"
        }
    except Exception as e:
        logger.error(f"Error clearing logs: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/logs/stream")
async def stream_logs(since: Optional[str] = Query(None)):
    """
    Get new logs since a specific timestamp
    Useful for polling-based real-time updates
    """
    try:
        since_dt = None
        if since:
            since_dt = datetime.fromisoformat(since)
        
        logs = log_capture.get_logs(since=since_dt)
        
        return {
            "success": True,
            "count": len(logs),
            "logs": logs,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error streaming logs: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "logs": []
        }