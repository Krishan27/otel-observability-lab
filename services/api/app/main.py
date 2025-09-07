from fastapi import FastAPI, HTTPException  # Import FastAPI framework and HTTPException for error handling
from typing import Optional                 # Import Optional for optional query parameters
import logging, time, random                # Import logging, time, and random modules

# Set up logger for this API
logger = logging.getLogger("api")
logger.setLevel(logging.INFO)

# Create FastAPI app instance
app = FastAPI(title="api")

# Health check endpoint
@app.get("/health")
def health():
    logger.info("health check")  # Log health check
    return {"ok": True}          # Return simple JSON response

# Simulated work endpoint
@app.get("/work")
def work(ms: Optional[int] = None):
    # If ms is provided, use it as delay; otherwise, pick random delay between 200-400 ms
    delay = ms if ms is not None else random.randint(200, 400)
    t0 = time.time()  # Record start time (in seconds)
    time.sleep(delay / 1000.0)  # Sleep for 'delay' milliseconds (converted to seconds)
    took_ms = int((time.time() - t0) * 1000)  # Calculate elapsed time in milliseconds
    logger.info("work done", extra={"took_ms": took_ms})  # Log how long it took
    return {"ok": True, "took_ms": took_ms}  # Return result as JSON

# Error simulation endpoint
@app.get("/error")
def error():
    try:
        raise ValueError("simulated failure")  # Intentionally raise an error
    except Exception as e:
        logger.exception("error endpoint failed")  # Log the exception with stack trace
        # Return HTTP 500 error with message
        raise HTTPException(status_code=500, detail="internal error") from e