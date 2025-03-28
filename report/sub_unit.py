from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field
from report.wats_base import WATSBase

class SubUnit(WATSBase):
    """
    A sub unit. 
    """
    pn: str = Field(..., max_length=100, min_length=1)
    """
    The partnumber of the sub unit.
    """
    rev: Optional[str] = Field(default=None, max_length=100, min_length=0)
    """
    The revision of the sub unit.
    """
    sn: str = Field(..., max_length=100, min_length=1)
    """
    The serial number of the sub unit.
    """
    part_type: Optional[str] = Field(default="Unknown", max_length=50, min_length=1, validation_alias="partType",serialization_alias="partType")
    """
    The type of sub unit.
    """

    model_config = ConfigDict(populate_by_name=True)
    


