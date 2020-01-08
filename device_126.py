import asyncio

from door import create_door


async def run():
    sn = '4d432d35383234543239303737393834'
    host = '192.168.10.126'
    config = {'host': host, 'sn': sn}
    door = await create_door(config)

    await door.get_monitor_status()
    task1 = asyncio.create_task(door.sync())
    task2 = asyncio.create_task(door.monitor())
    await task1
    await task2

if __name__ == '__main__':
    while True:
        print('start monitoring...')
        try:
            asyncio.run(run())
        except Exception as e:
            print(e)
            print('restart monitoring...')
