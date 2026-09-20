from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
import requests
import threading

app = FastAPI(title="NEXUS-LUNAR Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print("UI Client connected to Gateway.")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print("UI Client disconnected.")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            print(f"Received from UI: {payload}")
            
            # TODO: Route commands to specific microservices (ai_brain, physics_engine, etc.)
            # For now, echo back a mocked processing acknowledgement
            
            response = {
                "type": "ACK",
                "message": f"Gateway received command: {payload.get('command')}",
                "status": "processing"
            }
            await manager.broadcast(json.dumps(response))
            
            # Mocking some fast PINN/AI response latency (milliseconds)
            await asyncio.sleep(0.05)
            
            if payload.get("command") == "RUN_MCTS":
                await manager.broadcast(json.dumps({"type": "MCTS_UPDATE", "iteration": 1, "best_score": 0.82}))
            elif payload.get("command") == "GET_THERMAL":
                await manager.broadcast(json.dumps({"type": "PINN_THERMAL_MAP", "avg_temp": 250, "max_stress": "42 MPa"}))
            elif payload.get("command") == "RENDER_INFRASTRUCTURE":
                # Forward to Blender Engine Microservice
                try:
                    def _call_blender():
                        return requests.post("http://localhost:8005/render/infrastructure", json={
                            "center_lat": payload.get("lat", -85.0),
                            "center_lon": payload.get("lon", 0.0),
                            "infrastructure_type": payload.get("type", "habitat"),
                            "solar_incidence_angle": payload.get("solar_angle", 45.0)
                        }, timeout=5)
                    
                    blender_res = await asyncio.to_thread(_call_blender)
                    if blender_res.status_code == 200:
                        data = blender_res.json()
                        await manager.broadcast(json.dumps({
                            "type": "RENDER_SUBMITTED", 
                            "job_id": data.get("job_id"),
                            "message": data.get("message")
                        }))
                    else:
                        await manager.broadcast(json.dumps({"type": "ERROR", "message": "Blender engine failed to process request."}))
                except Exception as e:
                    print(f"Error calling blender engine: {e}")
                    await manager.broadcast(json.dumps({"type": "ERROR", "message": "Blender engine offline or unreachable."}))

    except WebSocketDisconnect:
        manager.disconnect(websocket)

# --- SCIENCE INTELLIGENCE ENDPOINTS ---

from packages.science_engine.models import PhysicsResult, ChemistryResult, BiologyResult, ScienceIntelligenceResult, ScienceStatus, EvidenceStatus, ConfidenceScore
from packages.science_engine.physics.illumination import calculate_illumination
from packages.data_pipeline.models import ObservationGeometry
from packages.science_engine.provenance import create_provenance

def _get_mock_physics(region_id: str) -> PhysicsResult:
    # Example logic using the new engine. In a real system, we'd query the DB for the region.
    geom = ObservationGeometry(solar_zenith_deg=45.0, solar_azimuth_deg=120.0)
    illum = calculate_illumination(latitude=0.0, longitude=0.0, geometry=geom)
    return PhysicsResult(
        illumination_condition=illum.get("illumination_condition"),
        status=ScienceStatus.COMPLETE
    )

def _get_mock_chemistry(region_id: str) -> ChemistryResult:
    return ChemistryResult(status=ScienceStatus.INSUFFICIENT_DATA)

def _get_mock_biology(region_id: str) -> BiologyResult:
    return BiologyResult(status=ScienceStatus.INSUFFICIENT_DATA)

@app.get("/science/region/{region_id}/physics", response_model=PhysicsResult)
async def get_physics(region_id: str):
    return _get_mock_physics(region_id)

@app.get("/science/region/{region_id}/chemistry", response_model=ChemistryResult)
async def get_chemistry(region_id: str):
    return _get_mock_chemistry(region_id)

@app.get("/science/region/{region_id}/biology", response_model=BiologyResult)
async def get_biology(region_id: str):
    return _get_mock_biology(region_id)

@app.get("/science/region/{region_id}/fusion", response_model=ScienceIntelligenceResult)
@app.get("/science/region/{region_id}", response_model=ScienceIntelligenceResult)
async def get_science_fusion(region_id: str):
    from packages.science_engine.fusion import fuse_evidence
    physics = _get_mock_physics(region_id)
    chemistry = _get_mock_chemistry(region_id)
    biology = _get_mock_biology(region_id)
    prov = create_provenance(source="Gateway API mock", processing_method="None", derived=True)
    return fuse_evidence(region_id, physics, chemistry, biology, [prov])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
