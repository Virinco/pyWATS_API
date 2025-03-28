
from typing import Any, Dict, Optional, Self
from pydantic import BaseModel, ModelWrapValidatorHandler, ValidationInfo, model_validator


class WATSBase(BaseModel):
    '''
    Base class for Report Model
    -
    Sets model configutation for all models
    Handles incoming deserialization-context for loading legacy-data by injecting default values
    '''
    # Injects default values sent in validation-context.
    @model_validator(mode="before")
    def inject_defaults(cls, data: Any, info: Optional[ValidationInfo]) -> Any:
        # Check if context is provided
        if info.context is not None and hasattr(info.context, 'defaults'):
            defaults = info.context.defaults
            for key, value in defaults.items():
                # Split type & prop
                if key.find(".") > 0:
                    type_name, prop_name = key.split(".")

                    # Skip if the type doesn't match
                    if type_name != cls.__qualname__:
                        continue
                    
                    # Get the alias for the field (if it exists)
                    field_info = cls.model_fields.get(prop_name)
                    alias = (
                        field_info.validation_alias
                        if field_info and field_info.validation_alias
                        else prop_name  # Fall back to the internal name
                    )

                    # Use the alias to check and set the value in the data
                    if data.get(alias) in (None, ""):
                        data[alias] = value
                else:
                    # Handle non-nested keys
                    if data.get(key) in (None, ""):
                        data[key] = value

        # Return the modified data for further validation
        return data

    #-------------------------------------------------------------------
    # Model Config
    # Make sure json is deserialized to alias names
    model_config = {
        "populate_by_name": True,          # Use alias for serializatio / deserialization
        "arbitrary_types_allowed": True,    # Fixes StepList issue
        "use_enum_values": True,
        "allow_inf_nan": True,
        "ser_json_inf_nan": 'strings'
    }