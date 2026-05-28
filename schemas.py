from pydantic import BaseModel, ConfigDict, Field, EmailStr
from datetime import datetime

class UserBase(BaseModel):
    username: str = Field(..., min_length=2, max_length=50, example="johndoe")
    email: EmailStr = Field(..., example="johndoe@example.com")

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    image_file: str | None = None
    image_path: str

class PostBase(BaseModel):                                                       
    title: str = Field(..., min_length=1, max_length=100, example="My First Post")
    content: str = Field(..., min_length=1, max_length=1000, example="This is the content of my first post.")

class PostCreate(PostBase):
    user_id: int = Field(..., example=1)

class PostResponse(PostBase): 
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    date_posted: datetime
    author: UserResponse