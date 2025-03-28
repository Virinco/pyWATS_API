from ...common_types import *

from report.uut.steps.comp_operator import CompOp

from ..step import Step, StepStatus
from .measurement import BooleanMeasurement, MultiBooleanMeasurement


class BooleanStep(Step):
    step_type: Literal["ET_PFT", "PassFailTest"] = Field(default="ET_PFT", validation_alias="stepType",serialization_alias="stepType")
 
    measurement: BooleanMeasurement = Field(default=None, validation_alias="booleanMeas", serialization_alias="booleanMeas")

    #Critical fix: Pre-process raw JSON data
    @model_validator(mode='before')
    def unpack_measurement(cls, data: dict) -> dict:
        if 'booleanMeas' in data:
            meas_data = data['booleanMeas']
            
            # Convert list to single item
            if isinstance(meas_data, list):
                data['booleanMeas'] = meas_data[0] if meas_data else None
            
            # Ensure dicts get converted to models
            if isinstance(data['booleanMeas'], dict):
                data['booleanMeas'] = BooleanMeasurement(**data['booleanMeas'])
    
        return data
    
    # Custom serializer for the measurement field
    @field_serializer('measurement', when_used='json')
    def serialize_measurement(self, measurement: Optional[BooleanMeasurement]) -> list:
        if measurement is None:
            return []
        return [measurement.model_dump(by_alias=True, exclude_none=True)]  # Use aliases during serialization
    
    def validate_step(self, trigger_children=False, errors=None) -> bool:
        if not super().validate_step(trigger_children=trigger_children, errors=errors):
            return False
        return True

class MultiBooleanStep(BooleanStep):
    step_type: Literal["ET_MPFT"] = Field(default="ET_MPFT", validation_alias="stepType", serialization_alias="stepType")
    measurements: list[MultiBooleanMeasurement] = Field(default_factory=list, validation_alias="booleanMeas",serialization_alias="booleanMeas")

    # validate_step
    def validate_step(self, trigger_children=False, errors=None) -> bool:
        if errors is None:
            errors = []
        if not super().validate_step(trigger_children=trigger_children, errors=errors):
            return False
        # Current Class Validation:
            
          # For every validation failure        
              # errors.append(f"{self.get_step_path()} ErrorMessage.")
        return True
    
    def add_measurement(self,*,name:str, status:str="P")-> MultiBooleanMeasurement :
        name = self.check_for_duplicates(name)
        nm = MultiBooleanMeasurement(name=name, status=status, parent_step=self)
        # Import single/multi logic before adding the test to list[numericMeasurements]

        # ? How to handle name if single/double
        # ? Alter type if meascount > 1

        # Add to list
        self.measurements.append(nm)
        return nm
    
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
    
   


   