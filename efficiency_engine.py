"""
efficiency_engine.py — Adaptive Rate Limiting & API Health Management

Provides intelligent rate limiting, key rotation, and fallback orchestration
to prevent API exhaustion during multi-agent pipeline execution.
"""

import os
import time
import random
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import deque

# Global state for API health tracking
_api_health: Dict[str, Dict[str, Any]] = {}
_health_lock = threading.Lock()

# Configuration
MAX_CONCURRENT_REQUESTS = 3
BASE_DELAY_SECONDS = 2.0
MAX_DELAY_SECONDS = 60.0
HEALTH_WINDOW_MINUTES = 5
ERROR_THRESHOLD = 3  # Consecutive errors before marking key unhealthy


def init_api_keys(api_keys: List[str]) -> None:
    """Initialize health tracking for all API keys."""
    global _api_health
    with _health_lock:
        for i, key in enumerate(api_keys):
            key_id = f"key_{i}"
            if key_id not in _api_health:
                _api_health[key_id] = {
                    "key": key,
                    "errors": 0,
                    "successes": 0,
                    "last_error_time": None,
                    "last_success_time": None,
                    "is_healthy": True,
                    "cooldown_until": None,
                    "request_times": deque(maxlen=100),
                }


def record_request(key_id: str, success: bool, error_type: Optional[str] = None) -> None:
    """Record the outcome of an API request for health tracking."""
    with _health_lock:
        if key_id not in _api_health:
            return

        health = _api_health[key_id]
        now = datetime.now()
        health["request_times"].append(now)

        if success:
            health["successes"] += 1
            health["last_success_time"] = now
            health["errors"] = 0  # Reset error count on success
            # If key was in cooldown and succeeded, mark healthy
            if health["cooldown_until"] and health["cooldown_until"] <= now:
                health["is_healthy"] = True
                health["cooldown_until"] = None
        else:
            health["errors"] += 1
            health["last_error_time"] = now

            # Check if we should mark as unhealthy
            if health["errors"] >= ERROR_THRESHOLD:
                health["is_healthy"] = False
                # Exponential backoff cooldown
                cooldown_minutes = min(2 ** health["errors"], 30)
                health["cooldown_until"] = now + timedelta(minutes=cooldown_minutes)
                print(f"⚠️ [Efficiency] Key {key_id} marked unhealthy. Cooldown: {cooldown_minutes} min")


def get_healthy_key(api_keys: List[str]) -> Optional[str]:
    """Get the healthiest available API key."""
    with _health_lock:
        if not api_keys:
            return None

        # Re-initialize if needed
        if not _api_health:
            init_api_keys(api_keys)

        now = datetime.now()
        healthy_keys = []

        for i, key in enumerate(api_keys):
            key_id = f"key_{i}"
            if key_id not in _api_health:
                _api_health[key_id] = {
                    "key": key,
                    "errors": 0,
                    "successes": 0,
                    "last_error_time": None,
                    "last_success_time": None,
                    "is_healthy": True,
                    "cooldown_until": None,
                    "request_times": deque(maxlen=100),
                }

            health = _api_health[key_id]

            # Check if cooldown expired
            if health["cooldown_until"] and health["cooldown_until"] <= now:
                health["is_healthy"] = True
                health["cooldown_until"] = None

            if health["is_healthy"]:
                healthy_keys.append((key_id, health))

        if not healthy_keys:
            # All keys unhealthy - force reset the one with oldest cooldown
            oldest = min(_api_health.items(), key=lambda x: x[1].get("cooldown_until") or datetime.max)
            oldest[1]["is_healthy"] = True
            oldest[1]["cooldown_until"] = None
            oldest[1]["errors"] = 0
            print(f"🔄 [Efficiency] All keys exhausted. Force-resetting {oldest[0]}")
            return oldest[1]["key"]

        # Sort by success rate and recency
        healthy_keys.sort(key=lambda x: (
            x[1]["successes"] / max(1, x[1]["successes"] + x[1]["errors"]),
            x[1]["last_success_time"] or datetime.min
        ), reverse=True)

        return healthy_keys[0][1]["key"]


def get_key_stats(key_id: str) -> Dict[str, Any]:
    """Get health statistics for a specific key."""
    with _health_lock:
        if key_id not in _api_health:
            return {"error": "Key not tracked"}
        health = _api_health[key_id].copy()
        # Convert deque to list for serialization
        health["request_times"] = list(health["request_times"])
        return health


def get_all_stats() -> Dict[str, Dict[str, Any]]:
    """Get health statistics for all tracked keys."""
    with _health_lock:
        stats = {}
        for key_id, health in _api_health.items():
            stats[key_id] = health.copy()
            stats[key_id]["request_times"] = list(health["request_times"])
        return stats


def calculate_adaptive_delay(key_id: str, base_delay: float = BASE_DELAY_SECONDS) -> float:
    """Calculate adaptive delay based on recent request rate and errors."""
    with _health_lock:
        if key_id not in _api_health:
            return base_delay

        health = _api_health[key_id]
        now = datetime.now()

        # Count requests in the health window
        recent_requests = sum(
            1 for t in health["request_times"]
            if now - t < timedelta(minutes=HEALTH_WINDOW_MINUTES)
        )

        # Calculate requests per minute
        rpm = recent_requests / HEALTH_WINDOW_MINUTES if HEALTH_WINDOW_MINUTES > 0 else 0

        # Base delay adjusted by load
        delay = base_delay

        # If RPM is high, increase delay
        if rpm > 10:
            delay *= 1.5
        if rpm > 20:
            delay *= 2.0
        if rpm > 30:
            delay *= 3.0

        # If recent errors, increase delay exponentially
        if health["errors"] > 0:
            delay *= (1.5 ** health["errors"])

        # Cap at max delay
        return min(delay, MAX_DELAY_SECONDS)


def wait_for_slot(key_id: str, base_delay: float = BASE_DELAY_SECONDS) -> None:
    """Wait for an available request slot with adaptive delay."""
    delay = calculate_adaptive_delay(key_id, base_delay)
    # Add jitter to prevent thundering herd
    jitter = random.uniform(0.5, 1.5)
    actual_delay = delay * jitter
    time.sleep(actual_delay)


class RateLimiter:
    """Token bucket rate limiter for API calls."""

    def __init__(self, max_requests: int = MAX_CONCURRENT_REQUESTS, window_seconds: float = 60.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()
        self.lock = threading.Lock()

    def acquire(self) -> None:
        """Acquire a rate limit slot, blocking if necessary."""
        while True:
            with self.lock:
                now = time.time()
                # Remove expired requests
                while self.requests and self.requests[0] < now - self.window_seconds:
                    self.requests.popleft()

                if len(self.requests) < self.max_requests:
                    self.requests.append(now)
                    return

            # Wait a bit before retrying
            time.sleep(0.5)

    def release(self) -> None:
        """Release a slot (not strictly needed for token bucket but kept for API compatibility)."""
        pass


# Global rate limiter instance
_rate_limiter = RateLimiter()


def execute_with_rate_limit(
    func,
    api_keys: List[str],
    *args,
    base_delay: float = BASE_DELAY_SECONDS,
    max_retries: int = 3,
    **kwargs
) -> Any:
    """
    Execute a function with adaptive rate limiting and key rotation.

    Args:
        func: The function to execute
        api_keys: List of API keys to rotate through
        base_delay: Base delay between requests
        max_retries: Maximum retries per key
        *args, **kwargs: Arguments to pass to func

    Returns:
        Result of func or raises last exception
    """
    if not api_keys:
        raise ValueError("No API keys provided")

    last_exception = None

    for attempt in range(max_retries * len(api_keys)):
        key = get_healthy_key(api_keys)
        if not key:
            time.sleep(1)
            continue

        key_id = f"key_{api_keys.index(key)}"

        # Wait for rate limit slot
        _rate_limiter.acquire()
        wait_for_slot(key_id, base_delay)

        try:
            result = func(key, *args, **kwargs)
            record_request(key_id, True)
            return result
        except Exception as e:
            record_request(key_id, False, type(e).__name__)
            last_exception = e

            # Check if it's a rate limit error
            err_str = str(e).lower()
            is_rate_limit = any(kw in err_str for kw in [
                "429", "rate limit", "quota", "resource exhausted",
                "too many requests", "limit exceeded"
            ])

            if is_rate_limit:
                print(f"⚠️ [Efficiency] Rate limit hit on {key_id}, rotating key...")
                continue

            # For other errors, retry with same key up to max_retries
            key_health = _api_health.get(key_id, {})
            if key_health.get("errors", 0) < max_retries:
                time.sleep(base_delay * (attempt + 1))
                continue
            else:
                print(f"⚠️ [Efficiency] Key {key_id} failed {max_retries} times, rotating...")
                continue

    raise last_exception or Exception("All API keys exhausted")


def get_efficiency_report() -> Dict[str, Any]:
    """Generate a comprehensive efficiency report."""
    with _health_lock:
        stats = get_all_stats()
        total_requests = sum(len(s.get("request_times", [])) for s in stats.values())
        total_successes = sum(s.get("successes", 0) for s in stats.values())
        total_errors = sum(s.get("errors", 0) for s in stats.values())

        healthy_count = sum(1 for s in stats.values() if s.get("is_healthy", False))

        return {
            "total_keys": len(stats),
            "healthy_keys": healthy_count,
            "total_requests": total_requests,
            "total_successes": total_successes,
            "total_errors": total_errors,
            "success_rate": total_successes / max(1, total_requests) if total_requests > 0 else 0,
            "key_details": stats
        }


# Convenience function for Gemini API integration
def call_gemini_with_efficiency(
    prompt: str,
    api_keys: List[str],
    model: str = "gemini-2.5-flash",
    temperature: float = 0.7,
    response_mime_type: str = "application/json"
) -> Any:
    """
    Call Gemini API with efficiency engine protection.

    This is a wrapper that integrates with the existing call_gemini_api pattern.
    """
    from google import genai
    from google.genai import types
    import json

    def _call(key: str):
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                response_mime_type=response_mime_type
            )
        )
        raw = response.text.strip()
        if "```json" in raw:
            raw = raw[raw.find("```json")+7:raw.rfind("```")]
        elif "```" in raw:
            raw = raw[raw.find("```")+3:raw.rfind("```")]
        return json.loads(raw.strip())

    return execute_with_rate_limit(_call, api_keys)


if __name__ == "__main__":
    # Test the efficiency engine
    test_keys = ["test_key_1", "test_key_2", "test_key_3"]
    init_api_keys(test_keys)

    print("Testing efficiency engine...")
    print(f"Healthy key: {get_healthy_key(test_keys)}")
    print(f"Stats: {get_all_stats()}")
    print(f"Report: {get_efficiency_report()}")