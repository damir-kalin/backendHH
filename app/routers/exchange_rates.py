from fastapi import APIRouter
from internal.exchange_rates import run_parse

from logger import logger


exchange_rates_router = APIRouter()

@exchange_rates_router.post("/")
def exchange_rates(date: str = None):
    logger.info(f"The task of parsing data from the Central Bank of the Russian Federation API is launched.Parameters: date-{date}.")
    run_parse(date)