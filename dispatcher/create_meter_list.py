
from class_t import testclass
from mqtt_mess import set_json 
import json
from select import select
from meter.OmniPower import OmniPower, C1Telegram
from utils.log import get_logger

meter_list = {}     # Creating a dict

def create_meter_list():
    """
    Clear the list of meters to read from.
    Creating a new list and an array of OmniPower classes.
    Meter list Id = OmniPower array position.
    """
    # Create test object to search in
    full_obj = json.loads(set_json())
    
    # Clear the dictionary
    meter_list.clear()

    for i in range (0, len(full_obj)):                
        # Set serial no. and convert to little-endian
        meter_id = full_obj[i]['deviceId']                     
        
        # Adding to dictionary
        meter_list.update({meter_id: OmniPower(name="OP-"+meter_id, meter_id=meter_id, aes_key=full_obj[i]['encryptionKey'])})                         
  

def dispatcher() -> bool: 

    # Get logger instance
    log = get_logger()
    
    try:
        fifo = open('../driver/IM871A_pipe', 'r')
    except OSError as err:
        log.exception(err)    
    
    select([fifo], [], [])                      # polls and wait for data ready for read on fifo
    msg = fifo.readline().strip()
    fifo.close()
    
    telegram = C1Telegram(msg)
    address = telegram.big_endian['A'].decode() # Gets address as UTF-8 string
    
    if address in meter_list.keys():
        meter_list[address].process_telegram(msg)



if __name__ == "__main__":
    create_meter_list()
    dispatcher()