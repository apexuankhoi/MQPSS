"""
FastAPI Main Application for MQPSS
Emergency Triage & Multilevel Queue Priority Scheduling System
"""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.core.config import settings
from backend.app.api.endpoints import router as api_router
from backend.app.core.websocket_manager import ws_manager
from backend.app.services.scheduler_service import scheduler_service

async def aging_background_loop():
    """Vòng lặp quét aging định kỳ mỗi 15 giây"""
    while True:
        try:
            await asyncio.sleep(15)
            promotions = scheduler_service.run_aging()
            if promotions:
                await ws_manager.broadcast("AGING_PROMOTIONS", {
                    "promotions": promotions,
                    "snapshot": scheduler_service.get_snapshot()
                })
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Quản lý vòng đời ứng dụng FastAPI với async lifespan handler"""
    aging_task = asyncio.create_task(aging_background_loop())
    yield
    aging_task.cancel()
    try:
        await aging_task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Hệ thống Phân Loại & Lập Lịch Bệnh Nhân Cấp Cứu theo Thuật Toán Multilevel Queue & Priority Scheduling",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware cho kết nối Web & Mobile client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký REST API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# WebSocket Endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        # Gửi ngay snapshot ban đầu khi vừa kết nối
        await websocket.send_json({
            "event": "INITIAL_STATE",
            "data": {
                "snapshot": scheduler_service.get_snapshot()
            }
        })
        while True:
            # Lắng nghe ping từ client để giữ kết nối
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


# Mount Frontend & Simulation static files
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
SIMULATIONS_DIR = Path(__file__).resolve().parent.parent.parent / "simulations"

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    def serve_frontend():
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"status": "ONLINE", "message": "MQPSS API is running. Frontend folder is ready."}
else:
    @app.get("/")
    def root():
        return {
            "status": "ONLINE",
            "project": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "docs": "/docs"
        }

if SIMULATIONS_DIR.exists():
    app.mount("/simulations", StaticFiles(directory=str(SIMULATIONS_DIR)), name="simulations")

