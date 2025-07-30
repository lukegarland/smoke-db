import bleak
import asyncio
import binascii
import time
import os



COMMAND_UUID="1086fff1-3343-4817-8bb2-b32206336ce8"
NOTIFY_UUID="1086fff2-3343-4817-8bb2-b32206336ce8"



def temperature_notify_callback(sender, data: bytearray):
    
    print(f"""
PROBE 1: {int(binascii.hexlify(data[5:7]).decode())/10}
PROBE 2: {int(binascii.hexlify(data[7:9]).decode())/10}
PROBE 3: {int(binascii.hexlify(data[9:11]).decode())/10}
PROBE 4: {int(binascii.hexlify(data[11:13]).decode())/10}
""")

async def find_device(name="TP25"):
    devices = await bleak.BleakScanner.discover(timeout=5)
    for device in devices:
        print(f"found device {device.name}")
        if device.name == name:
            return device
    print(f"Error. Did not find device with name: {name}")
    return None


async def main():
    device = await find_device()
    if device: 
        client = bleak.BleakClient(address_or_ble_device=device)
        
        # connect and send command sequence to start streaming / notfiying temperature data
        await client.connect()
        await client.write_gatt_char(COMMAND_UUID, bytearray([1,9,62,143,138,108,53,238,38,227,248,241]), response=True)
        
        # start temperature notifiactions via callback
        await client.start_notify(NOTIFY_UUID, temperature_notify_callback)

        while True:
            await asyncio.sleep(1)


asyncio.run(main())