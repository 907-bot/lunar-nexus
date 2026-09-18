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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
