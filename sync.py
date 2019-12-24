from door import Door, search_device

if __name__ == '__main__':
    devices = search_device()
    for device in devices:
        device_sn = device['sn']
        device_ip = str(device['ip'])
        door = Door(host=device_ip, sn=device_sn)
        door.sync()
