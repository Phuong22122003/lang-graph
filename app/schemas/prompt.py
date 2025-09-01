from pydantic import BaseModel
class PromptRequest(BaseModel):
    message: str

class PromptResponse(BaseModel):
    message: str