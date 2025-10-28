from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import os

from app.rag.pipeline import planner
from app.ingest.build_index import build_index

from fastapi import FastAPI, HTTPException


app = FastAPI(title="LifeSync Lite API", version="0.2.0")

# CORS: open in dev; tighten in prod
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

class HealthProfile(BaseModel):
    age: Optional[int] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    restrictions: Optional[str] = None

class PlanRequest(BaseModel):
    goal: str = Field(..., description="User's goal (e.g., '3-day muscle gain plan under 2200 kcal')")
    profile: Optional[HealthProfile] = None

@app.get("/")
def root():
    # Serve the HTML frontend
    return FileResponse("index.html")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/plan")
def generate_plan(req: PlanRequest) -> Dict[str, Any]:
    enriched = req.goal
    if req.profile:
        tags = []
        if req.profile.age is not None:        tags.append(f"Age {req.profile.age}")
        if req.profile.weight_kg is not None:  tags.append(f"Weight {req.profile.weight_kg} kg")
        if req.profile.height_cm is not None:  tags.append(f"Height {req.profile.height_cm} cm")
        if req.profile.restrictions:           tags.append(f"Diet {req.profile.restrictions}")
        if tags:
            enriched += " | Profile: " + ", ".join(tags)
    
    # Convert profile to dict for the planner
    profile_dict = None
    if req.profile:
        profile_dict = {
            "age": req.profile.age,
            "weight_kg": req.profile.weight_kg,
            "height_cm": req.profile.height_cm,
            "restrictions": req.profile.restrictions
        }
    
    return planner.plan(enriched, profile_dict)

@app.post("/admin/reindex")
def reindex():
    build_index()
    return {"status": "ok", "message": "Index rebuilt"}

