from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, status, Path, Body, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from .models import (
    StatusOkModel, UsageCreateModel, UsageResponseModel,
    UsageStorageModel, PyObjectId, UsageUpdateModel
)
from .db import (get_usage_type, list_usages_for_user, retrieve_usage,
                 add_usage, update_usage, delete_usage)
from .errors import ResourceNotFoundException
from .auth import validate_token, TokenData


app = FastAPI()


# CORS Origins.
origins = [
    "http://api.planetly.com",
    "https://planetly.com",
    "http://localhost",
]

# For usage as a nice little microservice, we would like to
# access authentication from other services too. This is why we need to
# set CORS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/protected", response_model=StatusOkModel)
async def read_users_me(token: TokenData = Depends(validate_token)):
    return {
        "msg": "logged in",
        "details": token.dict()
    }

# CRUD operations here...

@app.post("/usages", response_description="record new usage",
          response_model=UsageResponseModel,
          status_code=status.HTTP_201_CREATED)
async def record(usage: UsageCreateModel = Body(...)):
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
            "usage_type": resolved_type
        }
     )

    usage_in_db = await add_usage(new_item)
    return usage_in_db


@app.get("/usages/{id}", response_model=UsageResponseModel)
async def get_one(id: PyObjectId = Path(...)):
    """Return the specific usage object."""
    resp = await retrieve_usage(id)
    if not resp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not find the requested usage data"
        )
    return resp


@app.put("/usages/{id}", response_model=UsageResponseModel)
async def modify(id: PyObjectId = Path(...),
                 usage: UsageUpdateModel = Body(...)):
    """Modify an existing usage resource"""

    if usage.usage_type_id:
        # TODO: refactor and extract function
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
        response = await update_usage(id, updated_fields)
    except ResourceNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The resouce to update could not be found."
        )
    else:
        return response


@app.delete("/usages/{id}", status_code=status.HTTP_200_OK,
            response_model=StatusOkModel)
async def delete(id: PyObjectId = Path(...)):
    """Delete an exising usage resource"""
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
async def get_users(limit: Optional[int] = 10, offset: Optional[int] = 0):

    res = await list_usages_for_user(user_id=12, limit=limit, offset=offset)
    return res
