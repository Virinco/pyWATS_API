from __future__ import annotations  # Enable forward references
from abc import ABC
import base64
from enum import Enum
import os
from typing import Any, Optional, Self, Union, Literal
from pydantic import Field, ModelWrapValidatorHandler, model_validator
from abc import ABC, abstractmethod

from report.wats_base import WATSBase

from ..chart import Chart, ChartType
from ..additional_data import AdditionalData
from ..attachment import Attachment
# -----------------------------------------------------------------------
# LoopInfo for looping steps
class LoopInfo(WATSBase):
    idx: Optional[int] = Field(default=None)
    num: Optional[int] = Field(default=None)
    ending_index: Optional[int] = Field(default=None, validation_alias="endingIndex",serialization_alias="endingIndex")
    passed: Optional[int] = Field(default=None)
    failed: Optional[int] = Field(default=None)

class StepStatus(Enum):
    Passed = 'P'
    Failed = 'F'
    Skipped = 'S'
    Terminated = 'T'
    Done = 'D'
    
# -----------------------------------------------------------------------
# Step: Abstract base step for all steps
class Step(WATSBase, ABC):  
    # Parent Step - For internal use only - does not seriallize
    parent: Optional['Step'] = Field(default=None, exclude=True)

    # Required
    step_type: Literal["NONE"] = Field(default="NONE",validation_alias="stepType", serialization_alias="stepType")
    #step_type: str = Field(default="NO_VALID_STEP",validation_alias="stepType")
    
    name: str = Field(default="StepName", max_length=100, min_length=1)
    group: str = Field(default="M", max_length=1, min_length=1, pattern='^[SMC]$')
    #status: str = Field(default="P", max_length=1, min_length=1, pattern='^[PFSDET]$')
    status: StepStatus = Field(default=StepStatus.Passed)

    id: Optional[Union[int, str]] = Field(default=None)

    # Error code and report text
    error_code: Optional[Union[int, str]] = Field(default=None, validation_alias="errorCode",serialization_alias="errorCode")
    error_code_format: Optional[str] = Field(default=None, validation_alias="errorCodeFormat", serialization_alias="errorCodeFormat")
    error_message: Optional[str] = Field(default=None, validation_alias="errorMessage",serialization_alias="errorMessage")
    report_text: Optional[str] = Field(default=None, validation_alias="reportText",serialization_alias="reportText")
    
    start: Optional[str] = Field(default=None, validation_alias="start",serialization_alias="start")
    tot_time: Optional[Union[float, str]] = Field(default=None, validation_alias="totTime",serialization_alias="totTime")
    tot_time_format: Optional[str] = Field(default=None, validation_alias="totTimeFormat",serialization_alias="totTimeFormat")
    ts_guid: Optional[str] = Field(default=None, validation_alias="tsGuid",serialization_alias="tsGuid")
    
    # Step Caused Failure (ReadOnly)
    caused_seq_failure: Optional[bool] = Field(default=None, validation_alias="causedSeqFailure", serialization_alias="causedSeqFailure")
    caused_uut_failure: Optional[bool] = Field(default=None, validation_alias="causedUUTFailure", serialization_alias="causedUUTFailure")
    
    # LoopInfo
    loop: Optional[LoopInfo] = Field(default=None)
   
    # Additional Results, Charts and Attachments
    additional_results: Optional[list[AdditionalData]] = Field(default=None, validation_alias="additionalResults", serialization_alias="additionalResults")
    
    chart: Optional[Chart] = Field(default=None)
    attachment: Optional[Attachment] = Field(default=None)  



    # validate - all step types
    @abstractmethod
    def validate_step(self, trigger_children=False, errors=None) -> bool:
        # Implement generic step validation here

        # Validate Step
            # Validate LoopInfo
            # Validate Additional Results
            # Validate Chart
            # Validate Attachment

        return True
        # validate_step template:
        # @abstractmethod
        # def validate_step(self, trigger_children=False, errors=None) -> bool:
        #     if errors is None:
        #         errors = []
        #     if not super().validate_step(trigger_children=trigger_children, errors=errors):
        #         return False
        #     # Current Class Validation:
        #       # For every validation failure        
        #           errors.append(f"{self.get_step_path()} ErrorMessage.")
        #     return True

    # return the steps path
    def get_step_path(self) -> str:
        path = []
        current_step = self
        while current_step is not None:
            path.append(current_step.name)
            current_step = current_step.parent
        return '/'.join(reversed(path))

    # Add chart to any step
    def add_chart(self, chart_type:ChartType, chart_label: str, x_label:str, x_unit:str, y_label: str, y_unit: str) -> Chart:
        self.chart = Chart(chart_type=chart_type, label=chart_label, xLabel=x_label, yLabel=y_label, xUnit=x_unit, yUnit=y_unit)
        return self.chart
    
    # Attach a file to the step        
    def attach_file(self, file_name: str, delete_after_upload: bool = False) -> None:
        """
        Reads a file, encodes its contents in base64, and stores it in the data property.
        Optionally deletes the file after reading it.
        
        :param file_name: The name or path of the file to attach
        :param delete_after_upload: Whether to delete the file after attaching it (default is True)
        """
        if self.attachment is None:
            self.attachment = Attachment(name="New attachment")
        try:
            with open(file_name, 'rb') as file:
                # Read the file and encode it in base64
                binary_content = file.read()
                self.attachment.data = base64.b64encode(binary_content).decode('utf-8')
                # Optionally delete the file
                if delete_after_upload:
                    os.remove(file_name)
        except:
            raise(ValueError("Failed to attach file"))
        
        # Set the name of the attachment as the filename
        self.attachment.name = os.path.basename(file_name)
        import mimetypes
        self.attachment.content_type, _ = mimetypes.guess_type(file_name, strict=False)


        

StepType = Union['SequenceCall','MultiNumericStep','NumericStep','BooleanStep','MultiBooleanStep', 'MultiStringStep', 'StringStep', 'ChartStep', 'CallExeStep','MessagePopUpStep','GenericStep', 'ActionStep']
from .steps import NumericStep,MultiNumericStep,SequenceCall,BooleanStep,MultiBooleanStep,MultiStringStep,StringStep,ChartStep,CallExeStep,MessagePopUpStep,GenericStep,ActionStep  # noqa: E402

Step.model_rebuild()
