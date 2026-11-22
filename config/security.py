"""Small cache-backed throttling helpers (no extra dependency required)."""

import time

from django.core.cache import cache


def throttle_blocked(key, limit, window_seconds):
    """True when this key has already reached its allowed attempt count."""
    state = cache.get(key)
    if not state:
        return False
    if state['reset'] <= time.monotonic():
        cache.delete(key)
        return False
    return state['count'] >= limit


def throttle_hit(key, window_seconds):
    """Record one failed attempt for a key."""
    state = cache.get(key)
    if not state or state['reset'] <= time.monotonic():
        state = {'count': 0, 'reset': time.monotonic() + window_seconds}
    state['count'] += 1
    cache.set(key, state, window_seconds)


def throttle_reset(key):
    cache.delete(key)


def client_ip(request):
    return request.META.get('REMOTE_ADDR', 'unknown')[:64]
