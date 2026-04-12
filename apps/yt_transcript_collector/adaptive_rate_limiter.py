from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass


@dataclass
class LimiterSnapshot:
    base_interval_seconds: float
    current_penalty_seconds: float
    consecutive_429s: int
    consecutive_successes: int
    current_multiplier: float


class AdaptiveRateLimiter:
    """
    Adaptive request limiter for scraper-like workloads.

    Goals:
    - keep a minimum spacing between requests
    - increase spacing aggressively after 429s
    - recover gradually after successes
    - support different request weights (light/heavy)
    - be safe to call from multiple threads if needed later
    """

    def __init__(
        self,
        *,
        base_interval_seconds: float = 2.0,
        max_interval_seconds: float = 180.0,
        success_decay: float = 0.85,
        min_penalty_seconds: float = 0.0,
        penalty_step_seconds: float = 8.0,
        max_penalty_seconds: float = 300.0,
        multiplier_on_429: float = 1.8,
        max_multiplier: float = 12.0,
        jitter_ratio: float = 0.20,
        recovery_success_threshold: int = 3,
    ) -> None:
        self.base_interval_seconds = max(0.0, base_interval_seconds)
        self.max_interval_seconds = max(self.base_interval_seconds, max_interval_seconds)
        self.success_decay = min(max(success_decay, 0.01), 0.999)
        self.min_penalty_seconds = max(0.0, min_penalty_seconds)
        self.penalty_step_seconds = max(0.0, penalty_step_seconds)
        self.max_penalty_seconds = max(self.min_penalty_seconds, max_penalty_seconds)
        self.multiplier_on_429 = max(1.0, multiplier_on_429)
        self.max_multiplier = max(1.0, max_multiplier)
        self.jitter_ratio = min(max(jitter_ratio, 0.0), 1.0)
        self.recovery_success_threshold = max(1, recovery_success_threshold)

        self._lock = threading.Lock()
        self._next_allowed_time = 0.0
        self._current_penalty_seconds = self.min_penalty_seconds
        self._current_multiplier = 1.0
        self._consecutive_429s = 0
        self._consecutive_successes = 0

    def _compute_effective_interval(self, weight: float) -> float:
        weighted_base = self.base_interval_seconds * max(1.0, weight)
        interval = (weighted_base * self._current_multiplier) + self._current_penalty_seconds
        return min(interval, self.max_interval_seconds)

    def _apply_jitter(self, seconds: float) -> float:
        if seconds <= 0 or self.jitter_ratio <= 0:
            return seconds
        delta = seconds * self.jitter_ratio
        return max(0.0, random.uniform(seconds - delta, seconds + delta))

    def acquire_delay(self, *, weight: float = 1.0) -> float:
        """
        Reserve the next request slot and return how long the caller should sleep.
        """
        now = time.monotonic()
        with self._lock:
            effective_interval = self._compute_effective_interval(weight)
            target_time = max(now, self._next_allowed_time)
            delay = max(0.0, target_time - now)
            delay = self._apply_jitter(delay)

            # Reserve the following slot based on current state.
            reserve_from = max(now + delay, self._next_allowed_time)
            self._next_allowed_time = reserve_from + effective_interval

            return delay

    def sleep_if_needed(self, *, weight: float = 1.0, logger=None, reason: str | None = None) -> float:
        delay = self.acquire_delay(weight=weight)
        if delay > 0:
            if logger is not None:
                if reason:
                    logger.info("Adaptive limiter sleeping %.2f seconds before %s", delay, reason)
                else:
                    logger.info("Adaptive limiter sleeping %.2f seconds", delay)
            time.sleep(delay)
        return delay

    def record_success(self) -> None:
        with self._lock:
            self._consecutive_successes += 1
            self._consecutive_429s = 0

            # Decay penalty every success
            self._current_penalty_seconds = max(
                self.min_penalty_seconds,
                self._current_penalty_seconds * self.success_decay,
            )

            # Recover multiplier more slowly
            if self._consecutive_successes >= self.recovery_success_threshold:
                self._current_multiplier = max(
                    1.0,
                    self._current_multiplier * self.success_decay,
                )

    def record_rate_limit(self) -> None:
        with self._lock:
            self._consecutive_429s += 1
            self._consecutive_successes = 0

            self._current_penalty_seconds = min(
                self.max_penalty_seconds,
                self._current_penalty_seconds + self.penalty_step_seconds * self._consecutive_429s,
            )

            self._current_multiplier = min(
                self.max_multiplier,
                self._current_multiplier * self.multiplier_on_429,
            )

            # Push future requests out immediately
            now = time.monotonic()
            forced_gap = min(
                self.max_interval_seconds,
                (self.base_interval_seconds * self._current_multiplier) + self._current_penalty_seconds,
            )
            self._next_allowed_time = max(self._next_allowed_time, now + forced_gap)

    def snapshot(self) -> LimiterSnapshot:
        with self._lock:
            return LimiterSnapshot(
                base_interval_seconds=self.base_interval_seconds,
                current_penalty_seconds=self._current_penalty_seconds,
                consecutive_429s=self._consecutive_429s,
                consecutive_successes=self._consecutive_successes,
                current_multiplier=self._current_multiplier,
            )

    def format_state(self) -> str:
        s = self.snapshot()
        return (
            f"base={s.base_interval_seconds:.2f}s "
            f"penalty={s.current_penalty_seconds:.2f}s "
            f"multiplier={s.current_multiplier:.2f} "
            f"successes={s.consecutive_successes} "
            f"rate_limits={s.consecutive_429s}"
        )