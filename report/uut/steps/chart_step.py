# ChartStep

# Type/lib
from typing import Literal, Optional
from pydantic import Field

from report.uut.steps.numeric_step import MultiNumericStep

# Imports
from ..step import Step
from ...chart import Chart


# Example json object and schema

# Class: MessagePopUpStep
# A step type that displays a popup message.
class ChartStep(MultiNumericStep):
    step_type: Literal["WATS_XYGMNLT"] = Field(default="WATS_XYGMNLT", validation_alias="stepType", serialization_alias="stepType")
    def validate_step(self, trigger_children=False, errors=None) -> bool:
        if not super().validate_step(trigger_children=trigger_children, errors=errors):
            return False

        # Validate ChartStep here
        # Must have a valid chart
        
        return True


