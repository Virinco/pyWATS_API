import json
from typing import Any, Literal, Optional, Union, Generic, TypeVar
from uuid import UUID
from pydantic import Field, model_validator, root_validator
from pydantic_core.core_schema import FieldPlainInfoSerializerFunction

from report.wats_base import WATSBase
from .comp_operator import CompOp

class Measurement(WATSBase):
    parent_step: Optional[Any] = Field(default=None, exclude=True)

    model_config = {
        "populate_by_name": True,          # Use alias for serializatio / deserialization
        "arbitrary_types_allowed": True,    # Fixes StepList issue
        "use_enum_values": True,
        "json_encoders": {CompOp: lambda c: c.name},  # Serialize enums as their names
        "allow_inf_nan": True,
        "ser_json_inf_nan": 'strings'
    }

class BooleanMeasurement(Measurement):    
    status: str = Field(default="P", max_length=1, min_length=1, pattern='^[PFS]$')

class MultiBooleanMeasurement(BooleanMeasurement):    
    name: Optional[str] = Field(..., description="The name of the measurement - required for MultiStepTypes")

# ------------------------------------------------------------------------------------------
# LimitMeasurement 
class LimitMeasurement(BooleanMeasurement):
    value: Union[str,float] = Field(...)
    value_format: str | None = Field(default=None, validation_alias="valueFormat", serialization_alias="valueFormat")

    comp_op: Optional[CompOp] = Field(default=CompOp.LOG, validation_alias="compOp", serialization_alias="compOp")
    
    high_limit: float | str | None = Field(default=None, validation_alias="highLimit", serialization_alias="highLimit")
    high_limit_format: str | None = Field(default=None, validation_alias="highLimitFormat", serialization_alias="highLimitFormat")
    low_limit: float | str | None = Field(default=None, validation_alias="lowLimit", serialization_alias="lowLimit")
    low_limit_format: str | None = Field(default=None, validation_alias="lowLimitFormat", serialization_alias="lowLimitFormat")
        
    model_config = {
        "populate_by_name": True,          # Use alias for serializatio / deserialization
        "arbitrary_types_allowed": True,    # Fixes StepList issue
        "use_enum_values": True,
        "json_encoders": {CompOp: lambda c: c.name},  # Serialize enums as their names
        "allow_inf_nan": True,
        "ser_json_inf_nan": 'strings'
    }
    # Validate limits and comOp
    # @model_validator(mode="after")
    # def check_comp_op_limits(self):  
    #     if not self.comp_op.validate_limits(self.low_limit, self.high_limit):
    #         raise ValueError("Invalid limits")
    #     return self  
    
    # Using a Pydantic parsing method that supports current functionalities
    # @classmethod
    # def parse_obj(cls, obj):
    #     if isinstance(obj.get('comp_op'), str):
    #         obj['comp_op'] = CompOp[obj['comp_op']].value
    #     return super().model_validate(obj)

