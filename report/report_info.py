from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from report.wats_base import WATSBase

# -----------------------------------------------------------
# Class: ReportInfo
class ReportInfo(WATSBase):
    """
    Generic info class for both UUT&UUR
    """
    operator: str = Field(..., max_length=100, min_length=1, validation_alias="user", serialization_alias="user",
                            description="The name id ID of the operator")
    comment: Optional[str] = Field(default=None, max_length=5000, min_length=0,
                                   description="")
    exec_time: Optional[float] = Field(default=None, alias = "execTime",
                                       description="The execution time of the test in seconds.")
    exec_time_format: Optional[str] = Field(default=None, validation_alias="execTimeFormat", serialization_alias="execTimeFormat",
                                            description="")
