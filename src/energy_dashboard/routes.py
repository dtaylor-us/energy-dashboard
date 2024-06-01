import asyncio
import logging
from typing import Annotated, Dict, List, AsyncGenerator

import httpx
from fastapi import APIRouter, Depends, FastAPI, Request, Query, Form
from fastapi import Body
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from energy_dashboard.database import AsyncSessionLocal, SessionLocal
from energy_dashboard.models import (
    EnergyDataRequest,
    StreamChartDataRequest,
    EnergyData,
    EnergyType,
)
from energy_dashboard.services import EnergyDataService
from energy_dashboard.utils import TEMPLATES_DIR
from energy_dashboard.chart import (
    create_chart,
    create_context,
)


# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

HX_SSE_LISTENER = "hx-sse-listener"
CHART_TOPIC = "chart"
TERMINATE = "Terminate"

BUFFER_SIZE = 10

app = FastAPI()
router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATES_DIR)


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


def render_sse_html_chunk(event, chunk, attrs=None):
    if attrs is None:
        attrs = {}
    tmpl = templates.get_template("partials/streaming_chunk.jinja2")
    html_chunk = tmpl.render(event=event, chunk=chunk, attrs=attrs)
    return html_chunk


@app.post("/intruct-trigger-streaming", response_class=HTMLResponse)
async def instruct_trigger_streaming(
    request: Request,
    prompt: Annotated[str, Form()],
):
    sse_config = dict(
        listener=HX_SSE_LISTENER,
        path=f"/instruct-stream-chart?prompt={prompt}",
        topics=[CHART_TOPIC, TERMINATE],
    )
    return templates.TemplateResponse(
        "instruct.jinja2", {"request": request, "sse_config": sse_config}
    )


@app.post("/trigger-streaming", response_class=HTMLResponse)
async def trigger_streaming(
    request: Request,
    respondent: Annotated[str, Form()],
    type_name: Annotated[str, Form()],
    start_date: Annotated[str, Form()],
    end_date: Annotated[str, Form()],
):
    sse_config = dict(
        listener=HX_SSE_LISTENER,
        path=f"/stream-chart?respondent={respondent}&type_name={type_name}&start_date={start_date}&end_date={end_date}",
        topics=[CHART_TOPIC, TERMINATE],
    )
    return templates.TemplateResponse(
        "index.jinja2", {"request": request, "sse_config": sse_config}
    )


@app.get("/instruct-stream-chart", response_class=StreamingResponse)
async def instruct_stream_chart(
    service: EnergyDataService = Depends(get_energy_service),
    prompt: str = Query(None),
):
    if not prompt:
        return JSONResponse(
            status_code=400,
            content={"message": "Prompt must be provided"},
        )

    async def streaming_data(prompt: str):
        chart_state = {
            "x_state": [],
            "y_state": [],
        }

        nrgstrm = service.stream_all_from_prompt(prompt)
        async for energy_data, query in nrgstrm:
            log.info(f"Sending {energy_data} to client...")
            if energy_data is None:
                yield render_chunk(
                    TERMINATE,
                    {},
                    attrs={"id": HX_SSE_LISTENER, "hx-swap-oob": "true"},
                )
                await nrgstrm.aclose()
            else:
                chart_state["y_state"].append(energy_data.value)
                chart_state["x_state"].append(energy_data.period)
                div, script = create_chart(chart_state, query)
                context = create_context(div, script)
                yield render_chunk(
                    CHART_TOPIC,
                    context,
                    attrs={"id": "linechart", "hx-swap-oob": "true"},
                )
                await asyncio.sleep(2)

    return StreamingResponse(streaming_data(prompt), media_type="text/event-stream")


@app.get("/stream-chart", response_class=StreamingResponse)
async def energy_stream(
    service: EnergyDataService = Depends(get_energy_service),
    respondent: str = Query(None),
    type_name: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None),
):
    if not all([respondent, type_name, start_date, end_date]):
        return JSONResponse(
            status_code=400,
            content={"message": "All parameters must be provided"},
        )

    params = StreamChartDataRequest(
        respondent=respondent,
        type_name=EnergyType(type_name),
        start_date=start_date,
        end_date=end_date,
    )

    async def streaming_data(chart_params=params):
        chart_state = {
            "x_state": [],
            "y_state": [],
        }

        nrgstrm = buffer_stream(service, chart_params)
        async for energy_data in nrgstrm:
            log.info(f"Sending {energy_data} to client...")
            if energy_data is None:
                yield render_chunk(
                    TERMINATE,
                    {},
                    attrs={"id": HX_SSE_LISTENER, "hx-swap-oob": "true"},
                )
                await nrgstrm.aclose()
            else:
                chart_state["y_state"].append(energy_data.value)
                chart_state["x_state"].append(energy_data.period)
                div, script = create_chart(chart_state, params)
                context = create_context(div, script)
                yield render_chunk(
                    CHART_TOPIC,
                    context,
                    attrs={"id": "linechart", "hx-swap-oob": "true"},
                )
                await asyncio.sleep(2)

    return StreamingResponse(streaming_data(), media_type="text/event-stream")


def render_chunk(event: str, context: Dict, attrs: Dict):
    chunk = render_sse_html_chunk(
        event,
        context,
        attrs=attrs,
    )
    return f"{chunk}\n\n".encode("utf-8")


async def buffer_stream(
    service: EnergyDataService,
    chart_params: StreamChartDataRequest,
    row_count=BUFFER_SIZE,
) -> AsyncGenerator[List[EnergyData], None]:
    nrgstream = service.stream_all(chart_params, row_count=row_count)
    async for energy_data in nrgstream:
        for data in energy_data:
            yield data
    yield None


@app.get("/instruct", name="instruct")
async def instruct(request: Request):
    return templates.TemplateResponse("instruct.jinja2", {"request": request})


@app.get("/", name="index")
async def index(request: Request):
    # Serve the dashboard using the index.jinja2 template
    return templates.TemplateResponse("index.jinja2", {"request": request})


@app.post("/api/v1/seed-data/")
async def seed_energy_data(
    request_body: EnergyDataRequest = Body(...),
    service: EnergyDataService = Depends(get_energy_service),
):
    return await service.fetch_data(params=request_body.params)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logging.error(f"Validation error: {exc} in request: {request}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )


# Include the router for API endpoints
app.include_router(router)
