from typing import Literal
from pydantic import Field
from .uur_info import UURInfo
from ..report import Report

class UURReport(Report):
    # Overloads
    type: Literal["R"] = "R"

    # UUR Specific
    info: UURInfo = Field(default=None, validation_alias="uur", serialization_alias="uur")


