from pydantic import BaseModel


class Credentials(BaseModel):
    username: str|None
    password: str|None