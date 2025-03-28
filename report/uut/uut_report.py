"""
UUTReport.py
-
-
"""
from report.common_types import *
from ..report import Report
from .uut_info import UUTInfo
from .steps.sequence_call import SequenceCall, SequenceCallInfo
    
def_MissingString = "Missing"
def_MissingNumeric = "NaN"

class UUTReport(Report):
    """
    Class: UUTReport

    """
    # Overloads
    type: Literal["T"] = "T" #Field(default="T", max_length=1, min_length=1, pattern='^[T]$')

    # UUT Specific
    root: SequenceCall = Field(default_factory=SequenceCall)        # Root Sequence Call
    info: UUTInfo = Field(..., default_factory=UUTInfo, validation_alias="uut", serialization_alias="uut")     # Info (serializes as alias:uut)

    # -------------------------------------------------------------------
    # Get root sequence call    
    def get_root_sequence_call(self) -> SequenceCall:
        self.root.name = "MainSequence Callback"
        return self.root