from __future__ import annotations
from abc import abstractmethod

from report.uut.steps.measurement import BooleanMeasurement
from report.uut.steps.string_step import StringMeasurement
from ...common_types import *
from pydantic_core import core_schema

from report.chart import Chart, ChartSeries, ChartType

from ..step import Step, StepType
from ..steps import *
from .numeric_step import NumericStep, MultiNumericStep, NumericMeasurement
from .string_step import StringStep, MultiStringStep
from .boolean_step import BooleanStep, MultiBooleanStep
from .generic_step import GenericStep, FlowType
from .chart_step import ChartStep
from .action_step import ActionStep
from .comp_operator import CompOp

# ------------------------------------------------------------------------
# Custom list class with parent reference
class StepList(List[StepType]):
    """Custom list that behaves like a list but has a parent reference."""

    def __init__(self, items=None, parent: Optional["SequenceCall"] = None):  # Use string reference
        super().__init__(items or [])
        self.parent = parent

    def set_parent(self, parent: "SequenceCall"):  # Use string reference to avoid NameError
        """
        Set the correct parent reference for all elements.
        #If an item is a SequenceCall, propagate the hierarchy recursively.
        """
        self.parent = parent
        for item in self:
            if hasattr(item, "parent"):
                item.parent = parent  # Assign direct parent

            #If an item is a SequenceCall, propagate the hierarchy recursively.
            #if isinstance(item, SequenceCall):  # Ensure the parent is set recursively
            #    item.steps.set_parent(item)  # Child SequenceCall gets its own steps as children

    def append(self, item):
        """Ensure parent is set when appending."""
        if hasattr(item, "parent"):
            item.parent = self.parent
        super().append(item)

    def extend(self, iterable):
        """Ensure parent is set when extending."""
        for item in iterable:
            if hasattr(item, "parent"):
                item.parent = self.parent
        super().extend(iterable)

    def insert(self, index, item):
        """Ensure parent is set when inserting."""
        if hasattr(item, "parent"):
            item.parent = self.parent
        super().insert(index, item)

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        """Correctly handle serialization and validation for Pydantic with StepType (Union)."""
        return core_schema.list_schema(
            items_schema=handler.generate_schema(StepType),  # Handle Union[Step, NumericStep, ...]
            serialization=core_schema.plain_serializer_function_ser_schema(list),
        )

    @classmethod
    def _validate_list(cls, value):
        """Ensure the list is properly validated and converted."""
        if not isinstance(value, list):
            raise ValueError("Expected a list")
        return StepList(value)  # Convert normal lists to StepList
# ------------------------------------------------------------------------

# ------------------------------------------------------------------------
# Additional info in sequence call steps
class SequenceCallInfo(WATSBase):
    # Fields
    path: Optional[str] = Field(default=None, max_length=500, min_length=1)
    file_name: Optional[str] = Field(default=None, max_length=200, min_length=1, validation_alias="name", serialization_alias="name")
    version: Optional[str] = Field(default=None, max_length=30, min_length=1)
# ------------------------------------------------------------------------

# ------------------------------------------------------------------------
# Sequence call class
class SequenceCall(Step):
    """
    Class: SequenceCall
    
    sequence(uut):  UUTInfo
    steps:          StepList[StepType]
    """
    step_type: Literal["SequenceCall","WATS_SeqCall"] = Field(default="SequenceCall",validation_alias="stepType", serialization_alias="stepType")
    sequence: SequenceCallInfo = Field(default_factory=SequenceCallInfo, validation_alias="seqCall", serialization_alias="seqCall")

    # Child steps - Only applies to SequenceCall
    steps: Optional[StepList[Annotated[StepType, Field(discriminator='step_type')]]] = Field(default_factory=StepList)
    
    # StepList model validator - before. Converts incoming list to StepList when deserializing
    @model_validator(mode="before")
    @classmethod
    def convert_steps(cls, data):
        """
        Convert list to StepList before Pydantic validation.
        Also sets parent on all steps inside StepList during deserialization.
        """
        if isinstance(data, dict) and "steps" in data:
            steps = data["steps"]
            if isinstance(steps, list):  
                step_list = StepList(steps)
                step_list.set_parent(data) 
                data["steps"] = step_list
            else:
                step_list = StepList()
                data["steps"] = step_list
        return data
    # -------------------------------------------------------------------
    # Model validator (after)
    @model_validator(mode="after")
    def assign_parent(self):
        """Ensure all steps have the correct parent after model creation."""
        if not isinstance(self.steps, StepList):  # Fix list conversion issue
            self.steps = StepList(self.steps)  # Convert list to StepList if needed
        try:
            self.steps.set_parent(self)
        except Exception as e:
            print(f"Error setting parent: {e}")
        return self  

    # validate_step - all step types
    def validate_step(self, trigger_children=False, errors=None) -> bool:
        if errors is None:
            errors = []
        
        if not super().validate_step(trigger_children=trigger_children, errors=errors):
            return False
        
        # Sequence Call Validation:
        
        # Validate child steps
        if trigger_children:
            for step in self.steps:
                if not step.validate_step(trigger_children=trigger_children, errors=errors):
                    return False            
        
        return True
 
    # --------------------------------------------
    # AddSequenceCall() - Create a new sub-sequence below the current sequence call object 
    def add_sequence_call(self, name: str, file_name = "SequenceFilename.seq", version: str = "1.0.0.0", path: str = "NaN"):
        new_seq = SequenceCall()
        new_seq.name = name
        new_seq.sequence.file_name = file_name
        new_seq.sequence.path = path
        new_seq.sequence.version = version
        new_seq.parent = self
        self.steps.append(new_seq)
        return new_seq
    # --------------------------------------------
    # AddNumericLimitStep()
    def add_numeric_step(self, *,
                         name: str,
                         value: float,
                         unit: str = "NA",
                         comp_op: CompOp = CompOp.LOG,
                         low_limit: float = None,
                         high_limit: float = None,
                         status: str = "P", 
                         id: Optional[Union[int, str]] = None, 
                         group: str = "M", 
                         error_code: Optional[Union[int, str]] = None, 
                         error_message: Optional[str] = None, 
                         reportText: Optional[str] = None, 
                         start: Optional[str] = None, 
                         tot_time: Optional[Union[float, str]] = None):
        if status == "S":
            value = "NaN"
            comp_op = CompOp.LOG
            unit = ""
        ns = NumericStep(name=name, value=value, unit=unit, status=status, id=id, group=group, errorCode=error_code, error_message=error_message, reportText=reportText, start=start, totTime=tot_time, parent=self)
        nm = NumericMeasurement(value=value, unit=unit, status=status, comp_op=comp_op, low_limit=low_limit, high_limit=high_limit)
        ns.measurement = nm
        self.steps.append(ns)
        return ns
    
        # --------------------------------------------
    # AddNumericLimitStep()
    def add_multi_numeric_step(self, *,
                         name: str,
                         status: str = "P", 
                         id: Optional[Union[int, str]] = None, 
                         group: str = "M", 
                         error_code: Optional[Union[int, str]] = None, 
                         error_message: Optional[str] = None, 
                         reportText: Optional[str] = None, 
                         start: Optional[str] = None, 
                         tot_time: Optional[Union[float, str]] = None):
        ns = MultiNumericStep(name=name, status=status, id=id, group=group, errorCode=error_code, error_message=error_message, reportText=reportText, start=start, totTime=tot_time, parent=self)
        self.steps.append(ns)
        return ns   
    # --------------------------------------------
    # Add a single string step
    def add_string_step(self, *,
                        name: str,
                        value: str,
                        unit: str = "Na",
                        comp_op: CompOp = CompOp.LOG,
                        limit: str = None,
                        status: str = "P", 
                        id: Optional[Union[int, str]] = None, 
                        group: str = "M", 
                        error_code: Optional[Union[int, str]] = None, 
                        error_message: Optional[str] = None, 
                        report_text: Optional[str] = None, 
                        start: Optional[str] = None, 
                        tot_time: Optional[Union[float, str]] = None) -> StringStep:
        """
        """
        if status == "S":
            value = "Null"
            comp_op = CompOp.LOG
               
        ss = StringStep(name=name, value=value, unit=unit, status=status, id=id, group=group, error_code=error_code, error_message=error_message, report_text=report_text, start=start, tot_time=tot_time, parent=self)
        ss.measurement= StringMeasurement(value=value, unit=unit, status=status, comp_op=comp_op, limit=limit)
        self.steps.append(ss)
        return ss
        # --------------------------------------------
        # Add a single string step
    def add_multi_string_step(self, *,
                            name: str,
                            status: str = "P", 
                            id: Optional[Union[int, str]] = None, 
                            group: str = "M", 
                            error_code: Optional[Union[int, str]] = None, 
                            error_message: Optional[str] = None, 
                            report_text: Optional[str] = None, 
                            start: Optional[str] = None, 
                            tot_time: Optional[Union[float, str]] = None) -> MultiStringStep:
        """
        """
        ss = MultiStringStep(name=name, status=status, id=id, group=group, error_code=error_code, error_message=error_message, report_text=report_text, start=start, tot_time=tot_time, parent=self)
        self.steps.append(ss)
        return ss
    # --------------------------------------------
    # Add a single boolean step    
    def add_boolean_step(self, *,
                         name: str,
                         status: str = "P",
                         id: Optional[Union[int, str]] = None, 
                         group: str = "M", 
                         error_code: Optional[Union[int, str]] = None, 
                         error_message: Optional[str] = None, 
                         report_text: Optional[str] = None, 
                         start: Optional[str] = None, 
                         tot_time: Optional[Union[float, str]] = None) -> BooleanStep:
        """
        """
        bs = BooleanStep(name=name, status=status, id=id, group=group, errorCode=error_code, errorMessage=error_message, reportText=report_text, start=start, totTime=tot_time, parent=self)
        bs.measurement = BooleanMeasurement(status=status)        
        self.steps.append(bs)
        return bs
        # --------------------------------------------
    # Add a single boolean step    
    def add_multi_boolean_step(self, *,
                         name: str,
                         status: str = "P",
                         id: Optional[Union[int, str]] = None, 
                         group: str = "M", 
                         error_code: Optional[Union[int, str]] = None, 
                         error_message: Optional[str] = None, 
                         report_text: Optional[str] = None, 
                         start: Optional[str] = None, 
                         tot_time: Optional[Union[float, str]] = None) -> MultiBooleanStep:
        """
        """
        bs = MultiBooleanStep(name=name, status=status, id=id, group=group, errorCode=error_code, errorMessage=error_message, reportText=report_text, start=start, totTime=tot_time, parent=self)        
        self.steps.append(bs)
        return bs
    # --------------------------------------------
    # Add a chart step
    def add_chart_step(self, *,
                      name: str,
                      chart_type: ChartType,
                      status: str = "P",
                      label: str,
                      x_label: str,
                      x_unit: Optional[str],
                      y_label: str,
                      y_unit: Optional[str],
                      series: List[ChartSeries] = None,
                      id: Optional[Union[int, str]] = None, 
                      group: str = "M", 
                      error_code: Optional[Union[int, str]] = None, 
                      error_message: Optional[str] = None, 
                      report_text: Optional[str] = None, 
                      start: Optional[str] = None, 
                      tot_time: Optional[Union[float, str]] = None) -> ChartStep:
        cs = ChartStep(name=name, status=status, id=id, group=group, errorCode=error_code, errorMessage=error_message, reportText=report_text, start=start, totTime=tot_time, parent=self)
        cs.chart = Chart(chart_type=chart_type, label=label, x_label=x_label, y_label=y_label, x_unit=x_unit,y_unit=y_unit, series=series)
        self.steps.append(cs)
        return cs
    # --------------------------------------------
    # Add a generic step
    def add_generic_step(self, *,
                      step_type: FlowType,
                      name: str,
                      status: str = "P",
                      id: Optional[Union[int, str]] = None, 
                      group: str = "M", 
                      error_code: Optional[Union[int, str]] = None, 
                      error_message: Optional[str] = None, 
                      report_text: Optional[str] = None, 
                      start: Optional[str] = None, 
                      tot_time: Optional[Union[float, str]] = None) -> GenericStep:
        fs = GenericStep(name=name, step_type=step_type, status=status, id=id, group=group, errorCode=error_code, errorMessage=error_message, reportText=report_text, start=start, totTime=tot_time, parent=self)
        self.steps.append(fs)
        return fs

        
        


    # PRINT CHILD STEP HIERARCHY - For debugging
    def print_hierarchy(self, indent: int = 0):
        """Recursively print the hierarchy of SequenceCall and its steps with indentation, including parent names and class names."""
        prefix = " " * (indent * 4)  # Create indentation (4 spaces per level)
        parent_name = getattr(self.parent, "name", "None")  # Get parent name or "None"
        # Print the current SequenceCall with its class name
        print(f"{prefix}- {self.__class__.__name__}: {getattr(self, 'name', 'Unnamed')} (Parent: {parent_name}, Class: {self.__class__.__name__})")

        for step in self.steps:
            step_parent_name = getattr(step.parent, "name", "None")  # Get parent name for each step
            
            if isinstance(step, SequenceCall):  # If step is another SequenceCall, recurse
                self.print_hierarchy(step, indent + 1)
            else:
                # Print the step with its class name
                print(f"{prefix}    - {step.__class__.__name__}: {getattr(step, 'name', 'Unnamed')} (Parent: {step_parent_name}, Class: {step.step_type})")
    



