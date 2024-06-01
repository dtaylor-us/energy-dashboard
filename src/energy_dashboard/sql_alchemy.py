import asyncio
import threading
import time

from sqlalchemy import create_engine, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from database import EnergyDataTable, SessionLocal
from energy_dashboard.utils import ROOT_DIR

ASYNC_DATABASE_URL = f"sqlite+aiosqlite:///{ROOT_DIR}/energy.db"
DATABASE_URL = f"sqlite:///{ROOT_DIR}/energy.db"

engine = create_engine(DATABASE_URL, echo=True)

Session = sessionmaker(bind=engine)
session = SessionLocal()


def sync_main():
    # Fetch data synchronously
    sync_data = session.query(EnergyDataTable).where(EnergyDataTable.respondent == "MISO").order_by().limit(24).all()

    # Print the data all at once after it is fetched
    print("Synchronous Data:")
    for data in sync_data:
        print(f"Sync Msg: -> {data.period}")


async def fetch_data(async_session_local, order):
    result = await async_session_local().execute(select(EnergyDataTable)
                                                 .where(EnergyDataTable.respondent == "MISO")
                                                 .order_by()
                                                 .limit(24)
                                                 .offset(order * 24))
    async_data = result.scalars().all()

    # Return the data as a list
    return async_data


async def async_main():
    async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)
    async_session_local = async_sessionmaker(
        autocommit=False, autoflush=False, bind=async_engine
    )

    # Fetch data asynchronously
    async with async_session_local.begin():
        # Fetch multiple data concurrently
        tasks = [fetch_data(async_session_local, order) for order in range(5)]
        for future in asyncio.as_completed(tasks):
            data = await future
            for item in data:
                print(f"Async Msg: => {item.period}")
                yield item


async def run_async_main():
    async for _ in async_main():
        pass


if __name__ == "__main__":
    # Start the synchronous function in a separate thread
    threading.Thread(target=sync_main).start()

    # Run the asynchronous main function in the main thread
    asyncio.run(run_async_main())
