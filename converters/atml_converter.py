
from datetime import datetime
import xml.etree.ElementTree as ET
from typing import Dict, Optional
from zoneinfo import ZoneInfo

from report.uut.step import Step
from report.uut.steps.action_step import ActionStep
from report.uut.steps.comp_operator import CompOp
from report.uut.steps.generic_step import FlowType
from report.uut.steps.message_popup_step import MessagePopUpStep, MessagePopupInfo
from report.uut.steps.sequence_call import SequenceCallInfo
from report.uut.uut_info import UUTInfo
from report.uut.uut_report import UUTReport


class ATMLConverter:
    
    def convert_report(self, file_stream):
        text = file_stream.read()
        tree = ET.ElementTree(ET.fromstring(text))
        root = tree.getroot()
        trc, tr, ts, xsi, c = self.get_namespaces(root)

        if trc is None:  # No collection container, root is TestResults
            uut = self.create_report_header(root)
            current_sequence = uut.get_root_sequence_call()
            #process_elements(uut, tree.find(f".//{{{tr}}}ResultSet").find(f".//{{{tr}}}TestGroup"), current_sequence)
            #process_result_set_properties(uut, tree.find(f".//{{{tr}}}TestResults"))
            return uut
        else:
            for test_results in root.findall(f".//{{{trc}}}TestResults"):
                uut = self.create_report_header(test_results, trc, tr, ts, xsi, c)
                return uut
        
        return None
    
    def __init__(self, args: Optional[Dict[str, str]] = None):
        self.parameters = args or {
            "operator": "oper",
            "operationTypeCode": "10",
            "partNumber": "PN123",
            "serialNumber": "SN123456",
            "partRevision": "1.0",
            "sequenceName": "Sequence Name",
            "sequenceVersion": "1.0.0.0",
            "stationName": "Test Machine",
            "timezone": None,
            "location": "Drammen",
            "purpose": "Test",
        }

    def create_report_header(self, test_results, trc, tr, ts, xsi, c):
        
        # Create the namespaces dictionary
        namespaces = {
            'tr': tr,  # Map the 'tr' prefix to the correct namespace URI
            'ts': ts,  # If you need other namespaces, map them as well
            'xsi': xsi,
            'c': c
        }
        uut_definition = None

        uut_element = test_results.find(".//{{{}}}UUT".format(tr), namespaces)
        if uut_element:
            uut_definition = uut_element.find(".//{{{}}}Definition".format(c), namespaces)
        else:
            raise ValueError("UUT element not found in ATML file")
          
        part_number = self.get_part_number(uut_definition, c, namespaces)            
        serial_number = self.get_serial_number(uut_element, c, namespaces)
        operator_name = self.get_operator_name(test_results, tr, namespaces)
        station_name = self.get_station_name(test_results, tr, c, namespaces)
        sequence_name = self.get_sequence_name(test_results, tr, namespaces)

        current_uut = UUTReport(
            pn=part_number,
            sn=serial_number,
            process_code=self.parameters["operationTypeCode"],
            info=UUTInfo(operator=operator_name),
            station_name=station_name,
            rev=self.parameters["partRevision"],
            location=self.parameters["location"],
            purpose=self.parameters["purpose"]
        )

        current_uut.root.sequence = SequenceCallInfo(path="Path", file_name=sequence_name, version=self.parameters["sequenceVersion"])
        
        start_date_time_str, end_date_time_str = self.get_date_time_values(test_results, tr, namespaces)
        
        #Parse datetime string to datetime object
        parsed_dt = datetime.strptime(start_date_time_str, "%Y-%m-%dT%H:%M:%S.%f")

        formatted_dt = self.parse_datetime(parsed_dt)

        current_uut.start = formatted_dt
        
        end_date_time = datetime.strptime(end_date_time_str, "%Y-%m-%dT%H:%M:%S.%f")
        time_difference = end_date_time - parsed_dt

        current_uut.info.exec_time = time_difference.total_seconds()

        self.process_result_set(current_uut, test_results, tr, ts, c, namespaces)

        return current_uut
    
    def process_result_set(self, current_uut, test_results, tr, ts, c, namespaces):
        
        result_set_element = test_results.find(".//{{{}}}ResultSet".format(tr))
        current_seq = current_uut.get_root_sequence_call()
        current_seq.sequence.path = result_set_element.attrib.get("name").split("#")[0]
        current_uut.result = self.add_steps(result_set_element, current_seq, tr, ts, c, namespaces)
    
    def add_steps(self, result_set_element, current_sequence, tr, ts, c, namespaces):
        uut_status = "P"
        current_step = None
        
        if result_set_element is not None:
            
            for element in result_set_element:
                element_name = element.tag.split("}")[-1]
                
                if element_name == "TestGroup":
                    full_sequence_name = element.attrib.get("name", None)
                    sequence_name = element.attrib.get("callerName", None)
                    
                    if sequence_name is None:
                        sequence_name = full_sequence_name.split("#")[1]
                    
                    file_path = full_sequence_name.split("#")[0]
                    current_sequence = current_sequence.add_sequence_call(name=sequence_name,file_name=file_path, path=file_path, )
                    
                    step_type, step_group, step_time = self.parse_step_properties(element, tr, ts, namespaces)

                    outcome = element.find(".//{{{}}}Outcome".format(tr), namespaces)
                    step_result = self.parse_step_status(outcome, element, tr, namespaces)
                    
                    if step_result == "S":
                        continue
                    else:
                        current_sequence.status = step_result
                        if step_result == "F":
                            current_sequence.parent.status = "F"
                            uut_status = "F"

                    current_sequence.group = step_group
                    current_sequence.tot_time = step_time

                    self.add_steps(element, current_sequence, tr, ts, c, namespaces)
                    
                    current_sequence = current_sequence.parent

                elif element_name == "SessionAction":
                    current_step = None
                    step_name = element.attrib.get("name", None)
                    step_type, step_group, step_time = self.parse_step_properties(element, tr, ts, namespaces)
                    
                    action_outcome = element.find(".//{{{}}}ActionOutcome".format(tr), namespaces)
                    step_result = self.parse_step_status(action_outcome, element, tr, namespaces)
                    
                    if step_type in ["Action", "AdditionalResults"]:
                        current_step = ActionStep(name=step_name, group=step_group, status=step_result, tot_time=step_time)
                        current_sequence.steps.append(current_step)
                    elif step_type == "MessagePopup":
                        button_hit = self.get_button_hit(element, tr, c, namespaces)
                        
                        current_step = MessagePopUpStep(name=step_name, group=step_group, status=step_result, tot_time=step_time, messagePopup=MessagePopupInfo())
                        if button_hit is not None:
                            current_step.messagePopup.button = int(button_hit)
                        current_sequence.steps.append(current_step)
                    elif step_type in FlowType._value2member_map_:
                        current_step = current_sequence.add_generic_step(name=step_name, step_type=step_type, group=step_group, status=step_result, tot_time=step_time)
                
                elif element_name == "Test":
                    step_name = element.attrib.get("name", None)
                    step_type, step_group, step_time = self.parse_step_properties(element, tr, ts, namespaces)

                    if step_type == "NumericLimitTest":
                        outcome = element.find(".//{{{}}}Outcome".format(tr), namespaces)
                        step_result = self.parse_step_status(outcome, element, tr, namespaces)

                        measurement_value, low_limit, high_limit, comp_oper, unit = self.parse_numeric_step(element, tr, ts, c, namespaces)
                        current_step = current_sequence.add_numeric_step(name=step_name, value=measurement_value, low_limit=low_limit, high_limit=high_limit, comp_op=comp_oper, unit=unit, group=step_group, status=step_result, tot_time=step_time)
                    
                    elif step_type == "PassFailTest":
                        outcome = element.find(".//{{{}}}Outcome".format(tr), namespaces)
                        step_result = self.parse_step_status(outcome, element, tr, namespaces)

                        current_step = current_sequence.add_boolean_step(name=step_name, status=step_result, group=step_group, tot_time=step_time)
                        
                    elif step_type == "StringValueTest":
                        outcome = element.find(".//{{{}}}Outcome".format(tr), namespaces)
                        step_result = self.parse_step_status(outcome, element, tr, namespaces)

                        measurement_value, comp_oper, string_limit = self.parse_string_step(element, tr, c, namespaces)
                        current_step = current_sequence.add_string_step(name=step_name, value=measurement_value, comp_op=comp_oper, limit=string_limit, group=step_group, status=step_result, tot_time=step_time)
            
            return uut_status

#########################################################################
#Helper methods for parsing elements


    def parse_numeric_step(self, element, tr, ts, c, namespaces):
        test_measurement = None
        low_limit = None
        high_limit = None
        comp_oper = None
        unit = None
        
        test_result_element = element.find("./{{{}}}TestResult".format(tr), namespaces)
        if test_result_element is not None:
            test_data_element = test_result_element.find("./{{{}}}TestData".format(tr), namespaces)
            test_limits_element = test_result_element.find("./{{{}}}TestLimits".format(tr), namespaces)
            if test_data_element is not None:
                test_measurement = test_data_element.find("./{{{}}}Datum".format(c), namespaces).attrib.get("value", None)
                unit = test_data_element.find("./{{{}}}Datum".format(c), namespaces).attrib.get("nonStandardUnit", " ")
            if test_limits_element is not None:
                limits_element = test_limits_element.find("./{{{}}}Limits".format(tr), namespaces)
                for limit in limits_element:
                    element_name = limit.tag.split("}")[-1]
                    if element_name == "SingleLimit":
                        comp_oper = limit.attrib.get("comparator", None)
                        comp_oper = CompOp[comp_oper]
                        low_limit = limit.find("./{{{}}}Datum".format(c), namespaces).attrib.get("value", None)
                    elif element_name == "LimitPair":
                        comp_oper = ""
                        limits = []
                        for element in limit:
                            comp_oper += element.attrib.get("comparator", None)
                            limits.append(element.find("./{{{}}}Datum".format(c), namespaces).attrib.get("value", None))
     
                        comp_oper = CompOp[comp_oper]
                        low_limit = limits[0]
                        high_limit = limits[1]
                    elif element_name == "Expected":
                        comp_oper = CompOp[limit.attrib.get("comparator", None)]
                        low_limit = limit.find("./{{{}}}Datum".format(c), namespaces).attrib.get("value", None)
                    
            elif test_result_element.find("./{{{}}}Extension".format(tr), namespaces) is not None:
                limit_properties_element = test_result_element.find("./{{{}}}Extension".format(tr), namespaces).find("./{{{}}}TSLimitProperties".format(ts), namespaces)
                if limit_properties_element is not None:
                    comp_type_log_value = limit_properties_element.find("./{{{}}}IsComparisonTypeLog".format(ts), namespaces).attrib.get("value", None)
                    if comp_type_log_value == "true":
                        comp_oper = CompOp.LOG
        return test_measurement, low_limit, high_limit, comp_oper, unit

    def parse_string_step(self, element, tr, c, namespaces):
        string_measurement = None
        comp_oper = None
        string_limit = None

        test_result_element = element.find("./{{{}}}TestResult".format(tr), namespaces)
        if test_result_element is not None:
            test_data_element = test_result_element.find("./{{{}}}TestData".format(tr), namespaces)
            test_limits_element = test_result_element.find("./{{{}}}TestLimits".format(tr), namespaces)
            if test_data_element is not None:
                test_measurement = test_data_element.find("./{{{}}}Datum".format(c), namespaces)
                if test_measurement is not None:
                    string_measurement = test_measurement.find("./{{{}}}Value".format(c), namespaces).text
            if test_limits_element is not None:
                limits_element = test_limits_element.find("./{{{}}}Limits".format(tr), namespaces)
                if limits_element is not None:
                    comp_oper = limits_element.find("./{{{}}}Expected".format(c), namespaces).attrib.get("comparator", None)
                    if comp_oper is not None:
                        if comp_oper == "CIEQ":
                            comp_oper = "IGNORECASE"
                        else:
                            comp_oper = CompOp[comp_oper]
                    string_limit = limits_element.find("./{{{}}}Expected".format(c), namespaces).find("./{{{}}}Datum".format(c), namespaces).find("./{{{}}}Value".format(c), namespaces).text
        return string_measurement, comp_oper, string_limit
    

    def parse_step_properties(self, element, tr, ts, namespaces):
        step_type = None
        step_group = None
        step_time = None
        
        # Find the Extension element under 'element'
        extension = element.find("./{{{}}}Extension".format(tr), namespaces)
        
        # Proceed only if Extension element exists
        if extension is not None:
            # Find the TSStepProperties element under 'extension'
            step_properties = extension.find("./{{{}}}TSStepProperties".format(ts), namespaces)
            
            # Proceed only if TSStepProperties exists
            if step_properties is not None:
                # Find and assign StepType if it exists
                step_type_element = step_properties.find("./{{{}}}StepType".format(ts), namespaces)
                if step_type_element is not None:
                    step_type = step_type_element.text
                
                # Find and assign StepGroup if it exists
                step_group_element = step_properties.find("./{{{}}}StepGroup".format(ts), namespaces)
                if step_group_element is not None:
                    step_group = self.parse_step_group(step_group_element.text)
                    
                # Find and assign TotalTime if it exists
                step_time_element = step_properties.find("./{{{}}}TotalTime".format(ts), namespaces)
                if step_time_element is not None:
                    step_time = step_time_element.attrib.get("value", None)
        
        return step_type, step_group, step_time
            

    def get_part_number(self, uut_definition, c, namespaces):
        # Use the namespace dictionary to find the element
        identification_element = uut_definition.find(".//{{{}}}Identification".format(c), namespaces)
        
        if identification_element is not None:
            # Find the IdentificationNumbers element inside Identification
            identification_numbers_element = identification_element.find(".//{{{}}}IdentificationNumbers".format(c), namespaces)
            
            if identification_numbers_element is not None:
                # Find the IdentificationNumber element inside IdentificationNumbers
                identification_number_element = identification_numbers_element.find(".//{{{}}}IdentificationNumber".format(c), namespaces)
                
                if identification_number_element is not None:
                    # Access the 'number' attribute of the IdentificationNumber element
                    part_number = identification_number_element.attrib.get('number', None)
                    if part_number:
                        return part_number
        
        # If no part number is found, return the default part number
        return self.parameters["partNumber"]
        
    def get_serial_number(self, uut_element, c, namespaces):
        # Find the SerialNumber element using the correct namespace
        serial_number_element = uut_element.find(".//{{{}}}SerialNumber".format(c), namespaces)
        
        if serial_number_element is not None:
            # Get the text of the SerialNumber element
            serial_number = serial_number_element.text
            
            # If no serial number is found or it's empty, use the default from parameters
            if serial_number is None or serial_number == "":
                serial_number = self.parameters["serialNumber"]
            
            return serial_number
        
        # If the SerialNumber element isn't found, return the default serial number
        return self.parameters["serialNumber"]
        
    def get_operator_name(self, test_results, tr, namespaces):
        # Find the Personnel element using the correct namespace
        personnel_element = test_results.find(".//{{{}}}Personnel".format(tr), namespaces)
        
        if personnel_element is not None:
            # Find the SystemOperator element inside Personnel
            system_operator_element = personnel_element.find(".//{{{}}}SystemOperator".format(tr), namespaces)
            
            if system_operator_element is not None:
                # Get the 'name' attribute of the SystemOperator element
                operator_name = system_operator_element.attrib.get('name', None)
                
                # If the 'name' attribute is empty or None, fall back to the default operator
                if operator_name is None or operator_name == "":
                    operator_name = self.parameters["operator"]
                
                return operator_name
        
        # If the Personnel or SystemOperator element isn't found, return the default operator
        return self.parameters["operator"]
    def get_station_name(self, test_results, tr, c, namespaces):
         # Find the SerialNumber element using the correct namespace
        serial_number_element = test_results.find(".//{{{}}}TestStation".format(tr), namespaces)
        
        if serial_number_element is not None:
            # Get the text of the SerialNumber element
            station_name = serial_number_element.find(".//{{{}}}SerialNumber".format(c), namespaces).text
            
            # If no serial number is found or it's empty, use the default from parameters
            if station_name is None or station_name == "":
                station_name = self.parameters["stationName"]
            
            return station_name
        
        # If the SerialNumber element isn't found, return the default serial number
        return self.parameters["serialNumber"]
            
    def get_sequence_name(self, test_results, tr, namespaces):
        # Find the ResultSet element using the correct namespace
        result_set_element = test_results.find(".//{{{}}}ResultSet".format(tr), namespaces)
        
        if result_set_element is not None:
            # Get the 'name' attribute of the ResultSet element
            sequence_name = result_set_element.attrib.get('name', None)
            
            # If the 'name' attribute is empty or None, fall back to the default sequence name
            if sequence_name is None or sequence_name == "":
                sequence_name = self.parameters["sequenceName"]
            
            return sequence_name
        
        # If the ResultSet element isn't found, return the default sequence name
        return self.parameters["sequenceName"]
    
    def get_date_time_values(self, test_results, tr, namespaces):
        # Find the ResultSet element using the correct namespace
        result_set_element = test_results.find(".//{{{}}}ResultSet".format(tr), namespaces)
        
        if result_set_element is not None:
            # Get the 'startDateTime' and 'endDateTime' attributes from the ResultSet element
            start_date_time = result_set_element.attrib.get('startDateTime', None)
            end_date_time = result_set_element.attrib.get('endDateTime', None)
            
            # Return the start and end date-time values if found
            return start_date_time, end_date_time
        
        # If the ResultSet element isn't found, return None
        return None, None
    
    def get_button_hit(self, element, tr, c, namespaces):
        button_hit = None
        if element.find(".//{{{}}}Data".format(tr), namespaces):
            if element.find(".//{{{}}}Data".format(tr), namespaces).find("./{{{}}}Collection".format(c), namespaces):
                datum_element = element.find(".//{{{}}}Data".format(tr), namespaces).find("./{{{}}}Collection".format(c), namespaces).find("./{{{}}}Item".format(c), namespaces)
                if datum_element is not None:
                    button_hit = element.find(".//{{{}}}Data".format(tr), namespaces).find("./{{{}}}Collection".format(c), namespaces).find("./{{{}}}Item".format(c), namespaces).find("./{{{}}}Datum".format(c), namespaces).attrib.get("value", None)
        return button_hit
    

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

    def parse_step_group(self, step_group):
        if step_group == "Setup":
            step_group = "S"
        elif step_group == "Cleanup":
            step_group = "C"
        else:
            step_group = "M"
        return step_group
    
    def parse_step_status(self, outcome, element, tr, namespaces):
        outcome = outcome.attrib.get("value", None)
        if outcome == "Passed":
            return "P"
        elif outcome == "Failed":
            return "F"
        elif outcome == "Error":
            return "E"
        elif outcome == "Skipped":
            return "S"
        elif outcome == "Done":
            return "D"
        elif outcome == "Terminated":
            return "T"
        elif outcome == "UserDefined":
            outcome = element.find(".//{{{}}}Outcome".format(tr), namespaces).attrib.get("qualifier", None)
            if outcome == "Skipped":
                return "S"
            
    def get_namespaces(self, root_element):
        namespace_name = root_element.tag.split('}')[0].strip('{')

        if namespace_name == "http://www.ieee.org/ATML/2007/TestResults":
            trc = None
            tr = namespace_name
            ts = "www.ni.com/TestStand/ATMLTestResults/1.0"
            xsi = "http://www.w3.org/2001/XMLSchema-instance"
            c = "http://www.ieee.org/ATML/2006/Common"
        elif namespace_name == "urn:IEEE-1636.1:2011:01:TestResultsCollection":
            trc = namespace_name
            tr = "urn:IEEE-1636.1:2011:01:TestResults"
            ts = "www.ni.com/TestStand/ATMLTestResults/2.0"
            xsi = "http://www.w3.org/2001/XMLSchema-instance"
            c = "urn:IEEE-1671:2010:Common"
        elif namespace_name == "urn:IEEE-1636.1:2013:TestResultsCollection":
            trc = namespace_name
            tr = "urn:IEEE-1636.1:2013:TestResults"
            ts = "www.ni.com/TestStand/ATMLTestResults/3.0"
            xsi = "http://www.w3.org/2001/XMLSchema-instance"
            c = "urn:IEEE-1671:2010:Common"
        else:
            raise NotImplementedError("Unsupported ATML Format. Supported formats: 2.02, 5.0, 6.01")

        return trc, tr, ts, xsi, c
