from pydantic import BaseModel
from typing import List

class FormSubmit(BaseModel):
    full_name: str
    templates: List[str]