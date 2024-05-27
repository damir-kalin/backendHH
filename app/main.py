from fastapi import FastAPI

from model import core
from model.database import engine

from routers.parse import router as parse_router
from routers.exchange_rates import router as exchange_rates_router
from routers.metrics import router as metrics_router
from routers.skills import router as skills_router

# core.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(
    router=parse_router,
    prefix='/parse',
)

app.include_router(
    router=exchange_rates_router,
    prefix='/exchange_rates',
)

app.include_router(
    router=metrics_router,
    prefix='/metrics',
)

app.include_router(
    router=skills_router,
    prefix='/skills',
)