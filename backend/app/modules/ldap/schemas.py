from pydantic import BaseModel


class LdapTestPayload(BaseModel):
    username: str | None = None
    password: str | None = None
