from fastapi import FastAPI, Depends
import logging
from app.api.v1.api import api_router
from app.core.configs import settings
from app.core.lifespan import lifespan

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

app = FastAPI(
    title="Tarot",
    description="API | Tarot Online",
    version="1.0.0",
    contact={"url": "https://www.seusite.com"},
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
    lifespan=lifespan,
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {"message": "Bem-vindo ao Tarot Online!"}

