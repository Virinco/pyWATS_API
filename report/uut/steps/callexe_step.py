# CallExeStep

# Type/lib
from typing import Literal, Optional
from pydantic import Field

from report.wats_base import WATSBase

# Imports
from ..step import Step


# Example json object and schema:
class CallExeStepInfo(WATSBase):
    exit_code: Optional[int] = Field(default=None, description="The exit code of the executable.", validation_alias="exitCode", serialization_alias="exitCode")


# Class: MessagePopUpStep
# A step type that displays a popup message.
class CallExeStep(Step):
    step_type: Literal["CallExecutable"] = Field(default="CallExecutable", validation_alias="stepType", serialization_alias="stepType")
    callExe: Optional[CallExeStepInfo] = Field(default=None, validation_alias="callExe", serialization_alias="callExe")

    def validate_step(self, trigger_children=False, errors=None) -> bool:
        if not super().validate_step(trigger_children=trigger_children, errors=errors):
            return False
        return True




