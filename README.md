# Async Request Deduplication Service

A FastAPI-based server implementing an intelligent async request deduplication system with caching. This service prevents duplicate computation for concurrent requests with the same identifier while allowing different requests to run in parallel.

## 🚀 Features

- **Per-Key Request Deduplication**: Multiple concurrent requests with the same ID share a single computation
- **Parallel Processing**: Different request IDs run concurrently without blocking each other
- **Smart Caching**: Results are cached with configurable TTL (Time To Live)
- **Lock Management**: Per-request-key locks ensure thread safety without global blocking
- **Automatic Cache Cleanup**: Background task periodically removes expired cache entries
- **Status Monitoring**: Real-time visibility into active requests and cache status

## 📋 Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Architecture](#architecture)
- [How It Works](#how-it-works)
- [Testing](#testing)
- [Configuration](#configuration)

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- pip

### Setup

1. Clone the repository:
```bash
git clone https://github.com/vera-codes6/concurrent-fastapi-server.git
cd back_server
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## 🎯 Usage

### Starting the Server

Run the server using Python:
```bash
python -m main
```

Or using uvicorn directly:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The server will start on `http://localhost:8000`

### Basic Example

```bash
# Process a request with ID "task_A"
curl http://localhost:8000/process/task_A

# Check service status
curl http://localhost:8000/status
```

## 📡 API Endpoints

### `GET /process/{request_id}`

Process a request with deduplication.

**Parameters:**
- `request_id` (path): Unique identifier for the request

**Response:**
```json
{
  "success": true,
  "data": {
    "processed_data": "Processed: task_A",
    "timestamp": 1698470400.0,
    "processing_time": "10 seconds",
    "completion_time": "14:30:15"
  },
  "request_key": "task_A",
  "response_time": "10.02 seconds",
  "response_timestamp": "14:30:15"
}
```

**Behavior:**
- If the same `request_id` is requested multiple times concurrently, only one computation runs
- Subsequent identical requests wait for and share the result
- Cached results are returned instantly if still valid

### `GET /status`

Get current service status.

**Response:**
```json
{
  "active_requests": 2,
  "cached_results": 5,
  "active_keys": ["task_A", "task_B"],
  "cached_keys": ["task_A", "task_B", "task_C", "task_D", "task_E"],
  "locks": 2
}
```

### `GET /test-concurrent`

Test endpoint demonstrating concurrent request handling.

This endpoint makes multiple simultaneous requests to demonstrate:
- Deduplication of identical requests
- Parallel processing of different requests

## 🏗️ Architecture

### Project Structure

```
back_server/
├── main.py           # FastAPI application and endpoints
├── service.py        # AsyncRequestDeduplicationService implementation
├── model.py          # Data models (CachedResult)
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

### Core Components

#### 1. **AsyncRequestDeduplicationService** (`service.py`)

The heart of the deduplication system. Key features:

- **Per-Key Locking**: Each request key has its own lock, preventing global bottlenecks
- **Active Request Tracking**: Maintains a dictionary of ongoing computations
- **Result Caching**: Stores completed results with timestamps
- **Automatic Cleanup**: Manages lock and cache lifecycle

#### 2. **CachedResult** (`model.py`)

Simple data class for storing cached computation results with timestamps.

```python
@dataclass
class CachedResult:
    result: Any
    timestamp: float
```

#### 3. **FastAPI Application** (`main.py`)

REST API layer providing endpoints for request processing and monitoring.

## 🔍 How It Works

### Request Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Request A1 (ID: "task_A")                                  │
│  Request A2 (ID: "task_A")  ──┐                             │
│  Request B1 (ID: "task_B")  ──┼──> Deduplication Service    │
└───────────────────────────────┴─────────────────────────────┘
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
                ▼                ▼                ▼
         Per-Key Lock A    Per-Key Lock B    Cache Check
                │                │                │
                ▼                ▼                │
        Computation A     Computation B           │
          (10 sec)          (10 sec)              │
                │                │                │
                ▼                ▼                ▼
         ┌─────────────────────────────────────────┐
         │  A1, A2 share result ← Computation A    │
         │  B1 gets result      ← Computation B    │
         └─────────────────────────────────────────┘
```

### Deduplication Logic

1. **Request Arrives**: Client makes a request with a specific `request_id`
2. **Lock Acquisition**: Service acquires a lock for that specific `request_id`
3. **Active Check**: Checks if computation is already running for this ID
   - If yes: Wait for and reuse the existing computation
   - If no: Proceed to step 4
4. **Cache Check**: Check if cached result exists and is valid
   - If yes: Return cached result immediately
   - If no: Proceed to step 5
5. **New Computation**: Start new computation task
6. **Task Storage**: Store task reference for deduplication
7. **Computation**: Execute the heavy computation (10 seconds in demo)
8. **Caching**: Store result in cache with timestamp
9. **Cleanup**: Remove task from active requests, clean up lock if not needed

### Cache Management

- **TTL**: 300 seconds (5 minutes) by default
- **Background Cleanup**: Runs every 10 minutes
- **Automatic Expiry**: Old entries are automatically removed

## 🧪 Testing

### Manual Testing

1. **Test Deduplication** (same request ID):
```bash
# Open 3 terminals and run simultaneously:
# Terminal 1:
curl http://localhost:8000/process/test_task

# Terminal 2 (within 10 seconds):
curl http://localhost:8000/process/test_task

# Terminal 3 (within 10 seconds):
curl http://localhost:8000/process/test_task
```

**Expected**: Only one computation runs; all three requests get the same result.

2. **Test Parallel Processing** (different request IDs):
```bash
# Terminal 1:
curl http://localhost:8000/process/task_A

# Terminal 2 (simultaneously):
curl http://localhost:8000/process/task_B

# Terminal 3 (simultaneously):
curl http://localhost:8000/process/task_C
```

**Expected**: All three computations run in parallel, completing in ~10 seconds total.

3. **Test Caching**:
```bash
# First request
curl http://localhost:8000/process/cache_test

# Wait for completion (~10 seconds)

# Second request (immediately after)
curl http://localhost:8000/process/cache_test
```

**Expected**: First request takes 10 seconds; second request returns instantly from cache.

### Using the Test Endpoint

```bash
curl http://localhost:8000/test-concurrent
```

This endpoint automatically tests the concurrent processing and deduplication features.

## ⚙️ Configuration

### Cache Timeout

Modify the cache timeout when initializing the service:

```python
# In main.py
deduplication_service = AsyncRequestDeduplicationService(cache_timeout=600)  # 10 minutes
```

### Heavy Computation Duration

Modify the sleep duration in the `heavy_computation` function:

```python
# In main.py
async def heavy_computation(data: str) -> dict:
    await asyncio.sleep(10)  # Change this value
```

### Cleanup Interval

Modify the background cleanup interval:

```python
# In main.py
async def cleanup_task():
    while True:
        await asyncio.sleep(600)  # Change this value (in seconds)
        deduplication_service.cleanup_cache()
```

## 📊 Use Cases

This pattern is ideal for:

- **External API Calls**: Deduplicating calls to expensive third-party APIs
- **Database Queries**: Preventing redundant complex queries
- **ML Model Inference**: Sharing results for identical input data
- **File Processing**: Avoiding reprocessing the same files
- **Computation-Heavy Operations**: Any CPU/IO intensive tasks

## 🔧 Technical Details

### Dependencies

- **FastAPI**: Modern, fast web framework for building APIs
- **Uvicorn**: ASGI server for running FastAPI
- **aiohttp**: Async HTTP client/server framework
- **asyncio**: Python's built-in async/await support

### Python Version

- Requires Python 3.8+
- Uses modern async/await syntax
- Type hints for better code quality

## 📝 License

This project is available for use under standard open-source practices.

## 👨‍💻 Author

vera-codes6

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

## 📧 Contact

For questions or support, please open an issue in the repository.

---

**Note**: This is a demonstration project showing async request deduplication patterns. In production, consider:
- Adding authentication/authorization
- Implementing rate limiting
- Adding comprehensive error handling
- Setting up logging and monitoring
- Using environment variables for configuration
- Adding unit and integration tests
