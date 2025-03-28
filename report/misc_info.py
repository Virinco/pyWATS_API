from __future__ import annotations

from pydantic import ConfigDict

from report.wats_base import WATSBase
from .common_types import *

# --------------------------------------------------------
# Miscelaneous information
class MiscInfo(WATSBase):
    """
    MiscInfo, or Miscellaneous information provides a key-value pair of properties 
    that can be used to log unit configurations that has no dedicated header field.
    """
    id: Optional[str] = Field(default=None, description="Index?") #???????????????????
    # Key
    description: str = Field(..., min_length=1, description="The misc infos display name/key")
    # String value
    string_value: Optional[str] = Field(default=None, 
                                        max_length=100, 
                                        min_length=0, 
                                        validation_alias="text",
                                        serialization_alias="text",  
                                        description="The misc info value as string.")
    # Numeric value - depricated
    numeric_value: Optional[int] = Field(default=None,
                                         deprecated=True, 
                                         validation_alias = "numeric",
                                         serialization_alias = "numeric",
                                         description="Numeric value. Not available for analysis - use string_value")
    
    type_def: Optional[str] = Field(default=None, max_length=30, min_length=0, validation_alias="typedef", serialization_alias="typedef",
                                    description="??????????????????????????????????????????????")    
    numeric_normat: Optional[str] = Field(default=None, deprecated=True, validation_alias="numericFormat", serialization_alias="numericFormat",
                                          description="?????????????????????????????")

