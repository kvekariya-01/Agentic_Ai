"""
Policy Middleware with Rate Limiting
This module provides security governance for agent operations by enforcing
YAML-based policies including rate limits, module restrictions, and action blocks.
"""

import yaml
import json
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Optional, Deque


class PolicyMiddleware:
    """
    Middleware that intercepts every action, validates against policy,
    enforces rate limits, and logs all outcomes for audit purposes.
    """

    def __init__(self, policy_path: str):
        """Initialize middleware with policy configuration from YAML file."""
        with open(policy_path, 'r') as f:
            self.policy = yaml.safe_load(f)
        
        self.audit_log: list[str] = []
        
        # Rate limiting state
        self.request_times: Deque[float] = deque()
        self.max_requests_per_minute = self.policy['rate_limits']['max_requests_per_minute']
        self.burst_limit = self.policy['rate_limits']['burst_limit']
        self.current_burst = 0
        self.burst_window_start: Optional[float] = None

    def validate_action(self, action_name: str, module: str) -> bool:
        """
        Validate an action against the policy.
        
        Args:
            action_name: Name of the action to execute
            module: Module the action belongs to
            
        Returns:
            True if action is allowed, False if blocked
        """
        # Check rate limits first
        if not self._check_rate_limit():
            return False

        # Check module authorization
        if module not in self.policy['allowed_modules']:
            return self._enforce_violation(f"Unauthorized module: {module}")

        # Check restricted actions
        if action_name in self.policy['restricted_actions']:
            return self._enforce_violation(f"Restricted action blocked: {action_name}")

        # Record successful execution
        self._record_request()
        self.audit_log.append(
            f"[{datetime.now().isoformat()}] [PASS] {action_name} executed in module '{module}'"
        )
        return True

    def _check_rate_limit(self) -> bool:
        """
        Check and enforce rate limits.
        
        Implements a sliding window rate limiter with burst protection.
        Returns True if request is allowed, False if rate limited.
        """
        current_time = time.time()
        
        # Initialize burst window if not set
        if self.burst_window_start is None:
            self.burst_window_start = current_time
        
        # Reset burst window if minute has passed
        if current_time - self.burst_window_start >= 60:
            self.current_burst = 0
            self.burst_window_start = current_time
        
        # Check burst limit
        if self.current_burst >= self.burst_limit:
            self._enforce_violation(
                f"Rate limit exceeded: burst limit ({self.burst_limit}) reached"
            )
            return False
        
        # Remove requests older than 1 minute from sliding window
        one_minute_ago = current_time - 60
        while self.request_times and self.request_times[0] < one_minute_ago:
            self.request_times.popleft()
        
        # Check per-minute limit
        if len(self.request_times) >= self.max_requests_per_minute:
            self._enforce_violation(
                f"Rate limit exceeded: {self.max_requests_per_minute} requests/minute limit reached"
            )
            return False
        
        return True

    def _record_request(self) -> None:
        """Record a successful request for rate limiting."""
        current_time = time.time()
        self.request_times.append(current_time)
        self.current_burst += 1

    def _enforce_violation(self, message: str) -> bool:
        """Log a policy violation and return False."""
        timestamp = datetime.now().isoformat()
        violation_entry = f"[{timestamp}] [VIOLATION] {message}"
        self.audit_log.append(violation_entry)
        print(f"ALERT: {violation_entry}")
        return False

    def get_rate_limit_status(self) -> dict:
        """
        Get current rate limit status for monitoring.
        
        Returns:
            Dictionary with rate limit information
        """
        current_time = time.time()
        one_minute_ago = current_time - 60
        
        # Count requests in last minute
        requests_last_minute = sum(
            1 for t in self.request_times if t >= one_minute_ago
        )
        
        # Calculate time until rate limit resets
        if self.request_times:
            oldest_request = self.request_times[0]
            time_until_reset = max(0, 60 - (current_time - oldest_request))
        else:
            time_until_reset = 0
        
        return {
            "requests_last_minute": requests_last_minute,
            "max_requests_per_minute": self.max_requests_per_minute,
            "remaining_requests": self.max_requests_per_minute - requests_last_minute,
            "burst_usage": f"{self.current_burst}/{self.burst_limit}",
            "time_until_rate_reset": round(time_until_reset, 2)
        }

    def get_audit_log(self, filter_violations: bool = False) -> list[str]:
        """
        Retrieve audit log entries.
        
        Args:
            filter_violations: If True, return only violation entries
            
        Returns:
            List of audit log entries
        """
        if filter_violations:
            return [entry for entry in self.audit_log if "[VIOLATION]" in entry]
        return self.audit_log.copy()


# Demo execution
if __name__ == "__main__":
    # Initialize middleware
    middleware = PolicyMiddleware('agent_policy.yaml')
    
    print("=" * 60)
    print("Policy Middleware Demo - Security & Governance")
    print("=" * 60)
    
    # Test 1: Valid Action
    print("\nTest 1: Valid Action (calculate_sum in math module)")
    middleware.validate_action("calculate_sum", "math")
    
    # Test 2: Invalid Action (Blocked)
    print("\nTest 2: Invalid Action (delete_database)")
    middleware.validate_action("delete_database", "http_request")
    
    # Test 3: Unauthorized Module
    print("\nTest 3: Unauthorized Module (filesystem)")
    middleware.validate_action("read_file", "filesystem")
    
    # Display rate limit status
    print("\n" + "=" * 60)
    print("Rate Limit Status:")
    print(json.dumps(middleware.get_rate_limit_status(), indent=2))
    
    # Display audit log
    print("\n" + "=" * 60)
    print("Audit Log:")
    for entry in middleware.get_audit_log():
        print(f"  {entry}")
    
    print("\n" + "=" * 60)
    print("Violations Only:")
    for entry in middleware.get_audit_log(filter_violations=True):
        print(f"  {entry}")
