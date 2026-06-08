"""Feature serving API — sub-10ms P99."""
from fastapi import FastAPI
import redis.asyncio as redis
import json, time

app = FastAPI(title="ML Feature Platform")
redis_client = None

@app.on_event("startup")
async def startup():
    global redis_client
    redis_client = await redis.from_url("redis://feature-store:6379", decode_responses=True)

@app.get("/features/{entity_id}")
async def get_features(entity_id: str, feature_groups: str = "all"):
    t0 = time.perf_counter()
    pipe = redis_client.pipeline()
    groups = feature_groups.split(",") if feature_groups != "all" else ["behavior","risk","affinity","context"]
    for g in groups:
        pipe.hgetall(f"features:{g}:{entity_id}")
    results = await pipe.execute()
    latency_ms = (time.perf_counter() - t0) * 1000
    features = {}
    for g, r in zip(groups, results):
        features[g] = {k: float(v) for k, v in r.items()}
    return {"entity_id": entity_id, "features": features, "latency_ms": round(latency_ms, 2)}
