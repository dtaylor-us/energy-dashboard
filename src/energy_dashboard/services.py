import copy
import logging
import os
from datetime import datetime
from typing import AsyncGenerator

import httpx
from dotenv import load_dotenv
from sqlalchemy import insert, select, text, Row, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.sql.ddl import CreateTable

from .database import EnergyDataTable, database, engine, get_energy_data_schema
from .models import EnergyData, StreamChartDataRequest, SqlSelectQuery
from .utils import URLBuilder
from .llm import gen_async_client, streaming_gen_select_query

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class EnergyDataService:
    def __init__(self, async_db: AsyncSession, db: Session, client: httpx.AsyncClient):
        self.client = client
        self.api_key = os.getenv("API_KEY")
        self.async_db = async_db
        self.db = db

    def build_url(self, params: dict) -> str:
        # Create an instance of URLBuilder
        url_builder = URLBuilder()

        # Add parameters to the URLBuilder
        for key, value in params.items():
            url_builder.add_param(key, value)

        # Add API key to the URLBuilder
        url_builder.add_api_key(self.api_key)
        return url_builder.build()

    async def fetch_data(self, params) -> dict:
        while True:
            # Build the URL using the parameters
            url = self.build_url(params)

            # Send a GET request to the API
            response = await self.client.get(url)

            # Parse the response as JSON
            data = response.json()

            # Break the loop if there is no data in the response
            if not data["response"]["data"]:
                break

            # Process each item in the data
            for item in data["response"]["data"]:
                # Convert the value to float, or 0.0 if it is None
                value = float(item["value"]) if item["value"] is not None else 0.0

                # Parse the period string into a datetime object
                period = datetime.strptime(item["period"], "%Y-%m-%dT%H")

                # Create an insert query for the EnergyData table
                query = insert(EnergyDataTable).values(
                    value=value,
                    period=period,
                    respondent=item["respondent"],
                    respondent_name=item["respondent-name"],
                    type=item["type"],
                    type_name=item["type-name"],
                    value_units=item["value-units"],
                )

                # Execute the query
                await database.execute(query)

            # Increment the offset parameter for the next iteration
            params["offset"] += params["length"]

        return data

    def list_all(self):
        """
        Return all rows from the EnergyDataTable
        Filter out the US48 respondent
        """
        return (
            self.db.query(EnergyDataTable)
            .filter(EnergyDataTable.respondent != "US48")
            .order_by(EnergyDataTable.respondent, EnergyDataTable.period)
            .all()
        )

    async def stream_all_from_prompt(
        self, prompt: str, row_count=10
    ) -> AsyncGenerator[tuple[EnergyData, SqlSelectQuery], None]:
        """
        Perform select query on the EnergyDataTable table from the prompt
        """
        schema_ddl = get_energy_data_schema()
        client = gen_async_client()
        query = await streaming_gen_select_query(client, schema_ddl, prompt)
        log.info(f"Executing query: {query} from prompt: {prompt}")
        stmt = text(query.select_stmt).execution_options(
            stream_results=True, max_row_buffer=row_count
        )
        rows = await self.async_db.stream(stmt)
        columns = [clmn.description for clmn in EnergyDataTable.__table__.columns]
        async for row in rows:
            row_data = dict(zip(columns, row))
            data = EnergyData.model_validate(row_data)
            yield data, query
        yield None

    async def stream_all(
        self, chart_params: StreamChartDataRequest, row_count=10
    ) -> AsyncGenerator[EnergyData, None]:
        stmt = self.prepare_stmt(chart_params, row_count)
        results_stream = await self.async_db.stream(stmt)
        buffer = []
        async for partition in results_stream.partitions(row_count):
            for rows in partition:
                for row in rows:
                    row_dict = self.row_to_dict(row)
                    data = EnergyData.model_validate(row_dict)
                    buffer.append(data)
                    if len(buffer) >= row_count:
                        yield buffer
                        buffer = []
        if buffer:
            yield buffer

    @staticmethod
    def prepare_stmt(params: StreamChartDataRequest, row_count):
        if params:
            # Convert start_date and end_date from string to datetime
            try:
                start_date = datetime.strptime(
                    params.start_date, "%Y-%m-%d %H:%M:%S.%f"
                )
                end_date = datetime.strptime(params.end_date, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                start_date = datetime.strptime(params.start_date, "%Y-%m-%d")
                end_date = datetime.strptime(params.end_date, "%Y-%m-%d")

            stmt = (
                select(EnergyDataTable)
                .where(
                    and_(
                        EnergyDataTable.respondent == params.respondent,
                        EnergyDataTable.period >= start_date,
                        EnergyDataTable.period <= end_date,
                        EnergyDataTable.type_name == params.type_name.value,
                    )
                )
                .order_by(EnergyDataTable.respondent, EnergyDataTable.period)
                .execution_options(stream_results=True, max_row_buffer=row_count)
            )
        else:
            stmt = (
                select(EnergyDataTable)
                .filter(EnergyDataTable.respondent != "US48")
                .order_by(EnergyDataTable.respondent, EnergyDataTable.period)
                .execution_options(stream_results=True, max_row_buffer=row_count)
            )
        return stmt

    @staticmethod
    def row_to_dict(row: Row):
        """
        Convert a SQLAlchemy Row object to a dictionary
        row: Row (SQLAlchemy Row object)
        """
        m = {}
        for column in row.__table__.columns:
            m[column.name] = str(getattr(row, column.name))
        return m
