"""
Log Handler for Live Log Viewing
Captures application logs and makes them available via API
"""

import logging
from collections import deque
from datetime import datetime
from typing import List, Dict, Optional
import json

class LogCapture(logging.Handler):
    """Custom logging handler that captures logs in memory for API access"""
    
    def __init__(self, max_logs: int = 1000):
        super().__init__()
        self.max_logs = max_logs
        self.logs = deque(maxlen=max_logs)
        
    def emit(self, record):
        """Capture log record"""
        try:
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'level': record.levelname,
                'message': self.format(record),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno
            }
            self.logs.append(log_entry)
        except Exception:
            self.handleError(record)
    
    def get_logs(self, 
                 limit: Optional[int] = None, 
                 level: Optional[str] = None,
                 since: Optional[datetime] = None) -> List[Dict]:
        """
        Get captured logs with optional filtering
        
        Args:
            limit: Maximum number of logs to return
            level: Filter by log level (INFO, WARNING, ERROR, etc.)
            since: Only return logs after this timestamp
        """
        logs = list(self.logs)
        
        # Filter by level
        if level:
            logs = [log for log in logs if log['level'] == level.upper()]
        
        # Filter by timestamp
        if since:
            since_iso = since.isoformat()
            logs = [log for log in logs if log['timestamp'] > since_iso]
        
        # Apply limit
        if limit:
            logs = logs[-limit:]
        
        return logs
    
    def get_stats(self) -> Dict:
        """Get statistics about captured logs"""
        logs = list(self.logs)
        
        return {
            'total': len(logs),
            'by_level': {
                'INFO': sum(1 for log in logs if log['level'] == 'INFO'),
                'WARNING': sum(1 for log in logs if log['level'] == 'WARNING'),
                'ERROR': sum(1 for log in logs if log['level'] == 'ERROR'),
                'SUCCESS': sum(1 for log in logs if log['level'] == 'SUCCESS'),
                'DEBUG': sum(1 for log in logs if log['level'] == 'DEBUG'),
            },
            'oldest': logs[0]['timestamp'] if logs else None,
            'newest': logs[-1]['timestamp'] if logs else None,
        }
    
    def clear(self):
        """Clear all captured logs"""
        self.logs.clear()


# Global log capture instance
log_capture = LogCapture(max_logs=1000)

def setup_log_capture(logger: logging.Logger):
    """
    Setup log capture for a logger
    
    Args:
        logger: The logger instance to capture logs from
    """
    log_capture.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    log_capture.setFormatter(formatter)
    logger.addHandler(log_capture)
    return log_capture