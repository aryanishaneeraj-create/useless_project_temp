"""
Legacy FastAPI Prototype.
For the active production server with computer vision detection, use backend/app.py.
"""
try:
    from fastapi import FastAPI
    from pydantic import BaseModel
except ImportError:
    pass

from backend.auditor import audit_item

app = FastAPI()


class Item(BaseModel):
    name: str
    x: float
    y: float


class AuditRequest(BaseModel):
    items: list[Item]


@app.get("/")
def home():

    return {
        "message": "Sadhya Item Placement Auditor is running!"
    }


@app.post("/audit")
def audit(request: AuditRequest):

    results = []

    for item in request.items:

        result = audit_item(
            item.name,
            item.x,
            item.y,
            1000,
            1000
        )

        results.append(result)

    correct = sum(
        1 for result in results
        if result["status"] == "correct"
    )

    total = len(results)

    if total > 0:
        score = round((correct / total) * 100)
    else:
        score = 0

    return {
        "score": score,
        "results": results
    }