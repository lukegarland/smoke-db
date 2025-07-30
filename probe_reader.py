import bleak
import asyncio
import binascii
import time
import os



COMMAND_UUID="1086fff1-3343-4817-8bb2-b32206336ce8"
NOTIFY_UUID="1086fff2-3343-4817-8bb2-b32206336ce8"




def callback(sender, data: bytearray):
    print(f"""
PROBE 1: {int(binascii.hexlify(data[5:7]).decode())/10}
PROBE 2: {int(binascii.hexlify(data[7:9]).decode())/10}
PROBE 3: {int(binascii.hexlify(data[9:11]).decode())/10}
PROBE 4: {int(binascii.hexlify(data[11:13]).decode())/10}
""")

async def main():
    addr = "109ACFDA-16E3-E907-F362-6B8CC48DFAE9"
    
    client = bleak.BleakClient(address_or_ble_device=addr)

    await client.connect()
    data = await client.write_gatt_char(COMMAND_UUID, bytearray([1,9,62,143,138,108,53,238,38,227,248,241]), response=True)
#    print(data)
    await client.start_notify(NOTIFY_UUID, callback)

    while True:
        time.sleep(1)


asyncio.run(main())