from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pywats_api.WATS import WATS
import logging
from report.uut.steps.comp_operator import CompOp
from report.uut.uut_info import UUTInfo
from report.uut.uut_report import UUTReport


def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Logging has been set up from the config file.")

    # 1. Create an instance of WATS
    url = "https://YOURSERVER.wats.com/"
    token = "YOURTOKEN"
    wats = WATS(url, token)

    tz = timezone.utc
    tz = ZoneInfo(key='Europe/Paris')

    start_date = datetime(2025,3,12,8,0,0,0,tzinfo=tz)


    for d in range(1):
        dt = start_date
        for i in range(60*8):
            sn = str(d+i)
            dt+= timedelta(seconds=60)
            uut = create_report(sn, dt, 50)
            # 6. Submit the report to WATS    
            wats.submit_report(uut)
            print(i)
                        
        start_date = start_date + timedelta(days=1)

    # 6. Submit the report to WATS    
    #wats.submit_report(uut)




def create_report(sn: str, start_date: datetime, exec_time: float ):
        # 2. Create a UUTReport object
    uut = UUTReport(pn="OEE_TEST_6",sn=sn,rev="1.0", result="P",station_name="OEE_STATION_6",process_code=10, location="Drammen",purpose="APITest",
                    info=UUTInfo(operator="Operator",batch_number="B1", fixture_id="Fixture"))
    
    
    
    uut.root.sequence.path = "RootSequencePath"
    uut.root.sequence.file_name = "RootSequenceName"
    uut.root.sequence.version = "1.0"

    # 3. Add additional data to the UUTReport object
    uut.add_misc_info("Key", "Value")
    uut.add_sub_unit(part_type="PCB", sn="1234", pn="ABC123", rev="1.0")
    uut.add_asset(sn="73957657222", usage_count=10)

    uut.start = start_date
    uut.info.exec_time = exec_time

    # 4. Get the root sequence call 
    root = uut.get_root_sequence_call()
    
    # 5. Add steps to the root sequence call
    root.add_numeric_step(name="MyNumericStep",value=3.14, unit="V", comp_op=CompOp.LT, low_limit=4.0)
    root.add_string_step(name="NyStringStep", value="VALUE", unit="U", comp_op=CompOp.CASESENSIT, limit="VALUE", status="P")
    root.add_boolean_step(name="MyBooleanStep", status="P")

    mns = root.add_multi_numeric_step(name="MultiNumericStep", status="F")
    mns.add_measurement(name="Mesurement 1", value=3.14, unit="V", comp_op=CompOp.GELE, low_limit=0,high_limit=10, status="P")
    mns.add_measurement(name="Mesurement 2", value=6.28, unit="V", comp_op=CompOp.GELE, low_limit=0,high_limit=3, status="F")

    return uut


# Entry point check
if __name__ == '__main__':
    main()


