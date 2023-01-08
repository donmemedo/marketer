from pydantic import BaseModel


class SearchUser(BaseModel):
    username: str
