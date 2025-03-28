# MessagePopUp
# messagePopup: Optional[MessagePopup] = None

# Type/lib
from typing import Literal, Optional
from pydantic import BaseModel, Field

from report.wats_base import WATSBase

# Imports
from ..step import Step

class MessagePopupInfo(WATSBase):
    response: Optional[str] = Field(default=" ", max_length=100, min_length=1, description="The popup message.")
    button: Optional[int] = Field(default=None, description="The code of the button that was pressed.")

# Example

# Class: MessagePopUpStep
# A step type that displays a popup message.
class MessagePopUpStep(Step):
    step_type: Literal["MessagePopup"] = Field(default="MessagePopup", validation_alias="stepType", serialization_alias="stepType")
    button_format: Optional[str] = Field(default=None, description="", validation_alias="buttonFormat", serialization_alias="buttonFormat")
    messagePopup: Optional[MessagePopupInfo] = Field(default=None, description="The popup data")


    def validate_step(self, trigger_children=False, errors=None) -> bool:
        """ No validation required """
        return True


