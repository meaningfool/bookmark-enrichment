from pydantic import BaseModel
from typing import Optional

class Bookmark(BaseModel):
    notion_id: str
    url: Optional[str]
    domain: Optional[str]
    html: Optional[str]