from datetime import datetime
from enum import Enum
from typing import Dict, Any

from pydantic import BaseModel, Field


class LLMModel(str, Enum):
    Claude3 = "claude-3-opus-20240229"
    GPT4_Omni = "gpt-4o"
    LLAMA3 = "llama3-70b-8192"


class SqlSelectQuery(BaseModel):
    select_stmt: str = Field(..., description="The select statement for the query")
    explain_stmt: str = Field(..., description="The explain statement for the query")
    start_date: str = Field(..., description="The start date for the data")
    end_date: str = Field(..., description="The end date for the data")


class EnergyData(BaseModel):
    id: int = Field(..., description="The unique identifier for the data entry")
    period: datetime = Field(..., description="The period of the data entry")
    respondent: str = Field(..., description="The respondent for the data entry")
    respondent_name: str = Field(..., description="The name of the respondent")
    type: str = Field(..., description="The type of data entry")
    type_name: str = Field(..., description="The name of the type of data entry")
    value: float = Field(..., description="The value of the data entry")
    value_units: str = Field(
        ..., description="The units of the value of the data entry"
    )


class EnergyType(str, Enum):
    D = "Demand"
    NG = "Generation"


class StreamChartDataRequest(BaseModel):
    respondent: str = Field(..., description="The respondent for the data")
    type_name: EnergyType = Field(..., description="The category of the data")
    start_date: str = Field(..., description="The start date for the data")
    end_date: str = Field(..., description="The end date for the data")


class EnergyDataRequest(BaseModel):
    params: Dict[str, Any]
