
from __future__ import annotations


from pydantic import Field
from report.wats_base import WATSBase

class Attachment(WATSBase):
    """
    A document or file in binary format.
    """

    name: str = Field(..., min_length=1)
    """
    The name of the attached document or file.
    """
    content_type: str | None = Field(default=None, examples=[['image/png', 'text/plain']], min_length=1, validation_alias="contentType", serialization_alias="contentType")
    """
    The document or file MIME type.
    """
    data: str | None = Field(default=None, min_length=1)
    """
    The data of the document or file in binary format.
    """
    