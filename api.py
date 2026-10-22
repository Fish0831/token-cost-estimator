from fastapi import FastAPI

from estimator import estimate_monthly_cost, load_models
from schemas import EstimateRequest, EstimateResponse, ModelInfo

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Hello token-cost-estimator"}


@app.get("/models", response_model=list[ModelInfo])
def list_models(vendor: str | None = None):
    models = load_models()
    if vendor is None:
        return list(models.values())
    return [m for m in models.values() if m.vendor == vendor]


@app.get("/models/{name}", response_model=ModelInfo)
def get_model(name: str):
    models = load_models()
    return models[name]


@app.post("/estimate", response_model=EstimateResponse)
def estimate(request: EstimateRequest):
    cost = estimate_monthly_cost(**request.model_dump())
    return EstimateResponse(
        model=request.model,
        days=request.days,
        monthly_cost=round(cost, 2),
    )
