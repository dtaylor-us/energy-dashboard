from databases import Database
from sqlalchemy import Column, Integer, String, Float, DateTime, MetaData, create_engine, UniqueConstraint
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from energy_dashboard.utils import ROOT_DIR

# Define the URL for the SQLite database
ASYNC_DATABASE_URL = f"sqlite+aiosqlite:///{ROOT_DIR}/energy.db"
DATABASE_URL = f"sqlite:///{ROOT_DIR}/energy.db"

# Create a Database instance using the DATABASE_URL
database = Database(DATABASE_URL)

# Create a MetaData instance
metadata = MetaData()

# Create a declarative base class
Base = declarative_base(metadata=metadata)


# Define the EnergyData table
class EnergyDataTable(Base):
    __tablename__ = "energy_data"
    id = Column(Integer, primary_key=True, autoincrement=True)
    period = Column(DateTime, nullable=False)
    respondent = Column(String, nullable=True)
    respondent_name = Column(String, nullable=True)
    type = Column(String, nullable=True)
    type_name = Column(String, nullable=True)
    value = Column(Float, nullable=True)
    value_units = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "period", "respondent", "type", name="uix_period_respondent_type"
        ),
    )

    def __repr__(self):
        return f"<EnergyData(id={self.id}, period={self.period}, respondent={self.respondent}, respondent_name={self.respondent_name}, type={self.type}, type_name={self.type_name}, value={self.value}, value_units={self.value_units})>"


# Create an engine instance using the DATABASE_URL
# TODO: Highlight the async and sync sessions
## Async engine for async queries (https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=async_engine
)

## Sync engine for sync queries
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the tables defined in the metadata
Base.metadata.create_all(engine)
