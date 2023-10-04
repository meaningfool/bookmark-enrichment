from pydantic import BaseModel
from typing import Optional

class Bookmark(BaseModel):
    notion_id: str
    url: Optional[str] = None
    domain: Optional[str] = None
    html: Optional[str] = None