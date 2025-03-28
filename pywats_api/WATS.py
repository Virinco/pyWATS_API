import requests
import json as json_module
from typing import Any, Union
from report.report import Report
from report.uut.uut_report import UUTReport
from report.uur.uur_report import UURReport
from urllib.parse import urlparse, urljoin

import logging
logger = logging.getLogger(__name__)


class ReportHeader:
    uuid: str | None = None

class WATS(): 
    
    def __init__(self, url=None, token=None):
        # Log the init parameters at debug level for diagnostic purposes
        logger.debug("Initializing WATS with url=%s, token=%s", url, token)
        self.url = url
        self.token = token

        # Validate required parameters; log and raise exception if missing
        if not self.url or not self.token:
            error_msg = "API URL and Token must be provided as parameters at initialization"
            logger.error(error_msg)
            raise ValueError(error_msg)
  
        # Ensure the URL has a scheme (default to HTTPS if missing)
        parsed_url = urlparse(url)
        if not parsed_url.scheme:
            logger.debug("No scheme detected in the URL. Prepending 'https://'")
            url = "https://" + url

        # Remove trailing slashes for consistency
        self.url = url.rstrip('/')
        self.token = token

        ## TODO: Sjekke at API er connected ved api kall og logg connection sucessfull

        self.sync_local_processes_with_server()

        # Log success after setting URL/token
        logger.info("WATS instance created with URL: %s", self.url)

    def submit_report(self, report: Union[str, 'Report']):
        logger.debug("submit_report_from_object called")
        
        headers = {
            'Authorization': f'Basic {self.token}',
            'Content-Type': 'application/json'
        }

        if isinstance(report, str):
            json_string = self.get_validated_json_string(report)
        else:
            json_string = self.report_object_to_json_string(report)

        endpoint = self._get_full_endpoint("api/Report/WSJF")
        logger.debug(f"Endpoint URL: {endpoint}")

        try:
            response = requests.post(endpoint, data=json_string, headers=headers)
            logger.debug(f"Received response with status code: {response.status_code}")
            response.raise_for_status()
            logger.info(f"Report with uuid {report.id} was sent successfully.")
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred during report submission: {http_err} - Response text: {response.text}")
            raise 
        except Exception as err:
            logger.error(f"Error occurred during report submission: {err}")
            raise
        # Should we return a status or true/false?


    def load_report_from_server(self, guid, context: Any=None) -> Union[UUTReport,UURReport]:  
        logger.debug(f"load_report called with id: {guid}")

        headers = {
            'Authorization': f'Basic {self.token}',
            'Content-Type': 'application/json'
        }

        params = {'id': guid}
 
        endpoint = self._get_full_endpoint(f"api/Report/WSJF/{guid}")
        logger.debug(f"Endpoint URL: {endpoint}")

        try:
            response = requests.get(endpoint, params=params, headers=headers)
            logger.debug(f"Received response with status code: {response.status_code}")
            
            response.raise_for_status()
            
            json_data = response.json()
            logger.debug(f"Response JSON: {json_data}")

            # Convert the dictionary to a JSON string
            json_string = json_module.dumps(json_data)
            
            # Validate and parse the JSON string into a UUTReport object
            report = self.json_string_to_report_object(json_string, context)
            
            logger.info(f"Report with GUID {guid} was loaded successfully.")
            return report
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred during report loading: {http_err} - Response text: {response.text}")
            raise 
        except Exception as err:
            logger.error(f"Error occurred during report loading: {err}")
            raise

    def sync_local_processes_with_server(self):
        logger.debug("sync_local_processes_with_server called.")

        headers = {
            'Authorization': f'Basic {self.token}',
            'Content-Type': 'application/json'
        }

        endpoint = self._get_full_endpoint("api/internal/Process/GetProcesses")
        logger.debug("Endpoint URL: %s", endpoint)

        try:
            response = requests.get(endpoint, headers=headers)
            logger.debug(f"Received response with status code: {response.status_code}")
            
            response.raise_for_status()
            
            processes = response.json()
            logger.debug(f"Synchronized processes: {processes}")
            
            self.processes = processes
            return self.processes

        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred during process synchronization: {http_err} - Response text: {response.text}")
            raise
        except Exception as err:
            logger.error(f"Error occurred during process synchronization: {err}")
            raise

    def get_local_processes(self):
        logger.debug("get_local_processes called.")
        return self.processes

    def _get_full_endpoint(self, endpoint: str) -> str:
        """ Ensures consistent API endpoint joining """
        return urljoin(self.url + '/', endpoint) 
    
    def report_object_to_json_string(self, report: Report):
        return report.model_dump_json(by_alias=True, exclude_none=True)

    def json_string_to_report_object(self, json : str, context:Any=None):
        #return UUTReport.model_validate_json(json, context={"is_deserialization": True})
        return UUTReport.model_validate_json(json, context=context) 
    
    def get_validated_json_string(self, json : str, context:Any=None):
        return UUTReport.model_validate_json(json, context=context)








