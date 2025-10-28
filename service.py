import asyncio
import time
from typing import Dict, Any, Callable, Optional
from .model import CachedResult

class AsyncRequestDeduplicationService:
    def __init__(self, cache_timeout: int = 300):  # 5 minutes
        self.active_requests: Dict[str, asyncio.Task] = {}
        self.cache: Dict[str, CachedResult] = {}
        self.cache_timeout = cache_timeout
        self._locks: Dict[str, asyncio.Lock] = {}

    def _get_lock(self, request_key: str) -> asyncio.Lock:
        """Get or create a lock for a specific request key."""
        if request_key not in self._locks:
            self._locks[request_key] = asyncio.Lock()
        return self._locks[request_key]

    async def process_request(self, request_key: str, computation_fn: Callable) -> Any:
        """
        Process a request with deduplication PER REQUEST KEY.
        Different request keys run concurrently.
        Same request keys share computation.
        """
        # Use per-key lock instead of global lock
        lock = self._get_lock(request_key)
        
        async with lock:
            # Check if there's an active request for THIS SPECIFIC key
            if request_key in self.active_requests:
                task = self.active_requests[request_key]
                if not task.done():
                    print(f"Reusing active request for key: {request_key}")
                    return await task

            # Check cache for THIS SPECIFIC key
            cached = self.cache.get(request_key)
            if cached and time.time() - cached.timestamp < self.cache_timeout:
                print(f"Returning cached result for key: {request_key}")
                return cached.result

            # Create new task for THIS SPECIFIC key
            task = asyncio.create_task(
                self._execute_heavy_computation(request_key, computation_fn)
            )
            
            # Store the task for THIS SPECIFIC key
            self.active_requests[request_key] = task

        try:
            result = await task
            
            # Cache the result for THIS SPECIFIC key
            self.cache[request_key] = CachedResult(
                result=result,
                timestamp=time.time()
            )
            
            return result
        finally:
            # Remove from active requests when done
            async with lock:
                self.active_requests.pop(request_key, None)
                # Clean up lock if no longer needed
                if request_key in self._locks and request_key not in self.active_requests:
                    del self._locks[request_key]

    async def _execute_heavy_computation(self, request_key: str, computation_fn: Callable) -> Any:
        """Execute the heavy computation function."""
        print(f"[{time.strftime('%H:%M:%S')}] Starting heavy computation for key: {request_key}")
        
        try:
            result = await computation_fn()
            print(f"[{time.strftime('%H:%M:%S')}] Completed heavy computation for key: {request_key}")
            return result
        except Exception as error:
            print(f"[{time.strftime('%H:%M:%S')}] Error in heavy computation for key: {request_key}, error: {error}")
            raise

    def cleanup_cache(self):
        """Clean up old cache entries."""
        current_time = time.time()
        expired_keys = [
            key for key, cached in self.cache.items()
            if current_time - cached.timestamp >= self.cache_timeout
        ]
        for key in expired_keys:
            del self.cache[key]
        print(f"Cleaned up {len(expired_keys)} expired cache entries")

    def get_status(self) -> dict:
        """Get current service status."""
        return {
            "active_requests": len(self.active_requests),
            "cached_results": len(self.cache),
            "active_keys": list(self.active_requests.keys()),
            "cached_keys": list(self.cache.keys()),
            "locks": len(self._locks)
        }
