"""
Vehicle logging utility module for comprehensive logging and timing.

This module provides structured logging capabilities for the vehicle resolution system,
including API call logging, process step logging, and performance timing.
"""

import time
from datetime import datetime
from typing import Optional, Dict, Any


# Configuration flags for enabling/disabling detailed logging
ENABLE_DETAILED_LOGGING = True  # Enable/disable enhanced logging
ENABLE_API_LOGGING = True       # Enable/disable API call details
ENABLE_TIMING_LOGGING = True    # Enable/disable timing information

# Log level constants for structured output
LOG_LEVELS = {
    'API': '🔗',
    'PROCESS': '⚙️',
    'TIMING': '⏱️',
    'VEHICLE': '🚗',
    'ERROR': '❌',
    'CACHE': '💾',
    'DATABASE': '🗄️',
    'SUCCESS': '✅',
    'WARNING': '⚠️',
    'INFO': 'ℹ️'
}


class SimpleTimer:
    """Basic timing utility for performance measurement"""
    
    def __init__(self):
        self._start_times: Dict[str, float] = {}
    
    def start(self, operation_name: str) -> float:
        """
        Start timing an operation.
        
        Args:
            operation_name: Name of the operation being timed
            
        Returns:
            Start time as timestamp
        """
        start_time = time.time()
        self._start_times[operation_name] = start_time
        return start_time
    
    def end(self, start_time: float, operation_name: str) -> float:
        """
        End timing an operation and calculate duration.
        
        Args:
            start_time: Start time from start() method
            operation_name: Name of the operation being timed
            
        Returns:
            Duration in milliseconds
        """
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        # Clean up stored start time if it exists
        if operation_name in self._start_times:
            del self._start_times[operation_name]
            
        return duration_ms


class VehicleLogger:
    """Simple logging utility for vehicle processing operations"""
    
    def __init__(self):
        self.timer = SimpleTimer()
        self.current_vehicle = None
        self.vehicle_start_time = None
        self.phase_timings = {}
        self.operation_timings = {}
        self.api_call_timings = []
        self.total_api_calls = 0
    
    def _get_timestamp(self) -> str:
        """Get formatted timestamp for log messages"""
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    def _format_log_message(self, level: str, message: str, include_timing: bool = False) -> str:
        """Format log message with timestamp, level icon, and optional timing"""
        timestamp = self._get_timestamp()
        icon = LOG_LEVELS.get(level, '📝')
        
        # Add timing info if requested and available
        timing_info = ""
        if include_timing and self.vehicle_start_time:
            elapsed = (time.time() - self.vehicle_start_time) * 1000
            timing_info = f" [{elapsed:.0f}ms]"
        
        return f"{timestamp} {icon} {message}{timing_info}"
    
    def _print_separator(self, char: str = "=", length: int = 80, color: str = None) -> None:
        """Print a visual separator line"""
        separator = char * length
        if color:
            # Simple color support for terminals that support ANSI codes
            colors = {
                'blue': '\033[94m',
                'green': '\033[92m',
                'yellow': '\033[93m',
                'red': '\033[91m',
                'reset': '\033[0m'
            }
            if color in colors:
                separator = f"{colors[color]}{separator}{colors['reset']}"
        print(separator)
    
    def log_api_call_start(self, operation: str, vehicle_info: str, prompt: str) -> None:
        """
        Log the start of an API call with request details.
        
        Args:
            operation: Type of API operation (e.g., 'validation', 'resolution')
            vehicle_info: Vehicle information being processed
            prompt: The prompt/instruction being sent to the API
        """
        if not ENABLE_API_LOGGING or not ENABLE_DETAILED_LOGGING:
            return
        
        print(self._format_log_message("API", f"🚀 Starting {operation} API call", True))
        print(self._format_log_message("INFO", f"Vehicle: {vehicle_info}"))
        
        # Show truncated prompt for readability
        max_prompt_length = 200
        if len(prompt) > max_prompt_length:
            truncated_prompt = prompt[:max_prompt_length] + "..."
            print(self._format_log_message("INFO", f"Prompt: {truncated_prompt}"))
        else:
            print(self._format_log_message("INFO", f"Prompt: {prompt}"))
    
    def log_api_call_end(self, operation: str, response: str, duration_ms: float) -> None:
        """
        Log the end of an API call with response details and timing.
        
        Args:
            operation: Type of API operation
            response: Raw response from the API
            duration_ms: Duration of the API call in milliseconds
        """
        if not ENABLE_API_LOGGING or not ENABLE_DETAILED_LOGGING:
            return
        
        # Track API call timing for analysis
        self.track_api_call_timing(operation, duration_ms)
        
        # Determine performance level for color coding
        perf_icon = "🟢" if duration_ms < 2000 else "🟡" if duration_ms < 5000 else "🔴"
        
        print(self._format_log_message("SUCCESS", f"{perf_icon} Completed {operation} API call in {duration_ms:.2f}ms"))
        
        # Show truncated response for readability
        max_response_length = 300
        if len(response) > max_response_length:
            truncated_response = response[:max_response_length] + "... [truncated]"
            print(self._format_log_message("INFO", f"Response: {truncated_response}"))
        else:
            print(self._format_log_message("INFO", f"Response: {response}"))
    
    def log_process_step(self, step: str, details: str, duration_ms: Optional[float] = None) -> None:
        """
        Log a processing step with optional timing information.
        
        Args:
            step: Name of the processing step
            details: Additional details about the step
            duration_ms: Optional duration in milliseconds
        """
        if not ENABLE_DETAILED_LOGGING:
            return
        
        # Track phase timing for summary
        if duration_ms is not None:
            self.phase_timings[step] = duration_ms
        
        timing_info = f" ({duration_ms:.2f}ms)" if duration_ms is not None and ENABLE_TIMING_LOGGING else ""
        print(self._format_log_message("PROCESS", f"{step}: {details}{timing_info}", True))
    
    def log_timing(self, operation: str, duration_ms: float) -> None:
        """
        Log timing information for an operation.
        
        Args:
            operation: Name of the operation
            duration_ms: Duration in milliseconds
        """
        if not ENABLE_TIMING_LOGGING or not ENABLE_DETAILED_LOGGING:
            return
        
        # Track timing for analysis
        self.track_operation_timing(operation, duration_ms)
        self.phase_timings[operation] = duration_ms
        
        # Performance-based icons and analysis
        perf_icon = "⚡" if duration_ms < 1000 else "🐌" if duration_ms > 10000 else "⏱️"
        
        # Add performance context
        if duration_ms > 10000:  # > 10 seconds
            perf_note = " (SLOW - consider optimization)"
        elif duration_ms < 500:  # < 0.5 seconds
            perf_note = " (FAST)"
        else:
            perf_note = ""
        
        print(self._format_log_message("TIMING", f"{perf_icon} {operation} completed in {duration_ms:.2f}ms{perf_note}"))
    
    def log_vehicle_start(self, vehicle_info: str) -> None:
        """
        Log the start of vehicle processing with enhanced visual separation.
        
        Args:
            vehicle_info: Information about the vehicle being processed
        """
        if not ENABLE_DETAILED_LOGGING:
            return
        
        self.current_vehicle = vehicle_info
        self.vehicle_start_time = time.time()
        self.phase_timings = {}
        self.operation_timings = {}
        self.api_call_timings = []
        self.total_api_calls = 0
        
        print()  # Add spacing
        self._print_separator("=", 80, 'blue')
        print(self._format_log_message("VEHICLE", f"🚀 STARTING PROCESSING: {vehicle_info}"))
        print(self._format_log_message("INFO", f"Start time: {datetime.now().strftime('%H:%M:%S')}"))
        self._print_separator("=", 80, 'blue')
        print()
    
    def log_vehicle_complete(self, vehicle_info: str, total_duration_ms: float, success: bool = True) -> None:
        """
        Log the completion of vehicle processing with comprehensive timing summary.
        
        Args:
            vehicle_info: Information about the vehicle processed
            total_duration_ms: Total processing time in milliseconds
            success: Whether processing was successful
        """
        if not ENABLE_DETAILED_LOGGING:
            return
        
        status_icon = "✅" if success else "❌"
        status_text = "COMPLETED" if success else "FAILED"
        
        print()
        self._print_separator("-", 80, 'green' if success else 'red')
        print(self._format_log_message("VEHICLE", f"{status_icon} {status_text}: {vehicle_info}"))
        print(self._format_log_message("TIMING", f"⏱️ Total processing time: {total_duration_ms:.2f}ms ({total_duration_ms/1000:.2f}s)"))
        
        # Show comprehensive timing breakdown
        self._log_timing_summary()
        
        self._print_separator("-", 80, 'green' if success else 'red')
        print()
        
        # Reset vehicle tracking
        self.current_vehicle = None
        self.vehicle_start_time = None
        self.phase_timings = {}
        self.operation_timings = {}
        self.api_call_timings = []
        self.total_api_calls = 0
    
    def log_vehicle_separator(self, vehicle_info: str) -> None:
        """
        Log a visual separator between different vehicles being processed.
        Maintained for backward compatibility.
        
        Args:
            vehicle_info: Information about the vehicle being processed
        """
        self.log_vehicle_start(vehicle_info)
    
    def log_error(self, operation: str, error_details: str) -> None:
        """
        Log error information with full details.
        
        Args:
            operation: Operation where the error occurred
            error_details: Full error details
        """
        if not ENABLE_DETAILED_LOGGING:
            return
        
        print()
        self._print_separator("!", 60, 'red')
        print(self._format_log_message("ERROR", f"❌ ERROR in {operation}"))
        print(self._format_log_message("ERROR", f"Details: {error_details}"))
        self._print_separator("!", 60, 'red')
        print()
    
    def log_cache_operation(self, operation: str, result: str, duration_ms: Optional[float] = None) -> None:
        """
        Log cache operations with timing.
        
        Args:
            operation: Type of cache operation (lookup, store, etc.)
            result: Result of the cache operation
            duration_ms: Optional duration in milliseconds
        """
        if not ENABLE_DETAILED_LOGGING:
            return
        
        # Cache-specific icons
        cache_icon = "🎯" if "hit" in result.lower() else "💨" if "miss" in result.lower() else "💾"
        timing_info = f" ({duration_ms:.2f}ms)" if duration_ms is not None and ENABLE_TIMING_LOGGING else ""
        print(self._format_log_message("CACHE", f"{cache_icon} {operation}: {result}{timing_info}", True))
    
    def log_database_operation(self, operation: str, details: str, duration_ms: Optional[float] = None) -> None:
        """
        Log database operations with timing.
        
        Args:
            operation: Type of database operation
            details: Details about the operation
            duration_ms: Optional duration in milliseconds
        """
        if not ENABLE_DETAILED_LOGGING:
            return
        
        # Database-specific icons
        db_icon = "📝" if "insert" in operation.lower() or "update" in operation.lower() else "🔍" if "query" in operation.lower() or "select" in operation.lower() else "🗄️"
        timing_info = f" ({duration_ms:.2f}ms)" if duration_ms is not None and ENABLE_TIMING_LOGGING else ""
        print(self._format_log_message("DATABASE", f"{db_icon} {operation}: {details}{timing_info}", True))
    
    def log_phase_start(self, phase_name: str) -> None:
        """
        Log the start of a major processing phase.
        
        Args:
            phase_name: Name of the processing phase
        """
        if not ENABLE_DETAILED_LOGGING:
            return
        
        print()
        self._print_separator("-", 60, 'yellow')
        print(self._format_log_message("PROCESS", f"🔄 PHASE: {phase_name}", True))
        self._print_separator("-", 60, 'yellow')
    
    def log_phase_end(self, phase_name: str, duration_ms: float, success: bool = True) -> None:
        """
        Log the end of a major processing phase.
        
        Args:
            phase_name: Name of the processing phase
            duration_ms: Duration of the phase in milliseconds
            success: Whether the phase completed successfully
        """
        if not ENABLE_DETAILED_LOGGING:
            return
        
        status_icon = "✅" if success else "❌"
        print(self._format_log_message("PROCESS", f"{status_icon} Completed {phase_name} in {duration_ms:.2f}ms"))
        print()
    
    def log_warning(self, operation: str, warning_message: str) -> None:
        """
        Log warning information.
        
        Args:
            operation: Operation where the warning occurred
            warning_message: Warning message
        """
        if not ENABLE_DETAILED_LOGGING:
            return
        
        print(self._format_log_message("WARNING", f"⚠️ {operation}: {warning_message}"))
    
    def track_api_call_timing(self, operation: str, duration_ms: float) -> None:
        """
        Track API call timing for performance analysis.
        
        Args:
            operation: Type of API operation
            duration_ms: Duration of the API call in milliseconds
        """
        self.api_call_timings.append({
            'operation': operation,
            'duration_ms': duration_ms,
            'timestamp': datetime.now()
        })
        self.total_api_calls += 1
    
    def track_operation_timing(self, operation: str, duration_ms: float) -> None:
        """
        Track operation timing for performance analysis.
        
        Args:
            operation: Name of the operation
            duration_ms: Duration in milliseconds
        """
        if operation not in self.operation_timings:
            self.operation_timings[operation] = []
        self.operation_timings[operation].append(duration_ms)
    
    def get_total_api_time(self) -> float:
        """Get total time spent on API calls in milliseconds."""
        return sum(call['duration_ms'] for call in self.api_call_timings)
    
    def get_average_api_time(self) -> float:
        """Get average API call time in milliseconds."""
        if not self.api_call_timings:
            return 0.0
        return self.get_total_api_time() / len(self.api_call_timings)
    
    def get_slowest_api_call(self) -> Optional[Dict[str, Any]]:
        """Get information about the slowest API call."""
        if not self.api_call_timings:
            return None
        return max(self.api_call_timings, key=lambda x: x['duration_ms'])
    
    def get_fastest_api_call(self) -> Optional[Dict[str, Any]]:
        """Get information about the fastest API call."""
        if not self.api_call_timings:
            return None
        return min(self.api_call_timings, key=lambda x: x['duration_ms'])
    
    def _log_timing_summary(self) -> None:
        """Log comprehensive timing summary."""
        if not ENABLE_TIMING_LOGGING:
            return
        
        print(self._format_log_message("INFO", "📊 PERFORMANCE SUMMARY:"))
        
        # API call statistics
        if self.api_call_timings:
            total_api_time = self.get_total_api_time()
            avg_api_time = self.get_average_api_time()
            slowest = self.get_slowest_api_call()
            fastest = self.get_fastest_api_call()
            
            print(f"  🔗 API Calls: {self.total_api_calls} total, {total_api_time:.2f}ms total time")
            print(f"  📈 API Average: {avg_api_time:.2f}ms per call")
            if slowest:
                print(f"  🐌 Slowest API: {slowest['operation']} ({slowest['duration_ms']:.2f}ms)")
            if fastest:
                print(f"  ⚡ Fastest API: {fastest['operation']} ({fastest['duration_ms']:.2f}ms)")
        
        # Phase timing breakdown
        if self.phase_timings:
            print(f"  ⚙️ Phase Breakdown:")
            sorted_phases = sorted(self.phase_timings.items(), key=lambda x: x[1], reverse=True)
            for phase, duration in sorted_phases:
                percentage = (duration / sum(self.phase_timings.values())) * 100 if self.phase_timings else 0
                print(f"    • {phase}: {duration:.2f}ms ({percentage:.1f}%)")
        
        # Operation timing summary
        if self.operation_timings:
            print(f"  🔧 Operation Summary:")
            for operation, durations in self.operation_timings.items():
                total_time = sum(durations)
                avg_time = total_time / len(durations)
                count = len(durations)
                print(f"    • {operation}: {count}x calls, {avg_time:.2f}ms avg, {total_time:.2f}ms total")
    
    def log_performance_milestone(self, milestone: str, elapsed_ms: float) -> None:
        """
        Log a performance milestone during processing.
        
        Args:
            milestone: Description of the milestone
            elapsed_ms: Elapsed time since vehicle processing started
        """
        if not ENABLE_TIMING_LOGGING or not ENABLE_DETAILED_LOGGING:
            return
        
        print(self._format_log_message("TIMING", f"🏁 {milestone} (elapsed: {elapsed_ms:.2f}ms)"))
    
    def log_operation_breakdown(self, operation: str, breakdown: Dict[str, float]) -> None:
        """
        Log detailed breakdown of an operation's timing.
        
        Args:
            operation: Name of the operation
            breakdown: Dictionary of sub-operation names and their durations
        """
        if not ENABLE_TIMING_LOGGING or not ENABLE_DETAILED_LOGGING:
            return
        
        total_time = sum(breakdown.values())
        print(self._format_log_message("TIMING", f"📋 {operation} breakdown ({total_time:.2f}ms total):"))
        
        for sub_op, duration in sorted(breakdown.items(), key=lambda x: x[1], reverse=True):
            percentage = (duration / total_time) * 100 if total_time > 0 else 0
            print(f"    • {sub_op}: {duration:.2f}ms ({percentage:.1f}%)")
    
    def get_progress_timing_info(self) -> Dict[str, Any]:
        """
        Get timing information formatted for progress indicators.
        
        Returns:
            Dictionary with timing information suitable for progress displays
        """
        elapsed_ms = 0
        if self.vehicle_start_time:
            elapsed_ms = (time.time() - self.vehicle_start_time) * 1000
        
        return {
            'elapsed_ms': elapsed_ms,
            'elapsed_seconds': elapsed_ms / 1000,
            'total_api_calls': self.total_api_calls,
            'total_api_time_ms': self.get_total_api_time(),
            'average_api_time_ms': self.get_average_api_time(),
            'phase_count': len(self.phase_timings),
            'current_vehicle': self.current_vehicle,
            'performance_summary': {
                'api_calls': self.total_api_calls,
                'avg_api_time': self.get_average_api_time(),
                'total_phases': len(self.phase_timings)
            }
        }
    
    def log_progress_compatible_update(self, phase: str, details: str = None) -> None:
        """
        Log an update that's compatible with progress indicators.
        
        Args:
            phase: Current phase name
            details: Optional additional details
        """
        if not ENABLE_DETAILED_LOGGING:
            return
        
        elapsed_ms = 0
        if self.vehicle_start_time:
            elapsed_ms = (time.time() - self.vehicle_start_time) * 1000
        
        timing_info = f" [{elapsed_ms:.0f}ms]" if elapsed_ms > 0 else ""
        detail_info = f" - {details}" if details else ""
        
        print(self._format_log_message("PROCESS", f"🔄 {phase}{detail_info}{timing_info}"))


# Global logger instance for easy access throughout the application
vehicle_logger = VehicleLogger()