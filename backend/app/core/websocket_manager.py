"""
WebSocket Manager for Real-time Hospital Queue Updates
Broadcasts live events: Admissions, Promotions, Emergency Alarms, Doctor Calls
"""

import json
from typing import List
from fastapi import WebSocket

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, event_type: str, data: dict):
        """Gửi thông điệp thời gian thực đến toàn bộ màn hình đang kết nối"""
        payload = json.dumps({
            "event": event_type,
            "data": data
        }, default=str)
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception:
                disconnected.append(connection)

        for dead in disconnected:
            self.disconnect(dead)

ws_manager = WebSocketManager()
