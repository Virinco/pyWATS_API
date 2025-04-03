from pywats_api.WATS import WATS
from converters.teststand_xml_converter import TestStandXMLConverter


def main():

     # 1. Create an instance of WATS
    url = "https://YOURSERVER.wats.com/"
    token = "YOURTOKEN"
    wats = WATS(url, token)

    # Define filepath
    file_path = "C:/Users/ThomasMartinsen/Documents/TestStandXMLFiles/TS2023 - FATv1_Report[1 40 30 PM][2 25 2025] - Copy.xml"
     
    converter = TestStandXMLConverter()
    # with open(file_path, 'r') as file:
    uut = converter.convert_report(file_path)

    #print(uut)

    #Submit report
    wats.submit_report(uut)

# Entry point check
if __name__ == '__main__':
    main()
