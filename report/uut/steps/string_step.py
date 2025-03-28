from typing import Optional, Union, Literal, TYPE_CHECKING
from uuid import UUID
from pydantic import Field, field_serializer, model_serializer, model_validator

from report.uut.steps.comp_operator import CompOp

from ..step import Step
from .measurement import BooleanMeasurement, MultiBooleanMeasurement

class StringMeasurement(BooleanMeasurement):
    value: Optional[str] = None
    comp_op: Optional[CompOp] = Field(default=CompOp.LOG, validation_alias="compOp", serialization_alias="compOp")
    limit: Optional[str] = Field(default=None, validation_alias="limit", serialization_alias="limit")

    
class MultiStringMeasurement(StringMeasurement):
    name: str = Field(..., description="The name of the measurement - required for MultiStepTypes")


class StringStep(Step):
    step_type: Literal["ET_SVT"] = Field(default="ET_SVT", validation_alias="stepType", serialization_alias="stepType")
    measurement: StringMeasurement = Field(default=None, validation_alias="stringMeas", serialization_alias="stringMeas")

    def validate_step(self, trigger_children=False, errors=None) -> bool:
        if not super().validate_step(trigger_children=trigger_children, errors=errors):
            return False
        return True

    #Critical fix: Pre-process raw JSON data
    @model_validator(mode='before')
    def unpack_measurement(cls, data: dict) -> dict:
        if 'stringMeas' in data:
            meas_data = data['stringMeas']
            
            # Convert list to single item
            if isinstance(meas_data, list):
                data['stringMeas'] = meas_data[0] if meas_data else None
            
            # Ensure dicts get converted to models
            if isinstance(data['stringMeas'], dict):
                data['stringMeas'] = StringMeasurement(**data['stringMeas'])
        
        return data

    # Custom serializer for the measurement field
    @field_serializer('measurement', when_used='json')
    def serialize_measurement(self, measurement: Optional[StringMeasurement]) -> list:
        if measurement is None:
            return []
        return [measurement.model_dump(by_alias=True, exclude_none=True)]  # Use aliases during serialization


class MultiStringStep(Step):
    step_type: Literal["ET_MSVT"] = Field(default="ET_MSVT", validation_alias="stepType", serialization_alias="stepType")
    measurements: list[MultiStringMeasurement] = Field(default_factory=list, validation_alias="stringMeas", serialization_alias="stringMeas")

    def validate_step(self, trigger_children=False, errors=None) -> bool:
        if not super().validate_step(trigger_children=trigger_children, errors=errors):
            return False
        return True
    
    def add_measurement(self,*,name:str=None, value:float, status:str, comp_op: CompOp, limit: str = None):
        name = self.check_for_duplicates(name)
        sm = MultiStringMeasurement(name=name, value=value, status=status, comp_op=comp_op, limit=limit, parent_step=self)
        # Import single/multi logic before adding the test to list[numericMeasurements]

        # ? How to handle name if single/double
        # ? Alter type if meascount > 1

        # Add to list
        self.measurements.append(sm)

    def check_for_duplicates(self, name):
        """
        Check for duplicate measurement names
        """
        # Validate if a measurement with the same name already exists
        if any(measurement.name == name for measurement in self.measurements):
            base_name = name
            if len(name) >= 100:
                base_name = name[:97]
            suffix = 2
            new_name = f"{base_name} #{suffix}"

            # Keep generating a new name until it's unique
            while new_name in self.measurements:
                suffix += 1
                new_name = f"{base_name} #{suffix}"

            # Update the measurement's name
            name = new_name
        return name