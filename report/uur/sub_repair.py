from __future__ import annotations
from typing import Any, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field

from failure import Failure
from ..sub_unit import SubUnit

class SubRepair(SubUnit):
    idx: Optional[int] = None
    """
    The index of the sub unit. Only for UUR reports.
    """
    parentIdx: Optional[int] = Field(default=None, validation_alias="parentIdx", serialization_alias="parentIdx")
    """
    The index of the parent sub unit. Only for UUR reports
    """
    position: Optional[int] = Field(default=None)
    """
    The position of the unit.
    """
    replacedIdx: Optional[int] = Field(default=None, validation_alias="replacedIdx", serialization_alias="replacedIdx")
    """
    The index of the sub unit that replaced this unit. Only for UUR reports.
    """
    failures: Optional[list[Failure]] = Field(default=None)
    """
    A list of failures on this sub unit. Only for UUR reports.
    """

