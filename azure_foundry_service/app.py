"""
Azure AI Foundry Service
FastAPI application for predictions using 15 AutoML models
"""

import os
import json
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
from prediction_orchestrator import PredictionOrchestrator
from supabase_connector import SupabaseConnector

# Initialize FastAPI app
app = FastAPI(
    title="Azure AI Foundry Service",
    description="Prediction service with 15 AutoML models",
    version="1.0.0"
)

# Initialize components
try:
    orchestrator = PredictionOrchestrator()
    supabase = SupabaseConnector()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Azure AI Foundry Service initialized")
except Exception as e:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: Failed to initialize service: {e}")
    raise


# Request/Response models
class PredictionRequest(BaseModel):
    round_id: int
    round_number: int


class PredictionResponse(BaseModel):
    status: str
    signal_id: Optional[int] = None
    models_executed: int = 0
    ensemble_confidence: float = 0.0
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    models_loaded: int = 0
    supabase_connected: bool = False
    timestamp: str = ""
    error: Optional[str] = None


# API Endpoints

@app.get("/health", response_model=HealthResponse)
async def health():
    """
    Health check endpoint
    Returns service status and model availability
    """
    try:
        return HealthResponse(
            status="healthy",
            models_loaded=orchestrator.get_model_count(),
            supabase_connected=supabase.is_connected(),
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            models_loaded=0,
            supabase_connected=False,
            error=str(e),
            timestamp=datetime.now().isoformat()
        )


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Generate predictions from 15 AutoML models

    Args:
        request: PredictionRequest with round_id and round_number

    Returns:
        PredictionResponse with status, signal_id, models_executed, and ensemble_confidence
    """
    timestamp = datetime.now().strftime("%H:%M:%S")

    try:
        print(f"[{timestamp}] INFO: Prediction request for round {request.round_number}")

        # Step 1: Fetch 24-hour historical data from Supabase
        print(f"[{timestamp}] INFO: Fetching 24-hour historical data from Supabase...")
        historical_data = supabase.fetch_last_24h()

        if not historical_data:
            print(f"[{timestamp}] WARNING: No historical data available")
            return PredictionResponse(
                status="error",
                error="No historical data available"
            )

        print(f"[{timestamp}] INFO: Retrieved {len(historical_data)} rounds from last 24 hours")

        # Step 2: Run 15 models in parallel
        print(f"[{timestamp}] INFO: Running 15 AutoML models...")
        predictions = orchestrator.predict_all_models(historical_data)

        if not predictions:
            return PredictionResponse(
                status="error",
                error="Failed to generate predictions"
            )

        # Step 3: Build payload
        payload = {
            "modelPredictions": {
                "automl": predictions
            }
        }

        # Step 4: Calculate ensemble confidence
        confidences = [p['confidence'] for p in predictions]
        ensemble_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        # Step 5: Write to analytics_round_signals
        print(f"[{timestamp}] INFO: Writing predictions to analytics_round_signals...")
        signal_id = supabase.insert_analytics_signal(
            round_id=request.round_id,
            round_number=request.round_number,
            payload=payload
        )

        # Step 6: Return response
        print(f"[{timestamp}] SUCCESS: Prediction complete")
        print(f"[{timestamp}]   - Models: {len(predictions)}/15")
        print(f"[{timestamp}]   - Ensemble Confidence: {ensemble_confidence:.2%}")
        print(f"[{timestamp}]   - Signal ID: {signal_id}")

        return PredictionResponse(
            status="success",
            signal_id=signal_id,
            models_executed=len(predictions),
            ensemble_confidence=ensemble_confidence
        )

    except Exception as e:
        timestamp = datetime.now().strftime("%H:%M:%S")
        error_msg = str(e)
        print(f"[{timestamp}] ERROR: Prediction failed: {error_msg}")

        return PredictionResponse(
            status="error",
            error=error_msg
        )


@app.get("/status")
async def status():
    """Get detailed service status"""
    try:
        return {
            "status": "running",
            "service": "Azure AI Foundry",
            "version": "1.0.0",
            "models_loaded": orchestrator.get_model_count(),
            "model_names": list(orchestrator.models.keys()),
            "supabase_connected": supabase.is_connected(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/models")
async def list_models():
    """List all loaded models"""
    try:
        return {
            "total_models": orchestrator.get_model_count(),
            "models": list(orchestrator.models.keys()),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


# Error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle all exceptions"""
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Called on application startup"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{timestamp}] ===== Azure AI Foundry Service Started =====")
    print(f"[{timestamp}] Models Loaded: {orchestrator.get_model_count()}/15")
    print(f"[{timestamp}] Supabase Connected: {supabase.is_connected()}")
    print(f"[{timestamp}] Service Ready for Predictions")
    print(f"[{timestamp}] ==========================================\n")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Called on application shutdown"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{timestamp}] Azure AI Foundry Service Shutting Down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
