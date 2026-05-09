from pydantic import BaseModel
class VerifyTaskIn(BaseModel):
    verified: bool
class CompleteTaskIn(BaseModel):
    completed: bool
