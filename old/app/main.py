from fastapi import FastAPI
from app.core.cors import add_cors
from app.core.config import settings
from app.routers import auth
from app.db.session import engine
from sqlalchemy import text
from app.routers import image_router, diffusion_router, settings_router, frame_router
import sys
import asyncio
import logging
import time

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")


# if sys.platform.startswith("win"):
#     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.getLogger(settings.APP_NAME)

app = FastAPI(title=settings.APP_NAME)
add_cors(app)

app.include_router(auth.router)
app.include_router(diffusion_router.router)
app.include_router(frame_router.router)

app.include_router(settings_router.router)



app.include_router(image_router.router)
@app.on_event("startup")
async def test_connection():
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✅ Database connected:", result.scalar())
    except Exception as e:
        print("❌ Database connection failed:", e)

@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 App is shutting down...")
    # close DB, release resources, etc.