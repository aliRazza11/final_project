# app/schemas/settings.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class SettingsUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    old_password: Optional[str] = None
    new_password: Optional[str] = None

class SettingsUpdateResult(BaseModel):
    ok: bool
    reauth_required: bool
    message: str

class DeleteAccountRequest(BaseModel):
    password: str

class DeleteAccountResult(BaseModel):
    ok: bool
    message: str
