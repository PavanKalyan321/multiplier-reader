# Proper logging system with real-time updates
import sys
from datetime import datetime
from enum import Enum

class LogLevel(Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    EVENT = "EVENT"
    ROUND = "ROUND"
    WARNING = "WARNING"
    ERROR = "ERROR"
    STATUS = "STATUS"

class Logger:
    """Professional logging system with proper formatting"""

    def __init__(self):
        self.last_status_line_length = 0
        self.current_status = ""

    def clear_status_line(self):
        """Clear the current status line"""
        if self.last_status_line_length > 0:
            sys.stdout.write('\r' + ' ' * self.last_status_line_length + '\r')
            sys.stdout.flush()
            self.last_status_line_length = 0

    def get_timestamp(self):
        """Get formatted timestamp"""
        return datetime.now().strftime("%H:%M:%S")

    def log(self, message, level=LogLevel.INFO):
        """Log a message with timestamp"""
        self.clear_status_line()
        timestamp = self.get_timestamp()

        # Color codes for different levels
        colors = {
            LogLevel.DEBUG: '\033[36m',      # Cyan
            LogLevel.INFO: '\033[37m',       # White
            LogLevel.EVENT: '\033[33m',      # Yellow
            LogLevel.ROUND: '\033[35m',      # Magenta
            LogLevel.WARNING: '\033[93m',    # Bright yellow
            LogLevel.ERROR: '\033[91m',      # Bright red
            LogLevel.STATUS: '\033[32m',     # Green
        }

        reset = '\033[0m'
        color = colors.get(level, '\033[37m')

        formatted = f"{color}[{timestamp}] {level.value}: {message}{reset}"
        print(formatted)

    def status(self, message):
        """Display a status message on same line (overwrites previous)"""
        self.current_status = message
        timestamp = self.get_timestamp()
        status_line = f"[{timestamp}] STATUS: {message}"

        # Pad with spaces to clear any longer previous message
        padded = status_line + ' ' * max(0, self.last_status_line_length - len(status_line))
        self.last_status_line_length = len(status_line)

        sys.stdout.write('\r' + padded)
        sys.stdout.flush()

    def event(self, message):
        """Log a game event"""
        self.log(message, LogLevel.EVENT)

    def round_event(self, message):
        """Log a round event"""
        self.log(message, LogLevel.ROUND)

    def error(self, message):
        """Log an error"""
        self.log(message, LogLevel.ERROR)

    def warning(self, message):
        """Log a warning"""
        self.log(message, LogLevel.WARNING)

    def debug(self, message):
        """Log debug info"""
        self.log(message, LogLevel.DEBUG)

    def info(self, message):
        """Log info"""
        self.log(message, LogLevel.INFO)

    def newline(self):
        """Print a newline to separate sections"""
        self.clear_status_line()
        print()

    def section(self, title):
        """Print a section header"""
        self.clear_status_line()
        print(f"\n{'='*80}")
        print(f"{title:^80}")
        print(f"{'='*80}\n")

    def table_row(self, *columns, widths=None):
        """Print a formatted table row"""
        self.clear_status_line()
        if widths is None:
            widths = [20] * len(columns)

        row = ""
        for col, width in zip(columns, widths):
            row += f"{str(col):<{width}}"
        print(row)

    def separator(self, char='-', length=80):
        """Print a separator line"""
        self.clear_status_line()
        print(char * length)
