from pydantic import BaseModel


class SnapshotData(BaseModel):
    base64: str
    name: str
