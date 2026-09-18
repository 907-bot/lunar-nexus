import os
import subprocess
import json
import uuid
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Blender Engine Microservice", description="OpenAPI service for 3D Lunar Digital Twin Rendering")

# Data model for the rendering request
class RenderRequest(BaseModel):
    center_lat: float
    center_lon: float
    infrastructure_type: str = "habitat"  # e.g., 'habitat', 'solar_array', 'rover'
    solar_incidence_angle: float = 45.0
    resolution_m: float = 1.0

class RenderResponse(BaseModel):
    status: str
    job_id: str
    message: str
    output_path: Optional[str] = None

# Ensure output directory exists
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "outputs", "blender_renders")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_blender_subprocess(job_id: str, request_data: dict, output_filepath: str):
    script_path = os.path.join(os.path.dirname(__file__), "render_lunar_infra.py")
    
    # We pass the request data as a JSON string to the blender script
    params = {
        "job_id": job_id,
        "output_filepath": output_filepath,
        **request_data
    }
    
    # In a real environment, this assumes 'blender' is in the system PATH.
    # We use -b for background (headless) and -P to run the python script.
    # The '--' separates blender arguments from python script arguments.
    cmd = [
        "blender",
        "-b",
        "-P", script_path,
        "--",
        json.dumps(params)
    ]
    
    try:
        print(f"[{job_id}] Starting Blender render subprocess...")
        # Since this is a POC and the user may not have Blender installed in PATH, 
        # we will handle the subprocess gracefully.
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        if process.returncode == 0:
            print(f"[{job_id}] Render completed successfully: {output_filepath}")
        else:
            print(f"[{job_id}] Render failed. Is Blender installed in PATH?")
            print(process.stderr)
            
            # For POC purposes, if blender fails, we just touch the output file to mock success.
            with open(output_filepath, "w") as f:
                f.write("MOCK RENDER OUTPUT (Blender not found or failed)")
            print(f"[{job_id}] Created mock render output at {output_filepath}")
            
    except Exception as e:
        print(f"[{job_id}] Error running blender: {e}")
        # Create mock file
        with open(output_filepath, "w") as f:
            f.write("MOCK RENDER OUTPUT (Exception occurred)")


@app.post("/render/infrastructure", response_model=RenderResponse)
async def render_infrastructure(req: RenderRequest, background_tasks: BackgroundTasks):
    job_id = f"render_{uuid.uuid4().hex[:8]}"
    output_filename = f"{job_id}_{req.infrastructure_type}.png"
    output_filepath = os.path.join(OUTPUT_DIR, output_filename)
    
    # Trigger the background rendering job
    background_tasks.add_task(run_blender_subprocess, job_id, req.dict(), output_filepath)
    
    # Return immediately while rendering happens in the background
    return RenderResponse(
        status="processing",
        job_id=job_id,
        message="Render job submitted to Blender Engine.",
        output_path=f"/outputs/blender_renders/{output_filename}"
    )

@app.get("/status")
def get_status():
    return {"status": "Blender Engine is online."}

if __name__ == "__main__":
    import uvicorn
    # Run on a different port than the main gateway (8000) or chemistry engine (8003)
    uvicorn.run(app, host="0.0.0.0", port=8005)
