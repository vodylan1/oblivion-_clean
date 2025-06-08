"""
concurrency_manager.py

Phase 5: Minimal concurrency scaffolding using Python threading.
We spawn a background thread for GodAwareness scanning while the main thread
executes synergy and reflection loops.
"""

import threading
import time

from core.god_awareness.god_awareness import scan_for_whale_activity

# Shared variable to store the latest whale alert
latest_whale_alert = {
    "whale_alert": False,
    "info": ""
}

def concurrency_manager_init():
    """Initialize concurrency manager (placeholder)."""
    print("[ConcurrencyManager] Initialized.")

def god_awareness_thread_func():
    """
    Background thread function that periodically scans for whale activity.
    """
    global latest_whale_alert
    while True:
        alert = scan_for_whale_activity()
        if alert["whale_alert"]:
            print(f"[GodAwareness Thread] ALERT: {alert['info']}")
            latest_whale_alert = alert
        else:
            latest_whale_alert = alert

        # Sleep before scanning again
        time.sleep(5)

def start_god_awareness_thread():
    """
    Create and start the background thread for God Awareness scanning.
    """
    t = threading.Thread(target=god_awareness_thread_func, daemon=True)
    t.start()
    print("[ConcurrencyManager] GodAwareness thread started (daemon).")
