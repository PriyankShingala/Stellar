import asyncio
import cv2
import json
import logging
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Any
import time

from ai.inference.pose_estimator import PoseEstimator
from ai.inference.object_detector import ObjectDetector
from ai.inference.interaction_reasoner import InteractionReasoner
from ai.sequence_validator.sequence_validator import SequenceValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StellarServer")

app = FastAPI(title="Stellar AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State
class MissionState:
    def __init__(self):
        self.is_running = False
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logs: List[Dict[str, str]] = []
        
        self.pose_estimator = None
        self.object_detector = None
        self.interaction_reasoner = None
        self.sequence_validator = None
        
        self.cap = None
        self.current_frame = None
        self.latest_telemetry = {}
        self.active_protocol = None
        
        self.clients: List[WebSocket] = []

    def init_ai(self):
        if not self.pose_estimator:
            self.pose_estimator = PoseEstimator(min_detection_confidence=0.5, min_tracking_confidence=0.5)
            # Use permissive detection with high sensitivity and extended persistence
            self.object_detector = ObjectDetector(
                conf_threshold=0.15,
                glass_conf_threshold=0.15,
                bottle_conf_threshold=0.15,
                bottle_persistence_frames=20,
                glass_persistence_frames=20
            )
            self.interaction_reasoner = InteractionReasoner()
            self.sequence_validator = SequenceValidator()

    def reset(self):
        self.init_ai()
        if self.sequence_validator:
            self.sequence_validator.reset()
        if self.interaction_reasoner:
            self.interaction_reasoner.reset()
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logs = []
        curr_step = self.sequence_validator.state_machine.get_current_step() if self.sequence_validator else None
        self.latest_telemetry = {
            "type": "telemetry",
            "data": {
                "step_index": 0,
                "is_completed": False,
                "current_step_name": curr_step.get("action_name") if curr_step else "bottle_pickup",
                "active_states": [],
                "objects": {}
            }
        }
        asyncio.create_task(self.broadcast(self.latest_telemetry))
        self.add_log("SYSTEM", "Experiment reset.")

    def add_log(self, event: str, message: str):
        log_entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "event": event,
            "message": message
        }
        self.logs.append(log_entry)
        asyncio.create_task(self.broadcast({"type": "log_update", "data": log_entry}))

    async def broadcast(self, message: dict):
        dead_clients = []
        for client in self.clients:
            try:
                await client.send_json(message)
            except Exception:
                dead_clients.append(client)
        for client in dead_clients:
            self.clients.remove(client)

state = MissionState()

async def pipeline_loop():
    logger.info("Starting AI Pipeline Loop")
    await asyncio.to_thread(state.init_ai)
    
    if state.cap is None or not state.cap.isOpened():
        state.cap = await asyncio.to_thread(cv2.VideoCapture, 0)
    
    if not state.cap.isOpened():
        logger.error("Camera failed to open.")
        await state.broadcast({"type": "error", "message": "Camera unavailable"})
        state.is_running = False
        return

    # Warmup
    for _ in range(5):
        await asyncio.to_thread(state.cap.read)

    def run_ai_and_draw(f):
        pose = state.pose_estimator.estimate_pose(f)
        dets = state.object_detector.detect(f)
        ro = state.interaction_reasoner.update(pose, dets)
        ve = state.sequence_validator.process_interaction(ro)
        
        ann = f.copy()
        state.pose_estimator.draw_landmarks(ann, pose, draw_rack_bounds=False)
        state.object_detector.draw_detections(ann, dets)
        
        # Telemetry HUD directly on video stream
        h, w = ann.shape[:2]
        curr_step = state.sequence_validator.state_machine.get_current_step()
        step_str = f"STEP 0{curr_step['step_number']}: {curr_step['action_name'].upper()}" if curr_step else "ALL STEPS COMPLETED"
        is_p = "pouring" in ro.get("active_states", [])
        hud_txt = f"{step_str} | POURING: {'ACTIVE' if is_p else 'NO'}"
        hud_col = (0, 255, 127) if is_p else (0, 215, 255)
        cv2.putText(ann, hud_txt, (16, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, hud_col, 2, cv2.LINE_AA)
        
        _, buf = cv2.imencode('.jpg', ann)
        return ro, ve, buf.tobytes()

    while state.is_running:
        ret, frame = await asyncio.to_thread(state.cap.read)
        if not ret or frame is None:
            logger.error("Camera disconnected.")
            await state.broadcast({"type": "error", "message": "Camera disconnected"})
            break

        # AI Inference offloaded
        reasoner_output, validator_events, frame_bytes = await asyncio.to_thread(run_ai_and_draw, frame)
        
        state.current_frame = frame_bytes

        # Log events
        for res in validator_events:
            evt = res.get("event")
            valid = res.get("valid")
            msg = res.get("status_message", "")
            
            if valid:
                state.add_log(evt, f"Success: {msg}")
            else:
                dev = res.get("deviation_type")
                if dev not in ("ALREADY_COMPLETED", "CASCADE_GUARD_HELD"):
                    state.add_log(dev, f"Deviation: {msg}")

        # Build telemetry payload
        curr_step_dict = state.sequence_validator.state_machine.get_current_step()
        
        state.latest_telemetry = {
            "type": "telemetry",
            "data": {
                "step_index": state.sequence_validator.state_machine.current_step_index,
                "is_completed": state.sequence_validator.state_machine.is_completed(),
                "current_step_name": curr_step_dict.get("action_name") if curr_step_dict else "COMPLETED",
                "active_states": reasoner_output.get("active_states", []),
                "objects": reasoner_output.get("interactions", {})
            }
        }
        
        await state.broadcast(state.latest_telemetry)
        await asyncio.sleep(0.01) # Yield to event loop

    logger.info("Pipeline loop stopped.")
    if state.cap:
        state.cap.release()
        state.cap = None

@app.get("/status")
async def get_status():
    return {"status": "ok", "is_running": state.is_running}

@app.get("/log/{run_id}")
async def get_log(run_id: str):
    return {"run_id": state.run_id, "logs": state.logs}

@app.post("/experiment/select")
async def select_experiment(payload: dict):
    protocol_id = payload.get("protocol_id")
    state.active_protocol = protocol_id
    state.reset()
    state.add_log("SYSTEM", f"Selected Protocol: {protocol_id}")
    return {"status": "ok", "protocol_id": protocol_id}

@app.post("/experiment/reset")
async def reset_experiment():
    state.reset()
    return {"status": "ok"}

@app.post("/experiment/start")
async def start_experiment():
    state.reset()
    if not state.is_running:
        state.is_running = True
        state.add_log("SYSTEM", "Experiment Started.")
        asyncio.create_task(pipeline_loop())
    return {"status": "ok"}

@app.post("/experiment/stop")
async def stop_experiment():
    state.is_running = False
    state.add_log("SYSTEM", "Experiment Stopped.")
    return {"status": "ok"}

@app.get("/stream/config")
async def get_stream_config():
    return {"camera_index": 0, "resolution": "640x480"}

@app.websocket("/ws/status")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    state.clients.append(websocket)
    try:
        # Send initial state
        if state.latest_telemetry:
            await websocket.send_json(state.latest_telemetry)
        for log in state.logs:
            await websocket.send_json({"type": "log_update", "data": log})
        
        while True:
            await websocket.receive_text() # keep-alive
    except WebSocketDisconnect:
        if websocket in state.clients:
            state.clients.remove(websocket)

async def generate_frames():
    last_frame_time = 0
    while True:
        if state.current_frame:
            # Yield the frame
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + state.current_frame + b'\r\n')
        await asyncio.sleep(0.03)

@app.get("/video_feed")
async def video_feed():
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

# Serve the web frontend last
app.mount("/", StaticFiles(directory="web", html=True), name="web")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.server:app", host="0.0.0.0", port=8000, reload=True)
