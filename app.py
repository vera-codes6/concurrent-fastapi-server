import asyncio
import time
from fastapi import FastAPI, HTTPException
from .service import AsyncRequestDeduplicationService

# FastAPI application
app = FastAPI()
deduplication_service = AsyncRequestDeduplicationService()

async def heavy_computation(data: str) -> dict:
    """Simulate heavy computation that takes 10 seconds."""
    print(f"[{time.strftime('%H:%M:%S')}] Processing data: {data}")
    await asyncio.sleep(10)  # Simulate 10 second processing time
    
    return {
        "processed_data": f"Processed: {data}",
        "timestamp": time.time(),
        "processing_time": "10 seconds",
        "completion_time": time.strftime('%H:%M:%S')
    }

@app.get("/process/{request_id}")
async def process_endpoint(request_id: str):
    """
    Endpoint that handles heavy computation with deduplication.
    
    Test scenarios:
    - /process/A and /process/B will run concurrently
    - /process/A and /process/A will share the same computation
    """
    try:
        start_time = time.time()
        result = await deduplication_service.process_request(
            request_id,
            lambda: heavy_computation(request_id)
        )
        
        return {
            "success": True,
            "data": result,
            "request_key": request_id,
            "response_time": f"{time.time() - start_time:.2f} seconds",
            "response_timestamp": time.strftime('%H:%M:%S')
        }
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))

@app.get("/status")
async def status():
    """Get service status."""
    return deduplication_service.get_status()

@app.get("/test-concurrent")
async def test_concurrent():
    """
    Test endpoint to demonstrate concurrent processing.
    This will start multiple requests simultaneously.
    """
    import aiohttp
    
    async def make_request(session, request_id):
        async with session.get(f"http://localhost:8000/process/{request_id}") as response:
            return await response.json()
    
    async with aiohttp.ClientSession() as session:
        # Start multiple requests concurrently
        tasks = [
            make_request(session, "task_A"),
            make_request(session, "task_B"), 
            make_request(session, "task_A"),  # This should reuse task_A
            make_request(session, "task_C"),
            make_request(session, "task_B"),  # This should reuse task_B
        ]
        
        results = await asyncio.gather(*tasks)
        return {
            "message": "Concurrent test completed",
            "results": results
        }

# Background task to cleanup cache
async def cleanup_task():
    while True:
        await asyncio.sleep(600)  # Run every 10 minutes
        deduplication_service.cleanup_cache()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_task())