"""
This module contains helper models which is used for inheritance purposes.
"""
import uuid as uuid_pkg
from datetime import datetime

from sqlalchemy import TIMESTAMP, Column, text
from sqlmodel import Field, SQLModel


class UUIDModel(SQLModel):
    """
    Model containing unique identifier in UUID format.
    This class is used in inheritance to add identifier to database model.
    """
    id: uuid_pkg.UUID | None = Field(
        default_factory=uuid_pkg.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        sa_column_kwargs={
            "server_default": text("gen_random_uuid()"),
            "unique": True,
        },
    )