from datetime import datetime, timedelta
from fastapi import APIRouter

from internal.parse import run_parse
from logger import logger



parse_router = APIRouter()
yesterday = str((datetime.now() - timedelta(days=1)).date())

@parse_router.post("/")
def parse(profession:str, date:str = yesterday, page:int = 0, per_page:int = 100, area:int = 113):
    logger.info(f"The task of parsing data from the HH API is launched..Parameters: profession-{profession}, date-{date}, page-{page}, per_page-{per_page}, area-{area}.")
    run_parse(profession, date, page, per_page, area)
