from typing import Optional
from openai import BaseModel
from pydantic import Field, field_validator


class DBConfig(BaseModel):
    provider: str = Field(
        description="Provider of the database (e.g., 'sqlite', 'mysql')",
        default="sqlite",
    )

    config: Optional[dict] = Field(
        description="Configuration for the specific database",
        default={},
    )

    @field_validator("config")
    def validate_config(cls, v, values):
        provider = values.data.get("provider")
        if provider in ["sqlite", "mysql"]:
            return v
        else:
            raise ValueError(f"Unsupported database provider: {provider}")
