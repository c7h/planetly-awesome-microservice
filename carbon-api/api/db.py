import os
from bson.objectid import ObjectId
import motor.motor_asyncio
from .models import UsageStorageModel
from .errors import ResourceNotFoundException

mongo_host = os.getenv('MONGO_HOST')
mongo_port = os.getenv('MONGO_PORT')

DATABASE_URL = f"mongodb://{mongo_host}:{mongo_port}"


client = motor.motor_asyncio.AsyncIOMotorClient(
    DATABASE_URL,
    uuidRepresentation="standard"
)
database = client.carbon
usage_collection = database.get_collection("usage_collection")
usage_type_collection = database.get_collection("usage_type_collection")


async def get_usage_type(usage_type_id: int):
    """Get usage for usage type"""
    return await usage_type_collection.find_one({"id": usage_type_id})


async def list_usages_for_user(user_id: int, limit: int, offset: int):
    """Retrieve all usages present in the database for a certain user"""
    cursor = usage_collection.find({"user_id": str(user_id)}).limit(limit).skip(offset)
    items = await cursor.to_list(limit)
    return items


async def add_usage(usage_data: UsageStorageModel) -> dict:
    """Add a new usage into to the database"""
    usage = await usage_collection.insert_one(usage_data.dict())
    return await usage_collection.find_one({"_id": usage.inserted_id})


async def retrieve_usage(id: ObjectId) -> dict:
    """Retrieve a usage with a matching ID"""
    return await usage_collection.find_one({"_id": id})


async def update_usage(id: ObjectId, data: dict) -> dict:
    """Update certain values and return the new object"""
    usage = await usage_collection.find_one({"_id": id})
    if not usage:
        # usage not found in DB
        raise ResourceNotFoundException("Resource not found in DB")

    # we don't want Nones in the update set, since it would override data
    data = {k: v for k, v in data.items() if v is not None}

    await usage_collection.update_one(
        {"_id": id}, {"$set": data}
    )
    return await usage_collection.find_one({"_id": id})


async def delete_usage(id: ObjectId) -> int:
    """Delete usage from the database"""
    usage = await usage_collection.find_one({"_id": id})
    if not usage:
        raise ResourceNotFoundException("Resource not found in DB")
    res = await usage_collection.delete_one({"_id": id})
    return res.deleted_count
