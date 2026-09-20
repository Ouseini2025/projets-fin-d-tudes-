from fastapi import APIRouter

from app.api.routes import auth, catalog, commerce, health, stock, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(catalog.router)
api_router.include_router(stock.router)
api_router.include_router(commerce.r)
