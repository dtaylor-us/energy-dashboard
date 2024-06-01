import asyncio
import logging
import math
from typing import Annotated, Dict, List, AsyncGenerator

import httpx
import pandas as pd
from bokeh.embed import components
from bokeh.models import ColumnDataSource
from bokeh.models import NumeralTickFormatter, DatetimeTickFormatter, HoverTool, Range1d
from bokeh.plotting import figure
from fastapi import APIRouter, Depends, FastAPI, Request, Query, Form, Body
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from energy_dashboard.database import AsyncSessionLocal, SessionLocal
from energy_dashboard.models import RetrieveEnergyDataRequest, SeedEnergyDataRequest
from energy_dashboard.services import EnergyDataService
from energy_dashboard.utils import TEMPLATES_DIR

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


@app.get("/stream", name="stream", response_class=StreamingResponse)
async def stream_energy_data(
        request: Request, service: EnergyDataService = Depends(get_energy_service)
):
    """
    Stream the energy data as Server-Sent Events (SSE)
    """

    async def streaming_data():
        strm = service.stream_all()
        async for data in strm:
            yield f"data: {data.model_dump_json(indent=4)}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(streaming_data(), media_type="text/event-stream")


@app.post("/trigger-streaming", response_class=HTMLResponse)
async def trigger_streaming(
        request: Request,
        respondent: Annotated[str, Form()],
        category: Annotated[str, Form()],
        start_date: Annotated[str, Form()],
        end_date: Annotated[str, Form()],
):
    sse_config = dict(
        listener=HX_SSE_LISTENER,
        path=f"/stream-chart?respondent={respondent}&category={category}&start_date={start_date}&end_date={end_date}",
        topics=[CHART_TOPIC, TERMINATE],
    )
    return templates.TemplateResponse(
        "index.jinja2", {"request": request, "sse_config": sse_config}
    )


@app.get("/stream-chart", response_class=StreamingResponse)
async def energy_stream(
        service: EnergyDataService = Depends(get_energy_service),
        respondent: str = Query(None),
        category: str = Query(None),
        start_date: str = Query(None),
        end_date: str = Query(None),
):
    if not all([respondent, category, start_date, end_date]):
        return JSONResponse(
            status_code=400,
            content={"message": "All parameters must be provided"},
        )

    params = RetrieveEnergyDataRequest(
        respondent=respondent,
        category=category,
        start_date=start_date,
        end_date=end_date,
    )

    def create_context(div, script):
        context = {
            "script": script.replace("\n", " "),
            "div": div.replace("\n", " "),
        }
        return context

    def render_chunk(event: str, context: Dict, attrs: Dict):
        chunk = render_sse_html_chunk(
            event,
            context,
            attrs=attrs,
        )
        return f"{chunk}\n\n".encode("utf-8")

    async def streaming_data(chart_params=params):
        # TODO: Highlight stored chart state for appending buffer data
        chart_state = {
            "x_state": [],
            "y_state": [],
        }

        nrgstrm = buffer_stream(service, chart_params)
        async for energy_data in nrgstrm:
            print(f"Sending {energy_data} to client...")
            if energy_data is None:
                yield render_chunk(
                    TERMINATE,
                    None,
                    attrs={"id": HX_SSE_LISTENER, "hx-swap-oob": "true"},
                )
                nrgstrm.aclose()
            else:
                chart_state["y_state"].append(energy_data.value)
                chart_state["x_state"].append(energy_data.period)
                div, script = create_chart(chart_state)
                context = create_context(div, script)
                yield render_chunk(
                    CHART_TOPIC,
                    context,
                    attrs={"id": "linechart", "hx-swap-oob": "true"},
                )
                await asyncio.sleep(2)

    def prepare_data(chart_state):
        values = [value for value in chart_state["y_state"]]
        hours = [period for period in chart_state["x_state"]]
        source = ColumnDataSource(data=dict(hours=hours, values=values))
        return source

    def create_figure(hours):
        fig = figure(
            x_axis_type="datetime",
            height=500,
            tools="xpan",
            width=1250,
            title=f"MISO - Hour: {max(hours)}",
        )
        return fig

    def format_figure(fig):
        fig.title.align = "left"
        fig.title.text_font_size = "1em"
        fig.yaxis[0].formatter = NumeralTickFormatter(format="0.0a")
        fig.yaxis.axis_label = "Megawatt Hours"
        fig.y_range.start = 50000
        fig.y_range.end = 125000
        fig.xaxis.major_label_orientation = math.pi / 4

        # Convert start_date and end_date from string to datetime
        fig.x_range = Range1d(
            start=pd.Timestamp(params.start_date), end=pd.Timestamp(params.end_date)
        )

        fig.xaxis.ticker.desired_num_ticks = 24
        fig.xaxis.formatter = DatetimeTickFormatter(
            days="%m/%d/%Y, %H:%M:%S",  # Format for day-level ticks
            hours="%m/%d/%Y, %H:%M:%S",  # Format for hour-level ticks
        )
        return fig

    def add_line_and_hover(fig, source):
        fig.line(
            x="hours",
            y="values",
            source=source,
            line_width=2,
        )
        hover = HoverTool(
            tooltips=[
                ("Value", "@values{0.00}"),
                ("Hours", "@hours{%F %T}"),
            ],
            formatters={
                "@hours": "datetime",
            },
            mode="vline",
            show_arrow=False,
        )
        fig.add_tools(hover)
        return fig

    def create_chart(chart_state: Dict):
        source = prepare_data(chart_state)
        fig = create_figure(chart_state["x_state"])
        fig = format_figure(fig)
        fig = add_line_and_hover(fig, source)
        script, div = components(fig)
        return div, script

    return StreamingResponse(streaming_data(), media_type="text/event-stream")


async def buffer_stream(
        service: EnergyDataService,
        chart_params: RetrieveEnergyDataRequest,
        row_count=BUFFER_SIZE,
) -> AsyncGenerator[List[EnergyData], None]:
    nrgstream = service.stream_all(row_count, chart_params)
    async for energy_data in nrgstream:
        for data in energy_data:
            yield data
    yield None


@app.get("/", name="index")
async def index(request: Request):
    # Serve the dashboard using the index.jinja2 template
    return templates.TemplateResponse("index.jinja2", {"request": request})


@app.post("/api/v1/seed-data/")
async def seed_energy_data(
        request_body: SeedEnergyDataRequest = Body(...),
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
