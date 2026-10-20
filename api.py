from fastapi import FastAPI

from estimator import load_models

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Hello token-cost-estimator"}


@app.get("/models")
def list_models(vendor: str | None = None):
    models = load_models()
    if vendor is None:
        return list(models.values())
    return [m for m in models.values() if m.vendor == vendor]


@app.get("/models/{name}")
def get_model(name: str):
    models = load_models()
    return models[name]
