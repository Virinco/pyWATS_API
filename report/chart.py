
from __future__ import annotations

from enum import Enum
from typing import Any, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from report.wats_base import WATSBase

class ChartType(Enum):
    LINE = "Line"
    LINE_LOG_XY = "LineLogXY"
    LINE_LOG_X = "LineLogX"
    LINE_LOG_Y = "LineLogY"

class ChartSeries(WATSBase):
    """
    A series in a chart.
    """

    data_type: str = Field(default="XYG", 
                           min_length=1, 
                           validation_alias="dataType",
                           serialization_alias="dataType", 
                           error_messages={'required': 'data_type is rquired'})
    """
    The data type of series.
    """
    name: str = Field(..., max_length=100, min_length=1, error_messages={'name': 'data_type is rquired'})
    """
    The name of the series.
    """
    x_data: Optional[str] = Field(default=None, 
                                  min_length=1, 
                                  validation_alias="xdata", 
                                  serialization_alias="xdata")
    """
    A semicolon (;) separated list of values on the x-axis.
    """
    y_data: Optional[str] = Field(default=None, 
                        min_length=1, 
                        validation_alias="ydata",
                        serialization_alias="ydata", 
                        error_messages={'required': 'y_data is rquired'})
    """
    A semicolon (;) separated list of values on the y-axis.
    """


class Chart(WATSBase):
    """
    A step type that contains a chart.
    """

    chart_type: ChartType = Field(default=ChartType.LINE, 
                                  validation_alias="chartType",
                                  serialization_alias="chartType")
    """
    The type of chart.
    """
    label: str = Field(..., max_length=100, min_length=1)
    """
    The name of the chart.
    """
    x_label: str = Field(..., max_length=50, min_length=1, validation_alias="xLabel", serialization_alias="xLabel")
    """
    The name of the x-axis.
    """
    x_unit: Optional[str] = Field(default=None, max_length=20, min_length=0, validation_alias="xUnit", serialization_alias="xUnit")
    """
    The unit of the x-axis.
    """
    y_label: str = Field(..., max_length=50, min_length=1, validation_alias="yLabel", serialization_alias="yLabel")
    """
    The name of the y-axis.
    """
    y_unit: Optional[str] = Field(default=None, max_length=20, min_length=0, validation_alias="yUnit", serialization_alias="yUnit")
    """
    The unit of the y-axis.
    """
    series: list[ChartSeries] = Field(default_factory=list)
    """
    A list of chart series.
    """

        
    def AddSeries(self, name: str, y_label:str, y_values: List[float], x_label: str, x_values: List[float] = None) -> ChartSeries:        
        y_data = ";".join(map(str,y_values))
        x_data = None
        if(x_values is not None):
            x_data = ";".join(map(str, x_values))       
        serie = ChartSeries(name=name, xdata=x_data, x_label=x_label, ydata=y_data, y_label=y_label)
        self.series.append(serie)
        return serie


