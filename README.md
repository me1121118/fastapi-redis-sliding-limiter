# ⏱️ fastapi-redis-sliding-limiter

[![FastAPI](https://img.shields.io/badge/FastAPI-Supported-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Redis](https://img.shields.io/badge/Redis-Distributed-DC382D.svg?style=flat&logo=Redis&logoColor=white)](https://redis.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)]()

> A clean, distributed sliding-window rate limiter decorator for FastAPI with Redis and automatic in-memory fallback.

Protect your FastAPI routes from abuse, scrapers, and denial-of-service without heavy, complex configuration.

---

### ☕ Support My Studies / Buy Me a Coffee

Hey there! 👋 I build and open-source lightweight, focused developer tools.

If this small package helped protect your production API, please consider supporting my college/tuition fund:
- ☕ **Buy Me a Coffee:** [buymeacoffee.com/yourname](https://www.buymeacoffee.com)
- 💖 **Ko-fi:** [buymeacoffee.com/kcidi4148](https://buymeacoffee.com/kcidi4148)
- ⭐ **Star this repository** to help other developers discover it!

---

## 📦 Installation

```bash
pip install git+https://github.com/me1121118/fastapi-redis-sliding-limiter.git
```

---

## 🚀 Quick Example

```python
from fastapi import FastAPI, Request
from fastapi_redis_sliding_limiter import rate_limit, init_limiter

app = FastAPI()

# Optional: Connect to Redis for distributed cluster rate-limiting
# If omitted, it automatically uses local in-memory sliding window!
# import redis.asyncio as redis
# init_limiter(redis_client=redis.from_url("redis://localhost:6379"))

@app.get("/api/data")
@rate_limit(requests=5, window_seconds=60) # Max 5 requests per 60 seconds per IP
async def get_data(request: Request):
    return {"message": "Hello World"}
```

When the limit is exceeded, it automatically returns HTTP 429 with standard headers:
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 48
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 0

{"detail": "Too Many Requests. Please try again later."}
```

---

## 🧪 Testing

```bash
pytest -v tests
```

---

## 📄 License

MIT License. Free for personal and commercial use.
