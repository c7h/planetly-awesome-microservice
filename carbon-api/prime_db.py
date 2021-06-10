import os
import asyncio
# from bson.objectid import ObjectId
import motor.motor_asyncio

"""
This helper script adds default values
to the database.
"""
mongo_host = os.getenv('MONGO_HOST')
mongo_port = os.getenv('MONGO_PORT')

DATABASE_URL = f"mongodb://{mongo_host}:{mongo_port}"

client = motor.motor_asyncio.AsyncIOMotorClient(
    DATABASE_URL,
    uuidRepresentation="standard"
)
database = client.carbon
usage_type_collection = database.get_collection("usage_type_collection")

type_data = [
    {
        "id": 100,
        "name": "electricity",
        "unit": "kwh",
        "factor": 1.5
    },
    {
        "id": 101,
        "name": "water",
        "unit": "kg",
        "factor": 26.93
    },
    {
        "id": 102,
        "name": "heating",
        "unit": "kwh",
        "factor": 3.892
    },
    {
        "id": 103,
        "name": "heating",
        "unit": "l",
        "factor": 8.57
    },
    {
        "id": 104,
        "name": "heating",
        "unit": "m3",
        "factor": 19.456
    }
]

await database.
async def insert_types():
    return await usage_type_collection.insert_many(type_data)

if __name__ == "__main__":
    print(f"[?] Connected to database {DATABASE_URL}")
    print(f"[*] Adding {len(type_data)} entries to the collection...")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        insert_types()
    )
    print("[*]...done")
