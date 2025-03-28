# Type imports
from typing import Annotated, Any, Optional, Union
from pydantic import Field, SerializationInfo
from uuid import UUID,uuid4

# Model imports
from ..report_info import ReportInfo

class UURInfo(ReportInfo):
    processCode: int | None = Field(default=None, validation_alias="processCode", serialization_alias="processCode")
    processCodeFormat: str | None = Field(default=None, validation_alias="processCodeFormat", serialization_alias="processCodeFormat")
    processName: str | None = Field(default=None, validation_alias="processName", serialization_alias="processName")
    refUUT: UUID | None = Field(default=None, validation_alias="refUUT", serialization_alias="refUUT")
    confirmDate: str | None = Field(default=None, validation_alias="confirmDate", serialization_alias="confirmDate")
    finalizeDate: str | None = Field(default=None, validation_alias="finalizeDate", serialization_alias="finalizeDate")
    parent: UUID | None = Field(default=None)
    children: list[UUID] | None = Field(default=None)