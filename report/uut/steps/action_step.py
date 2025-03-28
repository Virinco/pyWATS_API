# MessagePopUp
# messagePopup: Optional[MessagePopup] = None

# Type/lib
from typing import Literal, Optional
from pydantic import Field

# Imports
from ..step import Step


# Example json object and schema:


# Class: MessagePopUpStep
# A step type that displays a popup message.
class ActionStep(Step):
    # Temporarily allow any step_type to use this as fallback
    #step_type: str = Field(default="Action", alias="stepType")

    #This is the correct implementation
    step_type: Literal["Action"] = Field(default="Action", validation_alias="stepType", serialization_alias="stepType")

    def validate_step(self, trigger_children=False, errors=None) -> bool:
        if not super().validate_step(trigger_children=trigger_children, errors=errors):
            return False
        return True


