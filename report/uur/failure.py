
from typing import Annotated
from pydantic import BaseModel, Field
from report.wats_base import WATSBase

from ..binary_data import BinaryData

class Failure(WATSBase):
    """
    A failure on a unit.
    """

    art_number: Annotated[str | None, Field(max_length=100, min_length=0, validation_alias="artNumber",serialization_alias="artNumber")] = None
    """
    The article number of the failed component.
    """
    art_rev: Annotated[str | None, Field(max_length=100, min_length=0, validation_alias="artRev",serialization_alias="artRev")] = None
    """
    The article revision of the failed component.
    """
    art_vendor: Annotated[str | None, Field(max_length=100, min_length=0, validation_alias="artVendor",serialization_alias="artVendor")] = None
    """
    The article vendor of the failed component.
    """
    art_description: Annotated[str | None, Field(max_length=100, min_length=0, validation_alias="artDescription",serialization_alias="artDescription")] = None
    """
    The article description of the failed component.
    """
    category: Annotated[str, Field(min_length=1)]
    """
    The failure category.
    """
    code: Annotated[str, Field(min_length=1)]
    """
    The failure category code.
    """
    comment: str | None = None
    """
    A comment about the failure.
    """
    com_ref: Annotated[str, Field(examples=[['C16', 'R2']], max_length=50, min_length=1, validation_alias="comRef", serialization_alias="comRef")] = None
    """
    The component reference of the failed component.
    """
    func_block: Annotated[str | None, Field(max_length=100, min_length=1, validation_alias="funcBlock",serialization_alias="funcBlock")] = None
    """
    The group of components the failed component belongs to.
    """
    ref_step_id: Annotated[int | None, Field(validation_alias="refStepId",serialization_alias="refStepId")] = None
    """
    The id of the step from the reference UUT report that uncovered the failure.
    """
    ref_step_name: Annotated[str | None, Field(validation_alias="refStepName",serialization_alias="refStepName")]
    """
    The name of the step from the reference UUT report that uncovered the failure (read-only).
    """
    attachments: Annotated[list[BinaryData] | None, Field()] = None
    """
    A list of attached files or documents in binary form.
    """