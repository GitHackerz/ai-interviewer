# app.py
from fastapi import FastAPI, WebSocket
from aiortc import RTCPeerConnection, RTCSessionDescription
import json

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    pc = RTCPeerConnection()

    @pc.on("track")
    async def on_track(track):
        print(f"Received track: {track.kind}")
        if track.kind == "audio":
            while True:
                frame = await track.recv()
                # Process audio frames here (STT, etc.)

    while True:
        msg = await websocket.receive_text()
        data = json.loads(msg)

        if data["type"] == "offer":
            offer = RTCSessionDescription(sdp=data["sdp"], type=data["type"])
            await pc.setRemoteDescription(offer)
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)
            await websocket.send_text(json.dumps({
                "sdp": pc.localDescription.sdp,
                "type": pc.localDescription.type
            }))
