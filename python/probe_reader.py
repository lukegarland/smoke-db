import bleak
import bleak.backends.device
import bleak.exc

import asyncio
import binascii
import datetime

import prometheus

# globals...
COMMAND_UUID="1086fff1-3343-4817-8bb2-b32206336ce8"
NOTIFY_UUID="1086fff2-3343-4817-8bb2-b32206336ce8"
STARTUP_COMMAND = bytearray([1,9,62,143,138,108,53,238,38,227,248,241])
prometheus_exporter = prometheus.PrometheusExporter()


def decode_bcd(bcd_bytearray:bytearray) -> int | None:
    hex_str = binascii.hexlify(bcd_bytearray).decode()
    try: 
        # value "xxxx" is actually xxx.x
        parse_hex_to_int = int(hex_str)
        return parse_hex_to_int/10
    except ValueError:
        return None


def temperature_notify_callback(sender, data: bytearray):
    probe_dict = {
        1: decode_bcd(data[5:7]),
        2: decode_bcd(data[7:9]),
        3: decode_bcd(data[9:11]),
        4: decode_bcd(data[11:13])
    }
    print(datetime.datetime.now().replace(microsecond=0).isoformat(sep=" "))
    print(f"""PROBE 1: {probe_dict.get(1)}
PROBE 2: {probe_dict.get(2)}
PROBE 3: {probe_dict.get(3)}
PROBE 4: {probe_dict.get(4)}
""")
    for probe_num, value in probe_dict.items():
        prometheus_exporter.report_probe_temp(value, probe_num)

async def find_device(name="TP25", timeout=5):
    devices = await bleak.BleakScanner.discover(timeout=timeout)
    for device in devices:
        if device.name == name:
            return device
    print(f"Error, Did not find device with name: {name}")
    return None

async def connect_device(device: bleak.backends.device.BLEDevice) -> bleak.BleakClient:
    client = bleak.BleakClient(address_or_ble_device=device)
    
    # connect and send command sequence to start streaming / notfiying temperature data
    await client.connect()
    await client.write_gatt_char(COMMAND_UUID, STARTUP_COMMAND, response=True)
    
    # start temperature notifiactions via callback
    await client.start_notify(NOTIFY_UUID, temperature_notify_callback)
    
    return client

async def main():
    predictor = prometheus.TemperatureTimePredictor(prometheus_exporter)
    device = await find_device(timeout=5)
    if device:
        client = await connect_device(device) 
        
        while True:
            try:
                await asyncio.sleep(5)
                predictor.run_realtime_prediction()
                if not client.is_connected:
                    device = await find_device(timeout=15)
                    if device:
                        client = await connect_device(device)
                    if client.is_connected:
                        print("successfully reconnected to device")
                    else:
                        print("Error, unable to connect to device")
                        prometheus_exporter.probe_disconnected()
            except bleak.exc.BleakError as e:
                print(e.with_traceback())
                continue
                
if __name__ == "__main__":
    asyncio.run(main())