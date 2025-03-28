from __future__ import annotations
from typing import Optional

from pydantic import Field
from report.wats_base import WATSBase

# ---------------------------------------------------------
# BinaryData
class BinaryData(WATSBase):
    """
    A document or file in binary format.
    """
    content_type: str = Field(..., max_length=100, min_length=1,
                        validation_alias="contentType",
                        serialization_alias="contentType",
                        description="The document or file MIME type.",
                        examples=[['image/png', 'text/plain']])
    """
    The document or file MIME type.
    """
    data: str = Field(..., min_length=1,
                        description="The data of the document or file in binary format.")
    """
    The data of the document or file in binary format.
    """
    name: str = Field(..., max_length=256, min_length=1,
                        description="Name of the document or file.")
    """
    Name of the document or file.
    """
    id: Optional[str] = Field(default=None, exclude=True,
                        description="Output only! The unique id of the document or file.")
    """
    The unique id of the document or file. This property is not used for incomming reports (read-only).
    """
