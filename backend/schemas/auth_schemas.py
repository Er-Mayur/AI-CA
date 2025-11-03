# backend/schemas/auth_schemas.py
from pydantic import BaseModel, EmailStr, Field

# --------------------------------------------------------------------
# Request models
# --------------------------------------------------------------------
# backend/schemas/auth_schemas.py

from pydantic import BaseModel, EmailStr, Field
from datetime import date

class RegisterIn(BaseModel):
    name: str = Field(..., example="Mayur Mahajan")
    email: EmailStr
    pan_number: str = Field(..., example="ABCDE1234F")
    password: str = Field(..., min_length=6, example="Qwer@1234")
    date_of_birth: date = Field(..., example="2004-05-28")
    gender: str = Field(..., example="Male")
    employment_type: str = Field(..., example="Salaried / Self-Employed / Freelancer")  # Salaried / Self-Employed / Freelancer
    residential_status: str = Field(..., example="Resident / NRI")  # Resident / NRI
    state: str = Field(..., example="Maharashtra")

class LoginIn(BaseModel):
    identifier: str = Field(..., example="ABCDE1234F or mayur@gmail.com")
    password: str = Field(..., min_length=6, example="password123")


# --------------------------------------------------------------------
# Response models
# --------------------------------------------------------------------
class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    pan_number: str

    class Config:
        orm_mode = True
