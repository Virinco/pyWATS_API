
from __future__ import annotations

from typing import Optional

from pydantic import Field
from report.wats_base import WATSBase


class AdditionalData(WATSBase):
    """
    A collection of additional step, header, or station data.
    """

    name: str = Field(..., max_length=200, min_length=1)
    """
    The name of the additional data.
    """
    props: list[Optional[AdditionalDataProperty]] = Field(default_factory=list)
    """
    List of properties in the additional data.
    """


class AdditionalDataArray(WATSBase):
    """
    Information about array in additional data.
    """

    dimension: int
    """
    Dimension of array.
    """
    type: str
    """
    Type of the values in the array.
    """
    indexes: list[Optional[AdditionalDataArrayIndex]]
    """
    List of indexes in the array.
    """

class AdditionalDataArrayIndex(WATSBase):
    """
    Information about an index in an array.
    """

    text: str
    """
    The index as text.
    """
    indexes: list[int]
    """
    List of indexes ordered by dimension.
    """
    value: Optional[AdditionalDataProperty] = None


class AdditionalDataProperty(WATSBase):
    """
    An additional data property.
    """

    name: str = Field(..., min_length=1)
    """
    Name of property.
    """
    type: str = Field(..., min_length=1)  #?
    """
    Value type of property.
    """
    flags: Optional[int] = None
    """
    Bit flags of property.
    """
    value: Optional[str] = None
    """
    Value string of property.
    """
    comment: Optional[str] = None
    """
    Comment of property.
    """
    num_format: Optional[str] = Field(default=None, validation_alias="numFormat", serialization_alias="numFormat")
    """
    Number format for value with type Number.
    """
    props: Optional[list[Optional[AdditionalDataProperty]]] = None
    """
    Array of sub-properties. Used for type Obj.
    """
    array: Optional[AdditionalDataArray] = None
    """
    Array information. Used for type Array.
    """

