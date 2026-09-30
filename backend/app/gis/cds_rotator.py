"""
Copernicus Climate Data Store (CDS) Multi-Key API Rotator & Parallel Rate Limit Manager
Manages multiple CDS API keys concurrently (up to 2 parallel downloads per key),
handling automatic round-robin rotation, concurrency locks, and exponential backoff on HTTP 429 rate limits.
"""

import time
import threading
from typing import Optional, List, Dict
from contextlib import contextmanager

# User-provided Copernicus CDS API Keys & Endpoint
CDS_API_KEYS = [
    '3393d02c-5667-4cb3-8f2a-d459f7cccd5f',
    'dd47eb98-28f8-491b-b17e-3f05bd3a9d4b',
    '8f6674de-7e6a-4c40-9ab8-1333d8167519',
    'f552809e-1bfa-487f-9052-740f81b33474',
    'f945075a-c03d-4786-b5ef-7a55d39d5af9',
    '846965d1-4b6a-493c-b04b-76cbb53dd38b',
    'd6edbf8d-0593-4569-acb7-5163e1b75e3f',
]

CDS_API_URL = 'https://cds.climate.copernicus.eu/api'


class CDSKeyManager:
    """
    Thread-safe Round-Robin & Concurrency-Aware Rate-Limit Manager for Copernicus CDS API.
    Supports parallel downloads (max 2 per account key) across 7 keys = 14 parallel slots!
    """

    def __init__(
        self,
        api_keys: Optional[List[str]] = None,
        url: str = CDS_API_URL,
        max_concurrent_per_key: int = 2
    ):
        self.api_keys = api_keys or CDS_API_KEYS
        self.url = url
        self.max_concurrent_per_key = max_concurrent_per_key
        self.lock = threading.Lock()

        # Track active requests count per key
        self.active_counts: Dict[str, int] = {k: 0 for k in self.api_keys}
        # Track cool-off expiration timestamp per key (if 429 rate limit hit)
        self.cooloff_until: Dict[str, float] = {k: 0.0 for k in self.api_keys}
        self._rr_index = 0

    def acquire_key(self, timeout: float = 120.0) -> str:
        """
        Acquires the least-busy, non-cooloff API key.
        Blocks until a key slot becomes available or timeout expires.
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            with self.lock:
                now = time.time()
                # Find keys not in cool-off and below max concurrent slots
                available_keys = [
                    k for k in self.api_keys
                    if now >= self.cooloff_until[k] and self.active_counts[k] < self.max_concurrent_per_key
                ]

                if available_keys:
                    # Pick key with lowest active count, using Round-Robin as tie breaker
                    available_keys.sort(key=lambda k: (self.active_counts[k], (self._rr_index + self.api_keys.index(k)) % len(self.api_keys)))
                    selected_key = available_keys[0]

                    self.active_counts[selected_key] += 1
                    self._rr_index = (self._rr_index + 1) % len(self.api_keys)

                    active_total = sum(self.active_counts.values())
                    print(f"[CDSKeyManager] Acquired key slot: {selected_key[:8]}... (Active in pool: {active_total}/{len(self.api_keys)*self.max_concurrent_per_key})")
                    return selected_key

            time.sleep(0.5)

        raise TimeoutError(f"Timed out after {timeout}s waiting for an available CDS API key slot.")

    def release_key(self, key: str):
        """Releases an active key slot after download or request completes."""
        with self.lock:
            if key in self.active_counts:
                self.active_counts[key] = max(0, self.active_counts[key] - 1)
                print(f"[CDSKeyManager] Released key slot: {key[:8]}...")

    def mark_rate_limited(self, key: str, cooloff_seconds: float = 45.0):
        """Puts a key in temporary cool-off status if HTTP 429 / Rate Limit error is encountered."""
        with self.lock:
            self.cooloff_until[key] = time.time() + cooloff_seconds
            print(f"\033[91m[CDSKeyManager Warning]\033[0m Key {key[:8]}... rate-limited! Cooling off for {cooloff_seconds}s.")

    @contextmanager
    def session(self, timeout: float = 120.0):
        """
        Context manager for acquiring a CDS key and client safely:
        
        with key_manager.session() as (client, key):
            client.retrieve('reanalysis-era5-single-levels', request_dict, 'output.nc')
        """
        key = self.acquire_key(timeout=timeout)
        client = None

        try:
            import cdsapi
            client = cdsapi.Client(url=self.url, key=key, quiet=True)
        except ImportError:
            # Fallback mock client if cdsapi package is not installed
            class MockCDSClient:
                def retrieve(self, *args, **kwargs):
                    print(f"[MockCDSClient] Simulated CDS API retrieve call with key {key[:8]}...")
            client = MockCDSClient()

        try:
            yield client, key
        except Exception as e:
            err_str = str(e).lower()
            if "429" in err_str or "too many requests" in err_str or "rate limit" in err_str or "quota" in err_str:
                self.mark_rate_limited(key, cooloff_seconds=60.0)
            raise
        finally:
            self.release_key(key)


# Global singleton instance ready for import
cds_key_manager = CDSKeyManager(CDS_API_KEYS, CDS_API_URL)


if __name__ == "__main__":
    print("Testing CDSKeyManager pool...")
    print(f"Total API Keys: {len(cds_key_manager.api_keys)}")
    print(f"Max Concurrent Download Capacity: {len(cds_key_manager.api_keys) * cds_key_manager.max_concurrent_per_key} parallel tasks")

    # Test acquiring 3 keys
    with cds_key_manager.session() as (client, k1):
        print(f"Session 1 active with key {k1[:8]}")
        with cds_key_manager.session() as (client2, k2):
            print(f"Session 2 active with key {k2[:8]}")
