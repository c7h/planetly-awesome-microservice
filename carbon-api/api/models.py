from typing import Optional
from pydantic import BaseModel, Field 
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class User(BaseModel):
    username: str
    user_id: int


class UsageTypeModel(BaseModel):
    id: int
    name: str
    unit: str
    factor: float


class UsageUpdateModel(BaseModel):
    amount: Optional[float]
    usage_type_id: Optional[int]


class UsageModel(BaseModel):
    """Base Model of a usage object"""
    user_id: str
    amount: float


class UsageCreateModel(UsageModel):
    """Model used to create a usage object"""
    usage_type_id: int


class UsageStorageModel(UsageModel):
    """How data is stored in the database"""
    usage_type: UsageTypeModel
    usage_at: datetime


class UsageResponseModel(UsageStorageModel):
    """The value stored in the database is an extended version of the
    Usage Model"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        json_encoders = {ObjectId: str}


class StatusOkModel(BaseModel):
    """Generic response containing additional information"""
    msg: str = ...
    detail: Optional[dict] = None
