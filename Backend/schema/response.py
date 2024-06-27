import datetime
import enum
import uuid
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field


class ResponseStatus(str, enum.Enum):
    OK = "ok"
    FAILURE = "failure"


class StatusResponse(BaseModel):
    status: ResponseStatus
    details: Optional[str]


class Page(BaseModel):
    next:Optional[str]
    prev:Optional[str]
    index:int
    page_count:int = Field(..., serialization_alias="pageCount")
    total_count:int = Field(..., serialization_alias="totalCount")

ResultT = TypeVar('ResultT')
class PaginatedResult(BaseModel, Generic[ResultT]):
    page:Page
    results:List[ResultT]

class DeviceInfo(BaseModel):
    id:uuid.UUID 
    name:Optional[str]
    latitude:Optional[float]
    longitude:Optional[float]

class UserInfo(BaseModel):
    id:int
    name:str

class LikeInfo(BaseModel):
    is_liked:bool = Field(..., serialization_alias="isLiked") 
    likes:int
    users:Optional[List[UserInfo]] = Field(..., serialization_alias="users") 

class BirdSnapImage(BaseModel):
    id:int

class BirdSnap(BaseModel):
    id:int
    device_info:Optional[DeviceInfo] = Field(..., serialization_alias="deviceInfo")
    user_info:Optional[UserInfo] = Field(..., serialization_alias="userInfo")
    like_info:LikeInfo = Field(..., serialization_alias="likeInfo")
    is_public:bool
    snap_time:datetime.datetime
    images:List[BirdSnapImage]
    bird_species:Optional[List[str]]