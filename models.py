from pydantic import BaseModel
from typing import Optional

class Bookmark(BaseModel):
    notion_id: str
    url: str
    html: Optional[str]