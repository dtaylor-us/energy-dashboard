import logging
import os
from datetime import datetime
from typing import AsyncGenerator

import httpx
from dotenv import load_dotenv
from sqlalchemy import insert, select, Row, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from .database import EnergyDataTable, database
from .models import EnergyData, RetrieveEnergyDataRequest
from .utils import URLBuilder

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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

    async def list_all(self, count=None, params=None):
        """
        Return rows from the EnergyDataTable based on the provided parameters.
        Filter out the US48 respondent by default.
        """
        # Prepare the SQL statement
        stmt = await self.prepare_stmt(params, count)

        # Execute the query and return the result
        result = await self.async_db.execute(stmt)
        rows = result.scalars().all()
        return [self.row_to_dict(row) for row in rows]

    async def stream_all(
            self, row_count=10, chart_params: RetrieveEnergyDataRequest = None
    ) -> AsyncGenerator[EnergyData, None]:
        stmt = await self.prepare_stmt(chart_params, row_count)
        stmt.execution_options(stream_results=True, max_row_buffer=row_count)

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
    async def prepare_stmt(params: RetrieveEnergyDataRequest, row_count):
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
                        EnergyDataTable.type_name == params.category.value,
                    )
                )
                .order_by(EnergyDataTable.respondent, EnergyDataTable.period)
            )
        else:
            stmt = (
                select(EnergyDataTable)
                .filter(EnergyDataTable.respondent != "US48")
                .order_by(EnergyDataTable.respondent, EnergyDataTable.period)
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
