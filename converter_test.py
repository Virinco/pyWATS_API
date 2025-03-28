from pywats_api.WATS import WATS
from converters.teststand_xml_converter import TestStandXMLConverter


def main():

     # 1. Create an instance of WATS
    url = "https://YOURSERVER.wats.com/"
    token = "YOURTOKEN"
    wats = WATS(url, token)

    # Define filepath
    # file_path = "converters/test_reports/Lion-DCC-PCBA-v3.0_[244114B12383][7-58-30-AM][11-25-2024].xml"
    file_path = "C:/Users/ThomasMartinsen/Documents/TestStandXMLFiles/TS2023 - FATv1_Report[1 40 30 PM][2 25 2025] - Copy.xml"
    #file_path = "C:/Users/ThomasMartinsen/Documents/TestStandXMLFiles/Lion_AUX_Power_Supply_[243015002556][10-49-46-AM][9-28-2024].xml"
    #file_path = "C:/Users/ThomasMartinsen/Documents/TestStandXMLFiles/TestStand_Lion-PM-1.5-Hipot2_[245315600975][3-11-52-PM][12-30-2024].xml"
    #file_path = "C:/Users/ThomasMartinsen/Documents/TestStandXMLFiles/Michael_Robak_CPx50_CPU_RF_[230941B09248][00-19-19][9-3-2023].xml"
    
    converter = TestStandXMLConverter()
    # with open(file_path, 'r') as file:
    uut = converter.convert_report(file_path)

    #print(uut)

    #Submit report
    wats.submit_report(uut)

# Entry point check
if __name__ == '__main__':
    main()
