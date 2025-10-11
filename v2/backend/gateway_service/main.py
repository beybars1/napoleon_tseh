from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram
from prometheus_client.exposition import generate_latest
from starlette.responses import Response

app = FastAPI(title="Napoleon CRM Gateway")

# Метрики Prometheus
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене заменить на конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    REQUEST_COUNT.labels(method='GET', endpoint='/', status_code=200).inc()
    return {"message": "Napoleon CRM Gateway Service"}

@app.get("/health")
async def health_check():
    REQUEST_COUNT.labels(method='GET', endpoint='/health', status_code=200).inc()
    return {"status": "healthy"}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
