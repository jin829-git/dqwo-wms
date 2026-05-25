"""
main.py — FastAPI 应用入口
启动命令：uvicorn main:app --host 0.0.0.0 --port 8000 --reload

"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.core.config import settings
from app.core.init_db import init_db
from app.routers import auth, users, fields, inventory, archive, analysis, config, change_requests

# ── 应用初始化 ──────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="库房物资管理系统 API — 使用 /docs 查看接口文档",
    # docs_url=None
)

# ── 跨域（CORS）────────────────────────────
app.add_middleware(
    CORSMiddleware,
    # allow_origins =[  "http://localhost:8000",
    #     "http://127.0.0.1:8000"]

    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 注册路由 ────────────────────────────────
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(fields.router)
app.include_router(inventory.router)
app.include_router(archive.router)
app.include_router(analysis.router)
app.include_router(config.router)
app.include_router(change_requests.router)

# ── 静态文件（前端 HTML）────────────────────
# 将前端 HTML 文件放到 static/ 目录下即可通过浏览器访问
STATIC_DIR = "static"
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def serve_frontend():
        index = os.path.join(STATIC_DIR, "index.html")
        if os.path.exists(index):
            return FileResponse(index)
        return {"msg": "请将前端 HTML 放入 static/index.html"}

    @app.get("/sw.js", include_in_schema=False)
    def serve_sw():
        sw_path = os.path.join(STATIC_DIR, "sw.js")
        if os.path.exists(sw_path):
            return FileResponse(sw_path, media_type="application/javascript")
        return {"msg": "sw.js not found"}


@app.get("/api/health", tags=["系统"])
def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


# ── 启动时初始化数据库 ──────────────────────
@app.on_event("startup")
def on_startup():
    os.makedirs("data", exist_ok=True)
    init_db()
