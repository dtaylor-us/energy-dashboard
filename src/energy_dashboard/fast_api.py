import asyncio
import logging
import typing
from typing import Annotated

import httpx
from fastapi import Depends, Body, Form, FastAPI, Request, Query
from fastapi.exceptions import RequestValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse, JSONResponse, HTMLResponse
from starlette.templating import Jinja2Templates

from energy_dashboard.database import SessionLocal, AsyncSessionLocal
from energy_dashboard.models import RetrieveEnergyDataRequest, SeedEnergyDataRequest
from energy_dashboard.services import EnergyDataService
from energy_dashboard.sql_alchemy import Session

app = FastAPI()


# Dependency function to get an instance of the database
## Async db: https://fastapi.tiangolo.com/tutorial/dependencies/
async def get_async_db():
    async_db = AsyncSessionLocal()
    try:
        yield async_db
    finally:
        await async_db.close()


## Sync db
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Dependency function to get an instance of EnergyDataService
def get_energy_service(
    db: Session = Depends(get_db), async_db: AsyncSession = Depends(get_async_db)
):
    return EnergyDataService(async_db, db, httpx.AsyncClient())


def app_context(request: Request) -> typing.Dict[str, typing.Any]:
    return {"app": request.app}


templates = Jinja2Templates(
    directory="templates",
)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="fast_api.jinja2",
    )


def app_context(request: Request) -> typing.Dict[str, typing.Any]:
    return {"app": request.app}


@app.get("/energy_data", name="energy_data", response_class=HTMLResponse)
async def get_energy_data(
    request: Request,
    respondent: str = Query(...),
    type_name: str = Query(...),
    start_date: str = Query(...),
    end_date: str = Query(...),
    service: EnergyDataService = Depends(get_energy_service),
):
    """
    Endpoint to get energy data based on the provided parameters.

    Parameters:
    respondent (str): The respondent for the data entry.
    type_name (str): The type_name of the data entry.
    start_date (str): The start date for the data entry.
    end_date (str): The end date for the data entry.
    service (EnergyDataService): The service to fetch the data.

    Returns:
    JSONResponse: The energy data.
    """

    if not all([respondent, type_name, start_date, end_date]):
        return JSONResponse(
            status_code=400,
            content={"message": "All parameters must be provided"},
        )

    params = RetrieveEnergyDataRequest(
        respondent=respondent,
        type_name=type_name,
        start_date=start_date,
        end_date=end_date,
    )

    data = await service.list_all(None, params)

    return templates.TemplateResponse(
        request=request,
        name="fast_api.jinja2",
        context={"energy_data": data},
    )


@app.get(
    "/api/v1/stream-energy-data",
    name="stream-energy-data",
    response_class=StreamingResponse,
)
async def stream_energy_data(service: EnergyDataService = Depends(get_energy_service)):
    """
    Stream the energy data as Server-Sent Events (SSE).

    Parameters:
    service (EnergyDataService): The service to fetch the data.

    Returns:
    StreamingResponse: The energy data as SSE.
    """

    async def streaming_data():
        strm = service.stream_all()
        async for data in strm:
            yield f"data: {data.model_dump_json(indent=4)}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(streaming_data(), media_type="text/event-stream")


@app.post("/api/v1/seed-data/")
async def seed_energy_data(
    request_body: SeedEnergyDataRequest = Body(...),
    service: EnergyDataService = Depends(get_energy_service),
):
    """
    Endpoint to seed energy data based on the provided parameters.

    Parameters:
    request_body (SeedEnergyDataRequest): The request body containing the parameters.
    service (EnergyDataService): The service to fetch the data.

    Returns:
    JSONResponse: The seeded energy data.
    """
    return await service.fetch_data(params=request_body.params)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logging.error(f"Validation error: {exc} in request: {request}")

    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("fast_api:app", host="0.0.0.0", port=6543, reload=True)
