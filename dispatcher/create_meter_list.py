
from class_t import testclass
from mqtt_mess import set_json 
import json

msg = "27442d2c5768663230028d208e11de0320188851bdc4b72dd3c2954a341be369e9089b4eb3858169494e"
meter_list = {}     # Creating a dict
meter = [None]*20   # Meter array


def lit_end(no: str) -> str:
    """
    Converting string from big to little endian bytewise
    """
    little = ""
    for i in range(0, len(no), 2):
        little+= no[len(no)-2 - i]
        little+= no[len(no)-1 - i]

    return little


def create_meter_list():

    # Create test object to search in
    full_obj = json.loads(set_json())
    
    # Clear the dictionary
    meter_list.clear()

    for i in range (0, len(full_obj)):                
        # Set serial no. and convert to little-endian
        meter_id = lit_end(full_obj[i]['deviceId'])                     
        
        # Adding to dictionary
        meter_list[meter_id] = {
            "id" : i,
            "manufacturerKey": full_obj[i]['manufacturerKey'],
            "EncryptionKey": full_obj[i]['encryptionKey'], 
            "ManufacturerDeviceKey": full_obj[i]['manufacturerDeviceKey']} 
            
        # Instantiating a class for every meter in dictionary
        meter[i] = testclass(meter_id)                                   
  

def dispatcher(message: str):

    for i in meter_list:
        print(meter_list[i])

    deviceId = str(message[8:16])
    if deviceId in meter_list.keys():
        print("This meter received the message: ")
        meter[meter_list[deviceId]['id']].printout()



if __name__ == "__main__":
    create_meter_list()
    dispatcher(msg)