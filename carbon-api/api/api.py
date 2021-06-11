from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, status, Path, Body, HTTPException, Depends

from models import (
    StatusOkModel, UsageCreateModel, UsageResponseModel,
    UsageStorageModel, PyObjectId, UsageUpdateModel, UsageTypeModel
)
from db import (get_usage_type, list_usages_for_user, retrieve_usage,
                add_usage, update_usage, delete_usage, get_all_usage_types)
from errors import ResourceNotFoundException
from auth import validate_token, TokenData


app = FastAPI()


# CRUD operations here...

@app.post("/usages", response_description="record new usage",
          response_model=UsageResponseModel,
          status_code=status.HTTP_201_CREATED)
async def record(usage: UsageCreateModel = Body(...),
                 token: TokenData = Depends(validate_token)):
    """Add a new carbon record to the database"""

    # resolve usage type
    resolved_type = await get_usage_type(usage.usage_type_id)
    if not resolved_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The provided usage type is unknown."
        )

    new_item = UsageStorageModel.parse_obj(
        {
            **usage.dict(),
            "usage_at": datetime.utcnow(),
            "usage_type": resolved_type,
            "user_id": token.user_id
        }
     )

    usage_in_db = await add_usage(new_item)
    return usage_in_db


@app.get("/usages/{id}", response_model=UsageResponseModel)
async def get_one(id: PyObjectId = Path(...),
                  token: TokenData = Depends(validate_token)):
    """Return the specific usage object."""
    resp = await retrieve_usage(id, token)
    if not resp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not find the requested usage data"
        )
    return resp


@app.put("/usages/{id}", response_model=UsageResponseModel)
async def modify(id: PyObjectId = Path(...),
                 usage: UsageUpdateModel = Body(...),
                 token: TokenData = Depends(validate_token)):
    """Modify an existing usage resource"""
    resolved_type = None
    if usage.usage_type_id:
        resolved_type = await get_usage_type(usage.usage_type_id)
        if not resolved_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The provided usage type is unknown."
            )
    updated_fields = dict(
        amount=usage.amount,
        usage_type=resolved_type
    )

    try:
        response = await update_usage(id, updated_fields, token)
    except ResourceNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The resouce to update could not be found."
        )
    else:
        return response


@app.delete("/usages/{id}", status_code=status.HTTP_200_OK,
            response_model=StatusOkModel)
async def delete(id: PyObjectId = Path(...),
                 token: TokenData = Depends(validate_token)):
    """Delete an exising usage resource"""

    # TODO: check for user
    try:
        deleted_cnt = await delete_usage(id)
    except ResourceNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resouce not found - couldn't delete it.")
    return {
        "msg": "Usage entry deleted successfully",
        "detail": {
            "delted_count": deleted_cnt
        }
    }


@app.get("/usages", response_model=List[UsageResponseModel])
async def get_users(limit: Optional[int] = 10, offset: Optional[int] = 0,
                    token: TokenData = Depends(validate_token)):

    res = await list_usages_for_user(
        user_id=token.user_id,
        limit=limit,
        offset=offset
    )
    return res


@app.get("/types", response_model=List[UsageTypeModel])
async def get_types(limit: Optional[int] = 10, offset: Optional[int] = 0):
    all_types = await get_all_usage_types(limit, offset)
    return all_types
