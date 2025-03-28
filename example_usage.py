import os
import re
import argparse
import shutil
from typing import Generator
from pywats_api.WATS import WATS
from converters.teststand_xml_converter import TestStandXMLConverter

class FileSearcher:
    def __init__(self, path: str, pattern: str):
        self.path = path
        self.pattern = re.compile(pattern)
    
    def find_matching_files(self) -> Generator[str, None, None]:
        """
        Generator som itererer gjennom alle filer i path og returnerer de som matcher pattern.
        """
        if not os.path.isdir(self.path):
            raise ValueError(f"{self.path} er ikke en gyldig katalog")
        
        for filename in os.listdir(self.path):
            if self.pattern.match(filename):
                yield os.path.join(self.path, filename)

def main():
    
     # Check if running in debug mode
    if os.getenv("DEBUG_MODE"):
        # Set default values for debugging
        path = "C:\\TestStandXML"
        pattern = ".*\\.xml$"
        ppa = "Move"
    else:
        parser = argparse.ArgumentParser(description="Search for files based on regex and convert them")
        parser.add_argument("path", type=str, help="Path to the directory where the files should be searched")
        parser.add_argument("pattern", type=str, help="Regex-pattern to filtrate files")
        parser.add_argument("ppa", type=str, help="post process action after submitting report")
        args = parser.parse_args()
        path = args.path
        pattern = args.pattern
        ppa = args.ppa
        
    searcher = FileSearcher(path, pattern)
    converter = TestStandXMLConverter()
    
    # Create an instance of WATS
    url = "https://debug.wats.com/"
    token = "am9uX3B5dGhvbl9hcGk6XmRxMHpKNUFubWU3MHRrNXRhNmhNSmhIY256bThk"
    wats = WATS(url, token)
    
    for file in searcher.find_matching_files():

        with open(file, "rb") as file_stream:  # Open file as a stream
            uut = converter.convert_report(file_stream)  # Pass stream instead of file path
        
        # Send report to WATS
        wats.submit_report(uut)
        
        #PPA 
        if ppa == "Move":
            done_folder = os.path.join(path, "Done")
            if os.path.exists(done_folder):
                shutil.move(file, done_folder)
            else:
                #done_folder = os.path.join(path, "Done")
                os.makedirs(done_folder)
                shutil.move(file, done_folder)
        elif ppa == "Delete":
            os.remove(file)

if __name__ == "__main__":
    main()
   