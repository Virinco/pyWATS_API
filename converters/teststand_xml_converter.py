import math
import re
import xml.etree.ElementTree as ET
from typing import List, Optional, Dict
import os
from zoneinfo import ZoneInfo
from report.chart import ChartSeries
from report.uut.step import StepStatus
from report.uut.steps import *
from report.uut.steps.callexe_step import CallExeStepInfo
from report.uut.steps.comp_operator import CompOp
from report.uut.steps.generic_step import FlowType
from report.uut.steps.message_popup_step import MessagePopupInfo
from report.uut.steps.numeric_step import NumericStep
from report.uut.uut_report import UUTReport
from report.uut.steps.sequence_call import SequenceCall, SequenceCallInfo
from report.uut.uut_info import UUTInfo
from datetime import datetime, timedelta
from uuid import UUID, uuid4

class TestStandXMLConverter:
    def __init__(self, args: Optional[Dict[str, str]] = None):
        self.parameters = args or {
            "operator": "oper",
            "operationTypeCode": "10",
            "partNumber": "PN123",
            "serialNumber": "SN123456",
            "partRevision": "1.0",
            "timezone": None,
            "location": "Drammen",
            "purpose": "Test",
        }

        self.namespaces = {
            'trc': "urn:IEEE-1636.1:2011:01:TestResults",
            'tr': "urn:IEEE-1636.1:2011:01:TestResults",
            'ts': "www.ni.com/TestStand/ATMLTestResults/2.0"
        }
        self.delete_files: List[str] = []

    def convert_report(self, file_stream):
        invalid_stylesheet_regex = re.compile(r'<\?xml:stylesheet.*\?>')

        text = file_stream.read().decode('utf-8', errors='replace')  # Read from stream
        text = invalid_stylesheet_regex.sub('', text)

        root = ET.fromstring(text)

        for report_elem in root.iter():
            if report_elem.tag == "TSReport" or report_elem.tag == "Report":
                return self.create_uut(report_elem)

        raise ValueError("TSReport or Report element was not found.")

    def clean_up(self):
        for file_path in self.delete_files:
            if os.path.exists(file_path):
                os.remove(file_path)

    def create_uut(self, report_element):
        dump = TSDumpReport(report_element)
        xp_root = dump.root_result
        xp_ts = xp_root.get_element(xp_root.element, "TS")

        xp_station_info = dump.station_info
        station_info_exists = xp_station_info.element is not None

        login_name_element = xp_station_info.get_string_value("LoginName")
        operator = ""
        if login_name_element != "":
            operator = login_name_element
        else: 
            operator = self.parameters.get("operator")
            
        #operator = xp_station_info.get_string_value("LoginName")     if station_info_exists else self.parameters.get("operator")
        station_id = xp_station_info.get_string_value("StationID") if station_info_exists else ""
        
        location = xp_station_info.get_string_value("Location", self.parameters["location"]) 
        
        if location == "":
            location = self.parameters.get("location")
        
        purpose = xp_station_info.get_string_value("Purpose", self.parameters["purpose"])
        
        if purpose == "":
            self.parameters.get("purpose")

        fixture_id = dump.uut_info.get_string_value("UUT_Fixture_ID", "NA")
        
        uut_report = UUTReport(
            pn=dump.uut_info.get_string_value("UUTPartNumber", self.parameters["partNumber"]),
            sn=dump.uut_info.get_string_value("SerialNumber", self.parameters["serialNumber"]),
            process_code=dump.uut_info.get_string_value("UUTOperationType", self.parameters["operationTypeCode"]),
            station_name=station_id,
            sequence=SequenceCallInfo(path="Path", file_name="Name", version="V"),
            rev=dump.uut_info.get_string_value("UUTPartRevisionNumber", self.parameters["partRevision"]),
            info = UUTInfo(operator=operator, fixture_id=fixture_id),
            location=location,
            purpose=purpose
        )

        if dump.ID and dump.ID != UUID(int=0):
            uut_report.id = dump.ID

        if report_element.tag == "Report":
            start_time = report_element.find("Prop[@Name='StartTime']")
            if start_time is not None:
                hours = int(start_time.find("Prop[@Name='Hours']").find("Value").text)
                minutes = int(start_time.find("Prop[@Name='Minutes']").find("Value").text)
                seconds = int(start_time.find("Prop[@Name='Seconds']").find("Value").text)
            start_date = report_element.find("Prop[@Name='StartDate']")
            if start_date is not None:
                year = int(start_date.find("Prop[@Name='Year']").find("Value").text)
                month = int(start_date.find("Prop[@Name='Month']").find("Value").text)
                day = int(start_date.find("Prop[@Name='MonthDay']").find("Value").text)

            start_date_time = datetime(year, month, day, hours, minutes, seconds)
            parsed_dt = self.parse_datetime(start_date_time)
            uut_report.start = parsed_dt

        if report_element.find(".//Prop[@Type='TEResult']/Prop[@Name='TS']/Prop[@Name='SequenceCall']/Prop[@Name='Sequence']"):
            uut_report.root.sequence.file_name = report_element.find(".//Prop[@Type='TEResult']/Prop[@Name='TS']/Prop[@Name='SequenceCall']/Prop[@Name='Sequence']").find("Value").text
        if report_element.find(".//Prop[@Type='TEResult']/Prop[@Name='TS']/Prop[@Name='SequenceCall']/Prop[@Name='SequenceFile']"):
            uut_report.root.sequence.path = report_element.find(".//Prop[@Type='TEResult']/Prop[@Name='TS']/Prop[@Name='SequenceCall']/Prop[@Name='SequenceFile']").find("Value").text
        if report_element.find(".//Prop[@Type='TEResult']/Prop[@Name='TS']/Prop[@Name='SequenceCall']/Prop[@Name='SequenceFileVersion']"):
            uut_report.root.sequence.version = report_element.find(".//Prop[@Type='TEResult']/Prop[@Name='TS']/Prop[@Name='SequenceCall']/Prop[@Name='SequenceFileVersion']").find("Value").text
        if uut_report.root.sequence.version == "" or uut_report.root.sequence.version is None:
            uut_report.root.sequence.version = "1.0.0.1"    
        uut_report.info.exec_time = report_element.find(".//Prop[@Type='TEResult']/Prop[@Name='TS']/Prop[@Name='TotalTime']").find("Value").text
        if report_element.find(".//Prop[@Type='TEResult']/Prop[@Name='Status']").find("Value").text != "Passed":
            uut_report.result = "F"

        uut_report.info.error_code = xp_root.get_int_value("Error.Code", 0)
        uut_report.info.error_message = xp_root.get_string_value("Error.Msg", None)

        # additional_data_element = dump.uut_info.get_element(dump.uut_info.element, "AdditionalData")
        # if additional_data_element is not None:
        #     additional_data_props = dump.uut_info.get_element(dump.uut_info.element, "AdditionalData").findall("Prop")
        #     if additional_data_props:
        #         for additional_data_prop in additional_data_props:
        #             xp_additional_data = XElementParser(additional_data_prop)
        #             if self.parameters["convertAdditionalDataToMiscInfo"].lower() == "true":
        #                 if xp_additional_data.element.text:
        #                     uut_report.add_misc_info(xp_additional_data.name, xp_additional_data.element.text)
        #             else:
        #                 uut_report.add_additional_data(xp_additional_data.name, xp_additional_data.element)

        #Misc Info
        misc_uut_result = dump.uut_info.get_element(dump.uut_info.element, "MiscUUTResult")
        if misc_uut_result is not None:
            xp_uut_misc_info = misc_uut_result.find("Prop[@Name='Misc_UUT_Info']")
            if xp_uut_misc_info:
                misc_values = xp_uut_misc_info.findall("Value")
                for value in misc_values:
                    misc_description = value.find("Prop[@Type='Obj']").find("Prop[@Name='Description']").find("Value").text
                    misc_data_string = value.find("Prop[@Type='Obj']").find("Prop[@Name='Data_String']").find("Value").text
                    uut_report.add_misc_info(misc_description, misc_data_string)

            #Sub unit info
            uut_part_info = misc_uut_result.find("Prop[@Name='UUT_Part_Info']")
            if uut_part_info:
                for value in uut_part_info.findall("Value"):
                    su_part_type = value.find("Prop[@TypeName='ET_UUT_Part_Info']").find("Prop[@Name='Part_Type']").find("Value").text
                    su_pn = value.find("Prop[@TypeName='ET_UUT_Part_Info']").find("Prop[@Name='Part_Number']").find("Value").text
                    su_sn = value.find("Prop[@TypeName='ET_UUT_Part_Info']").find("Prop[@Name='Part_Serial_Number']").find("Value").text
                    su_rev = value.find("Prop[@TypeName='ET_UUT_Part_Info']").find("Prop[@Name='Part_Revision_Number']").find("Value").text
                    uut_report.add_sub_unit(part_type=su_part_type, sn=su_sn, pn=su_pn, rev=su_rev)

            #Asset Info
            uut_asset_info = misc_uut_result.find("Prop[@Name='Asset_Info']")
            if uut_asset_info:
               for value in uut_asset_info.findall("Value"):
                    asset_sn = value.find("Prop[@TypeName='WATS_Asset_Info']").find("Prop[@Name='AssetSerialNumber']").find("Value").text
                    asset_usage_count = int(value.find("Prop[@TypeName='WATS_Asset_Info']").find("Prop[@Name='UsageCount']").find("Value").text)
                    uut_report.add_asset(sn=asset_sn, usage_count=asset_usage_count)  

        result_list = report_element.find(".//Prop[@Type='TEResult']/Prop[@Name='TS']/Prop[@Name='SequenceCall']/Prop[@Name='ResultList']")

        result_list_values = []
        if result_list is not None:
            result_list_values = result_list.findall("Value")

        root_seq = uut_report.get_root_sequence_call()
        

        self.add_steps(root_seq, result_list_values)
        
        uut_report.root.status = uut_report.result
        
        return uut_report

    def add_steps(self, current_seq, result_list_values):
        current_step = None
        
        if result_list_values is None:
            return
        
        for value in result_list_values:
            te_result = value.find("Prop[@Type='TEResult']")
            if te_result is not None:
                step_status = te_result.find("Prop[@Name='Status']").find("Value").text
                ts_element = te_result.find("Prop[@Name='TS']")
                if ts_element is not None:
                    if ts_element.find("Prop[@Name='StepType']"):
                        step_type = ts_element.find("Prop[@Name='StepType']").find("Value")
                        step_name = ts_element.find("Prop[@Name='StepName']").find("Value").text
                        step_group = ts_element.find("Prop[@Name='StepGroup']").find("Value").text

                        step_group = self.set_step_group(step_group)

                        if len(step_name) > 100:
                            step_name = step_name[:100]

                        step_execution_time = float(ts_element.find("Prop[@Name='TotalTime']").find("Value").text)

                        if step_type.text in ["SequenceCall", "WATS_SeqCall"]:
                                
                            if step_status.lower() == "skipped":
                                current_seq = current_seq.add_sequence_call(name=step_name)
                                current_seq.group = step_group
                                current_seq.status = StepStatus.Skipped
                                current_seq.tot_time = step_execution_time
                                current_seq = current_seq.parent
                                continue
                            
                            current_seq = self.parse_sequence_call_step(ts_element, step_group, current_seq)
                            current_seq.group = step_group
                            current_seq.tot_time = step_execution_time
                            current_seq.status = self.set_step_status(step_status)
                            current_seq = current_seq.parent

                        elif step_type.text in ["StringValueTest", "ET_SVT"]:
                            string_step = self.parse_string_step(te_result, step_name, step_group, step_status, current_seq)
                            if string_step is None:
                                continue
                            string_step.tot_time = step_execution_time
                            current_step = string_step
                        
                        elif step_type.text in ["ET_MSVT"]:
                            multi_string_step = self.parse_multi_string_step(te_result, step_name, step_group, step_status, current_seq)
                            multi_string_step.tot_time = step_execution_time
                            current_step = multi_string_step
                        
                        elif step_type.text in ["PassFailTest", "ET_PFT"]:
                            if step_status.lower() == "skipped":
                                current_seq.add_boolean_step(name=step_name, status=StepStatus.Skipped)
                                continue

                            step_result = te_result.find("Prop[@Name='PassFail']").find("Value").text
                            pass_fail_step = current_seq.add_boolean_step(name=step_name, group=step_group)

                            pass_fail_step.tot_time = step_execution_time
                            pass_fail_step.status = self.set_step_status(step_status)
                            self.check_for_error_msg(te_result, pass_fail_step)
                            current_step = pass_fail_step

                        elif step_type.text in ["ET_MPFT"]:
                            multi_boolean_step = self.parse_multi_boolean_step(te_result, step_name, step_group, step_status, current_seq)
                            multi_boolean_step.tot_time = step_execution_time
                            self.check_for_error_msg(te_result, multi_boolean_step)
                            current_step = multi_boolean_step

                        elif step_type.text in ["NumericLimitTest", "ET_NLT"]:

                            numeric_step = self.parse_numeric_step(te_result, step_name, step_group, step_status, current_seq)
                            numeric_step.tot_time = step_execution_time
                            self.check_for_error_msg(te_result, numeric_step)
                            current_step = numeric_step

                        elif step_type.text in ["NI_MultipleNumericLimitTest", "ET_MNLT"]:
                            
                            if step_status.lower() == "skipped":
                                current_seq.add_multi_numeric_step(name=step_name, group=step_group, status=StepStatus.Skipped)
                                continue

                            mlt_numeric_step = self.parse_multi_numeric_step(te_result, step_name, step_group, step_status, current_seq)
                            mlt_numeric_step.tot_time = step_execution_time
                            mlt_numeric_step.status = self.set_step_status(step_status)
                            self.check_for_error_msg(te_result, mlt_numeric_step)
                            current_step = mlt_numeric_step

                        elif step_type.text in FlowType._value2member_map_:
                            status = self.set_step_status(step_status)
                            step_type = FlowType(step_type.text)
                            generic_step = current_seq.add_generic_step(step_type=step_type, name=step_name, group=step_group, status=status)
                            generic_step.tot_time = step_execution_time
                            self.check_for_error_msg(te_result, generic_step)
                            current_step = generic_step

                        elif step_type.text == "MessagePopup":
                            
                            status = self.set_step_status(step_status)
                            message_pop_up_step = MessagePopUpStep(name=step_name, messagePopup=MessagePopupInfo(), group=step_group, step_status=status,tot_time=step_execution_time, parent=current_seq)
                            
                            if te_result.find("Prop[@Name='ButtonHit']"):
                                if te_result.find("Prop[@Name='ButtonHit']").find("Value").text is not None:
                                    message_pop_up_step.messagePopup.button = int(te_result.find("Prop[@Name='ButtonHit']").find("Value").text)
                            
                            if te_result.find("Prop[@Name='Response']"):
                                if te_result.find("Prop[@Name='Response']").find("Value").text is not None:
                                    message_pop_up_step.messagePopup.response = te_result.find("Prop[@Name='Response']").find("Value").text
                            
                            self.check_for_error_msg(te_result, message_pop_up_step)
                            current_seq.steps.append(message_pop_up_step)
                            current_step = message_pop_up_step

                        elif step_type.text == "CallExecutable":
                            status = self.set_step_status(step_status)
                            call_exe_step = CallExeStep(name=step_name, callExe=CallExeStepInfo(), group=step_group, step_status=status, tot_time=step_execution_time, parent=current_seq)
                            call_exe_step.callExe.exit_code = int(te_result.find("Prop[@Name='ExitCode']").find("Value").text)
                            self.check_for_error_msg(te_result, call_exe_step)
                            current_seq.steps.append(call_exe_step)
                            current_step = call_exe_step

                        elif step_type.text == "WATS_XYGMNLT":
                            chart_step = self.parse_chart_step(te_result, step_name, step_group, step_status, current_seq)
                            self.check_for_error_msg(te_result, chart_step)
                            current_step = chart_step

                step_report_text = te_result.find("Prop[@Name='ReportText']")
                
                if step_report_text is not None and current_step is not None:
                    current_step.report_text = step_report_text.find("Value").text

    #Parse Sequence Call Step
    def parse_sequence_call_step(self, ts_element, step_group, current_seq) -> SequenceCall:
        
        sequence_name = ts_element.find("Prop[@Name='StepName']").find("Value").text
        sequence_file_path = " "
        sequence_version = " "

        if ts_element.find("Prop[@Name='SequenceCall']") is not None:
            sequence_file_element = ts_element.find("Prop[@Name='SequenceCall']").find("Prop[@Name='SequenceFile']")
            if sequence_file_element is not None:
                sequence_file_path = sequence_file_element.find("Value").text
                
            sequence_version_element = ts_element.find("Prop[@Name='SequenceCall']").find("Prop[@Name='SequenceFileVersion']")
            if sequence_version_element is not None:
                sequence_version = sequence_version_element.find("Value").text
        
        current_seq = current_seq.add_sequence_call(name=sequence_name, path=sequence_file_path, version=sequence_version)
        
        sequence_call_element = ts_element.find("Prop[@Name='SequenceCall']")
        
        if sequence_call_element is not None:
            result_list = sequence_call_element.find("Prop[@Name='ResultList']")
            current_seq.group = step_group
            self.add_steps(current_seq, result_list)
        
        return current_seq
    
    #Parse String Step
    def parse_string_step(self, te_result, step_name, step_group, step_status, current_seq) -> StringStep:
        # if step_status.lower() == "skipped":
        #     string_step = current_seq.add_string_step(name=step_name, value="", status="S")
        #     return string_step
        
        string_measurement = te_result.find("Prop[@Name='String']")
        
        if string_measurement is not None:
            string_measurement = string_measurement.find("Value").text

            if string_measurement is None:
                string_measurement = ""
            elif len(string_measurement) > 100:
                string_measurement = string_measurement[:100]

        comp_op = te_result.find("Prop[@Name='Comp']")
        if comp_op is not None:
            comp_op = comp_op.find("Value").text
            comp_op = self.get_comp_op(comp_op)
        
        string_limit = ""
        if comp_op != "LOG":
            string_limit_element = te_result.find("Prop[@Name='Limits']/Prop[@Name='String']/Value")
            if string_limit_element is not None and string_limit_element.text is not None:
                string_limit = string_limit_element.text[:100]
        
        step_status = self.set_step_status(step_status)
        if comp_op == "LOG":
            string_step = current_seq.add_string_step(name=step_name, value=string_measurement, comp_op=CompOp(comp_op.upper()), group=step_group, status=step_status)
        else:
            string_step = current_seq.add_string_step(name=step_name, value=string_measurement, comp_op=CompOp(comp_op.upper()), limit=string_limit, group=step_group, status=step_status)
        return string_step
    
    #Parse Multi String Step
    def parse_multi_string_step(self, te_result, step_name, step_group, step_status, current_seq) -> MultiStringStep:
        status = self.set_step_status(step_status)
        mlt_string_step = current_seq.add_multi_string_step(name=step_name,status=status, group=step_group)
        values = te_result.find("Prop[@Name='Measurement']").findall("Value")

        for value in values:
            
            measurement_name = value.find("Prop[@Type='Obj']").find("Prop[@Name='MeasName']").find("Value").text
            measurement_value = value.find("Prop[@Type='Obj']").find("Prop[@Name='StringData']").find("Value").text
            
            if measurement_value is None:
                measurement_value = ""

            comp_op = self.parse_value(value.find("Prop[@Type='Obj']").find("Prop[@Name='Comp']").find("Value").text)
            string_limit = value.find("Prop[@Type='Obj']").find("Prop[@Name='StringLimit']").find("Value").text

            if comp_op != "LOG" and string_limit is None:
                string_limit = ""

            measure_status = self.set_step_status(value.find("Prop[@Type='Obj']").find("Prop[@Name='Status']").find("Value").text)

            mlt_string_step.add_measurement(name=measurement_name, value=measurement_value, status=measure_status, comp_op=CompOp(comp_op), limit=string_limit)
            mlt_string_step.status = self.set_step_status(step_status)

        return mlt_string_step

    #Parse Multi Boolean Step
    def parse_multi_boolean_step(self, te_result, step_name, step_group, step_status, current_seq) -> MultiBooleanStep:
        step_status = self.parse_value(step_status)
        mlt_boolean_step = current_seq.add_multi_boolean_step(name=step_name, group=step_group, status=step_status)
        
        values = te_result.find("Prop[@Name='Measurement']").findall("Value")
        
        for value in values: 
            measure_name = value.find("Prop[@Type='Obj']").find("Prop[@Name='MeasName']").find("Value").text
            measure_status = self.parse_value(value.find("Prop[@Type='Obj']").find("Prop[@Name='PassFail']").find("Value").text)
            mlt_boolean_step.add_measurement(name=measure_name, status=measure_status)
        
        return mlt_boolean_step
    
    #Parse Chart step
    def parse_chart_step(self, te_result: ET.Element, step_name: ET.Element, step_group : ET.Element, step_status, current_seq: SequenceCall) -> ChartStep:
        
        chart_label = te_result.find("Prop[@Name='Chart']").find("Prop[@Name='ChartLabel']").find("Value").text
        
        x_label = te_result.find("Prop[@Name='Chart']").find("Prop[@Name='Xlabel']").find("Value").text
        y_label = te_result.find("Prop[@Name='Chart']").find("Prop[@Name='Ylabel']").find("Value").text
        x_unit = te_result.find("Prop[@Name='Chart']").find("Prop[@Name='Xunit']").find("Value").text
        y_unit = te_result.find("Prop[@Name='Chart']").find("Prop[@Name='Yunit']").find("Value").text
        
        chart_type = te_result.find("Prop[@Name='Chart']").find("Prop[@Name='ChartType']").find("Value").text

        plots_element = te_result.find("Prop[@Name='Chart']").find("Prop[@Name='Plots']")
        plot_name = plots_element.find("ArrayElementPrototype").find("Prop[@Name='PlotName']").find("Value").text
        
        chart_series_list = []

        for value_element in plots_element.findall("Value"):

            plot_name = value_element.find("Prop[@Type='Obj']").find("Prop[@Name='PlotName']").find("Value").text
            plot_data_element = value_element.find("Prop[@Type='Obj']").find("Prop[@Name='PlotData']").findall("Value")
            
            chart_series = ChartSeries(name=plot_name)
            
            x_values = []
            y_values = []

            for value_element in plot_data_element:
                    value_id = value_element.get('ID')
                    if value_id.startswith('[0]'):
                        x_value = self.parse_value(value_element.text)
                        x_values.append(x_value)
                    elif value_id.startswith('[1]'):
                        y_value = self.parse_value(value_element.text)
                        y_values.append(y_value)

            chart_series.x_data = ";".join(map(str,x_values))
            chart_series.y_data = ";".join(map(str,y_values))     
            chart_series_list.append(chart_series)

        chart_status = self.parse_value(step_status)
        chart_step = current_seq.add_chart_step(name=step_name, group=step_group, label=chart_label, x_label=x_label, y_label=y_label, x_unit=x_unit, y_unit=y_unit, chart_type=chart_type, series=chart_series_list, status=chart_status)
        
        measurements = te_result.findall(".//Prop[@Type='Obj'][@TypeName='NI_LimitMeasurement']")
        #Debug to curcumvent the issue with steps that only have one measurement
        if len(measurements) > 1:
            for measurement in measurements:
                measurement_name = measurement.get("Name")
                measurement_data = self.extract_numeric(measurement.find("Prop[@Name='Data']").find("Value").text)
                #measure_unit = measurement.find("Prop[@Name='Units']").find("Value").text
                measurement_comp = self.parse_value(measurement.find("Prop[@Name='Comp']").find("Value").text)

                measure_low_limit = self.extract_numeric(measurement.find("Prop[@Name='Limits']").find("Prop[@Name='Low']").find("Value").text)
                measure_high_limit = self.extract_numeric(measurement.find("Prop[@Name='Limits']").find("Prop[@Name='High']").find("Value").text)
                
                measure_status = self.parse_value(measurement.find("Prop[@Name='Status']").find("Value").text)

                chart_step.add_measurement(name=measurement_name, value=measurement_data, comp_op=CompOp(measurement_comp), low_limit=measure_low_limit, high_limit=measure_high_limit, status=measure_status)
        return chart_step              
    
    #Parse Numeric step
    def parse_numeric_step(self, te_result, step_name, step_group, step_status, current_seq) -> NumericStep:
        step_measurement = self.extract_numeric(te_result.find("Prop[@Name='Numeric']").find("Value").text)
        
        if step_measurement is None:
            step_measurement = 0.0
        limits_element = te_result.find("Prop[@Name='Limits']")
        low_limit_element = limits_element.find("Prop[@Name='Low']")
        high_limit_element = limits_element.find("Prop[@Name='High']")

        low_limit, high_limit = None, None

        if low_limit_element is not None:
            low_limit =  self.extract_numeric(low_limit_element.find("Value").text)
        if high_limit_element is not None:
            high_limit = self.extract_numeric(high_limit_element.find("Value").text)

        step_units_element = te_result.find("Prop[@Name='Units']")
        
        step_unit = ""
        if step_units_element is not None:
            step_unit = step_units_element.find("Value").text
            step_unit = step_unit[:20]
        step_comp = te_result.find("Prop[@Name='Comp']").find("Value").text
        com_op = CompOp(step_comp)

        #If comp_op uses only one limit (e.g., "LT" or "LE"), the server uses low_limit.
        if step_comp in ["LT", "LE"]:
            if low_limit is None and high_limit is not None:
                low_limit = high_limit
                high_limit = None

        step_status = self.set_step_status(step_status)
        numeric_step = current_seq.add_numeric_step(name=step_name, value=step_measurement, unit=step_unit, low_limit=low_limit, high_limit=high_limit, comp_op=com_op, group=step_group, status=step_status)

        return numeric_step
    
    #Parse Multi Numeric Step
    def parse_multi_numeric_step(self, te_result, step_name, step_group, step_status, current_seq) -> MultiNumericStep:
        
        current_step = current_seq.add_multi_numeric_step(name=step_name, group=step_group)
        self.check_for_error_msg(te_result, current_step)

        measurement = te_result.find("Prop[@Name='Measurement']")
        values = measurement.findall("Value")

        for value in values:                                
            measure = value.find("Prop[@TypeName='NI_LimitMeasurement']")
            measurement_name = measure.get("Name")

            measurement_name = measurement_name[:100]

            step_measurement = self.extract_numeric(measure.find("Prop[@Name='Data']").find("Value").text)

            limits_element = measure.find("Prop[@Name='Limits']")
            low_limit_element = limits_element.find("Prop[@Name='Low']")
            high_limit_element = limits_element.find("Prop[@Name='High']")

            low_limit, high_limit = None, None

            if low_limit_element is not None:
                low_limit =  self.extract_numeric(low_limit_element.find("Value").text)
                
            if high_limit_element is not None:
                high_limit = self.extract_numeric(high_limit_element.find("Value").text)

            step_units_element = measure.find("Prop[@Name='Units']")
            
            step_unit = ""
            if step_units_element is not None:
                step_unit = step_units_element.find("Value").text
                step_unit = step_unit[:20]

            measure_status = measure.find("Prop[@Name='Status']").find("Value").text

            if measure_status.lower() == "passed":
                measure_status = "P"
            elif measure_status.lower() == "failed":
                measure_status = "F"
                current_step.status = StepStatus.Failed
                current_seq.status = StepStatus.Failed
            
            step_comp = measure.find("Prop[@Name='Comp']").find("Value").text
            
            current_step.add_measurement(name=measurement_name, value=step_measurement, unit=step_unit, low_limit=low_limit, high_limit=high_limit, comp_op=CompOp(step_comp), status=measure_status)

            
        return current_step
    
    # Method to parse the datetime string
    def parse_datetime(self, parsed_dt):
        try:
            
            # Get the timezone from self.parameters["timeZone"]
            time_zone_str = self.parameters["timezone"]
            
            # Get the local timezone
            if time_zone_str is not None:
                try:
                    # Try to get the timezone using zoneinfo (Python 3.9+)
                    local_tz = ZoneInfo(time_zone_str)
                except Exception as e:
                    print(f"Invalid timezone '{time_zone_str}' provided. Falling back to local timezone. Error: {e}")
                    # Fallback to local timezone if the timezone is invalid
                    local_tz = datetime.now().astimezone().tzinfo
            else:
                # If no timezone string is provided, fallback to local system timezone
                local_tz = datetime.now().astimezone().tzinfo

            # Localize the datetime (assign the timezone)
            localized_dt = parsed_dt.replace(tzinfo=local_tz)
            
            # Format as ISO string with timezone offset
            formatted_dt = localized_dt.strftime("%Y-%m-%dT%H:%M:%S%z")
            
            return formatted_dt

        except ValueError as e:
            print(f"Error parsing the datetime string: {e}")
            return None
            
    # Method to extract numeric part from a string
    def extract_numeric(self, value: str) -> Optional[float]:
        if value.lower() == "nan":
            return math.nan
        elif value.lower() == "inf":
            return math.inf
        elif value.lower() == "-inf":
            return -math.inf
        else:
            match = re.search(r"(?P<numeric>[-+]?\d*\.?\d+)", value)
            if match:
                return float(match.group("numeric"))
        return None      
    
    #Parse Value element
    def parse_value(self, value: str) -> str:
        if value.lower() == "nan":
            return "NaN"
        elif value.lower() == "inf":
            return "Inf"
        elif value.lower() == "-inf":
            return "-Inf"
        elif value.lower() == "equal":
            return "EQ"
        elif value.lower() == "passed":
            return "P"
        elif value.lower() == "failed":
            return "F"
        elif value.lower() == "skipped":
            return "S"
        elif value.lower() == "true":
            return "P"
        elif value.lower() == "false":
            return "F"
        return value
    
    # Method to determine step status                          
    def set_step_status(self, step_status: str) -> StepStatus:
        """
        Method to get the status code based on the step status.
        :param step_status: The status of the step.
        :return: The corresponding status code.
        """
        status_map = {
            "failed": StepStatus.Failed,
            "skipped": StepStatus.Skipped,
            "terminated": StepStatus.Terminated,
            "done": StepStatus.Done
        }
        return status_map.get(step_status.lower(), StepStatus.Passed)
    
    # Method to check for error message
    def check_for_error_msg(self, te_result, current_step):
        error_msg = te_result.find("Prop[@Name='Error']").find("Prop[@Name='Msg']").find("Value").text
        error_code = te_result.find("Prop[@Name='Error']").find("Prop[@Name='Code']").find("Value").text
        if error_msg is not None or error_msg != "":
            current_step.error_message = error_msg
        if error_code is not None or error_code != "":
            current_step.error_code = error_code

    #Set Step Group
    def set_step_group(self, step_group: str) -> str:
        
        if step_group == "Setup":
            step_group = "S"
        elif step_group == "Cleanup":
            step_group = "C"
        else:
            step_group = "M"
        return step_group
    
    #Get Comp Operator
    def get_comp_op(self, comp_op) -> str:
        if "CASESENSITIVE" in comp_op.upper():
                comp_op = "CASESENSIT"
        elif "IGNORECASE" in comp_op.upper():
                comp_op = "IGNORECASE"
        return comp_op

############################################################
"""
    Serializer.XElementParser.cs
"""
class XElementParser:
    def __init__(self, element: ET.Element, name_path: Optional[str] = None):
        self.element = self.get_element(element, name_path) if name_path else element
        self.datatype = self.get_data_type(self.element.get("Type")) if self.element is not None else None

    @staticmethod
    def create(element: ET.Element, name_path: Optional[str] = None):
        tmp_element = XElementParser.get_element(element, name_path)
        if tmp_element is None:
            return None
        else:
            return XElementParser(tmp_element)

    @staticmethod
    def get_element(element: ET.Element, name_path: Optional[str]) -> Optional[ET.Element]:
        if name_path is None:
            return element
        path = name_path.split('.')
        for p in path:
            found = False
            for child in element.findall("Prop"):
                if child.get("Name") == p:
                    element = child
                    found = True
                    break
            if not found:
                print(f"Element not found for path: {name_path}, part: {p}")
                return None
        print(f"Element found for path: {name_path}")
        return element

    @staticmethod
    def get_data_type(type_string: Optional[str]) -> Optional[type]:
        if type_string is None:
            return None
        return {
            "String": str,
            "Boolean": bool,
            "Number": float,
            "Array": list,
            "TEResult": dict,  # Placeholder for actual TEResult type
            "Obj": object
        }.get(type_string, object)

    def get_string_value(self, name_path: str, default: str = "") -> str:
        element = self.get_element(self.element, name_path)
        if element is None:
            print(f"String value not found for path: {name_path}, returning default: {default}")
            return default
        value_element = element.find("Value")
        if value_element is None:
            print(f"Value element not found for path: {name_path}, returning default: {default}")
            return default
        return value_element.text.strip() if value_element.text else default

    def get_int_value(self, name_path: str, default: int = 0) -> int:
        value = self.get_string_value(name_path, str(default))
        try:
            return int(float(value))
        except ValueError:
            return default

    def get_double_value(self, name_path: str, default: float = 0.0) -> float:
        value = self.get_string_value(name_path, str(default))
        try:
            return float(value)
        except ValueError:
            return default

    def get_boolean_value(self, name_path: str, default: bool = False) -> bool:
        value = self.get_string_value(name_path, str(default))
        return value.lower() in ("true", "1")

    def exists(self, name_path: str) -> bool:
        return self.get_element(self.element, name_path) is not None


############################################################
"""
    Serializer.TSDumpReport.cs
"""
class TSDumpReport:
    def __init__(self, root: ET.Element):
        self._root = root
        guid = self.get_report_info("ID")
        self.ID = UUID(guid) if guid else uuid4()

        start = self.get_report_info("Start")
        start_utc = self.get_report_info("StartUTC")
        engine_started = self.get_report_info("EngineStarted")
        report_written = self.get_report_info("ReportWritten")

        self.Start = datetime.fromisoformat(start) if start else None
        self.StartUTC = datetime.fromisoformat(start_utc) if start_utc else None
        self.EngineStarted = datetime.fromisoformat(engine_started) if engine_started else None
        self.ReportWritten = datetime.fromisoformat(report_written) if report_written else None

    @property
    def main_result(self) -> XElementParser:
        parser = XElementParser(self._root)
        if parser.exists("MainSequenceResults"):
            return XElementParser(self._root, "MainSequenceResults")
        else:
            x_element = next((el for el in self._root.findall("Prop") if el.get("Type") == "TEResult"), None)
            return XElementParser(x_element)

    @property
    def uut_info(self) -> XElementParser:
        return XElementParser(self._root, "UUT")

    @property
    def station_info(self) -> XElementParser:
        return XElementParser(self._root, "StationInfo")

    @property
    def time_details(self) -> XElementParser:
        return XElementParser(self._root, "StartTime")

    @property
    def date_details(self) -> XElementParser:
        return XElementParser(self._root, "StartDate")

    @property
    def root_result(self) -> Optional[XElementParser]:
        mr = self.main_result
        atr_type = mr.element.get("Type")

        if atr_type == "TEResult":
            return XElementParser(mr.element)
        elif atr_type == "Array":
            value_element = mr.element.find("Value")
            if value_element is not None:
                prop_element = next((el for el in value_element.findall("Prop") if el.get("Type") == "TEResult"), None)
                return XElementParser(prop_element)
        return None

    def get_report_info(self, key: str) -> Optional[str]:
        report_info = next((t for t in self._root.findall("ReportInfo") if t.get("key") == key), None)
        return report_info.get("value") if report_info is not None else None

    ############################################################
    """
       Serializer.XElementParser.TEResult.cs
    """
class TEResult(XElementParser):
    def __init__(self, element, name_path=None):
        super().__init__(element, name_path)

    @property
    def is_sequence_call(self):
        return self.exists("TS.SequenceCall")

    @property
    def step_order_number(self):
        return self.get_int_value("TS.Id", -1)

    @property
    def step_index(self):
        return self.get_int_value("TS.Index", -1)

    @property
    def step_id(self):
        return self.get_string_value("TS.StepId", "")

    @property
    def step_id_as_guid(self):
        return self.parse_ts_guid_string(self.step_id)

    @property
    def step_group(self):
        return self.get_string_value("TS.StepGroup", "")

    @property
    def step_type(self):
        return self.get_string_value("TS.StepType", "")

    @property
    def step_name(self):
        return self.get_string_value("TS.StepName", "")

    @property
    def step_status_text(self):
        return self.get_string_value("Status", "")

    @property
    def sequence_name(self):
        return self.get_string_value("TS.SequenceCall.Sequence", "")

    @property
    def sequence_file_name(self):
        return self.get_string_value("TS.SequenceCall.SequenceFile", "")

    @property
    def sequence_file_version(self):
        return self.get_string_value("TS.SequenceCall.SequenceFileVersion", None) or self.get_string_value("SeqFileVersion", "")

    @property
    def start_time(self):
        return self.get_double_value("TS.StartTime", 0)

    @property
    def error_code(self):
        return self.get_int_value("Error.Code")

    @property
    def error_message(self):
        return self.get_string_value("Error.Msg", "")

    @property
    def step_time(self):
        return self.get_double_value("TS.TotalTime", 0)

    @property
    def module_time(self):
        return self.get_double_value("TS.ModuleTime", 0)

    @property
    def step_caused_sequence_failure(self):
        return self.get_boolean_value("StepCausedSequenceFailure", False)

    @property
    def report_text(self):
        return self.get_string_value("ReportText", "")

    def get_children(self, path):
        children = self.get_element(self.element, path)
        if children is not None:
            return children.findall("Value")
        else:
            return []

    @property
    def measurements(self):
        children = self.get_element(self.element, "Measurement")
        if children is not None and children.element is not None:
            return children.element.findall("Value")
        else:
            return []

    @property
    def additional_results(self):
        return self.get_values("AdditionalResults")

    # def get_chart_data(self):
    #     return Chart(self.get_element(self.element, "Chart").element)

    ############################################################
    """
       Serializer.XElementParser.TSUUTReport.cs
    """

    class TSUUTReport(UUTReport):

        def __init__(self, api_ref, create_header: bool, engine_started: datetime, operator_name: str, sequence_name: str, sequence_version: str, initialize_root_sequence: bool):
            super().__init__(api_ref, create_header)
            self._engine_started = engine_started
            self.initialize_uut_header(operator_name, sequence_name, sequence_version, initialize_root_sequence)
            self._meas_order_number = 0

        def get_start_time(self, ts_engine_time: float) -> datetime:
            if ts_engine_time > 0:
                return self._engine_started + timedelta(seconds=ts_engine_time)
            else:
                return self._engine_started
