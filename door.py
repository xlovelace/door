import asyncio
import binascii
import ipaddress
import socket
import textwrap
import time
from collections import namedtuple

from api import TaidiiApi
from card import Card
from db import db
import settings
from utils import hex_to_ascii, ip_to_hex, str_to_hex, dec2hex, get_bcd_password, str2datetime

Command = namedtuple('Command', ['control_code', 'data_length'])


class Door(object):
    FLAG = '7E'
    COMMANDS = {
        '设置通讯密码': {},
        '读取TCP参数': Command('010600', '00000000'),
        '设置TCP参数': Command('010601', '00000089'),
        '获取设备版本号': Command('010800', '00000000'),
        '获取设备运行信息': Command('010900', '00000000'),

        '读取所有授权卡': Command('070300', '00000001'),
        '读取授权卡信息': Command('070100', '00000000'),
    }
    OK_CODE = '210100'

    reader = writer = None
    cards_data = []

    def __init__(self, host='192.168.3.35', port=8000, password='FFFFFFFF', sn=None):
        self.host = host
        self.port = port
        self.password = password
        self.sn = sn or self.get_sn()

    async def open_connection(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

    async def send(self, data):
        received_data = ''
        self.writer.write(data)
        await self.writer.drain()

        n = 1024
        while True:
            packet = await self.reader.read(n)
            packet = binascii.hexlify(packet).decode()
            received_data += packet
            # todo: 某些命令返回数据较大,会分多个包,会有多个7e...7e这样的格式,需要处理
            if packet[-2:].lower() == '7e':
                break
        return received_data

    async def send_command(self, command, data=''):
        info_code = '19883d90'  # 信息码,可以是随机数
        data = self.compose_data(info_code, command.control_code, command.data_length, data)
        res = await self.send(data)
        res = self.parse_res(res)
        return res

    def get_sn(self):
        self.sn = '30303030303030303030303030303030'  # 获取sn时不重要
        info_code = '19883D90'
        control_code = '010200'
        data_length = '00000000'
        data = self.compose_data(info_code, control_code, data_length)
        res = self.send(data)
        res = self.parse_res(res)
        # print(res)
        return res['data']

    def compose_data(self, info_code, control_code, data_length, data_content=''):
        data = self.sn + self.password + info_code + control_code + data_length + data_content
        checksum = self.check_sum(data)
        data = self.FLAG + data + checksum + self.FLAG
        data = self.data_switch(data)
        return data

    def parse_res(self, res):
        info_code = res[2: 10]
        sn = res[10: 42]
        password = res[42: 50]
        # control_code有3部分组成,分类,命令,参数,每部分占用1字节
        category = res[50: 52]
        command = res[52: 54]
        parama = res[54: 56]
        data_length = res[56: 64]
        data = res[64: -4]
        res_checksum = res[-4: -2]  # 用作校验
        return {
            'info_code': info_code,
            'sn': sn,
            'password': password,
            'category': category,
            'command': command,
            'parama': parama,
            'data_length': data_length,
            'data': data
        }

    def parse_ip(self, ip_data):
        return {
            'mac': ip_data[: 12],
            'ip': ipaddress.IPv4Address(int(ip_data[12: 20], 16)),
            'mask': ipaddress.IPv4Address(int(ip_data[20: 28], 16)),
            'gateway': ipaddress.IPv4Address(int(ip_data[28: 36], 16)),
            'dns1': ipaddress.IPv4Address(int(ip_data[36: 44], 16)),
            'dns2': ipaddress.IPv4Address(int(ip_data[44: 52], 16)),
            'work_type': ip_data[52: 54],
            'tcp_listen': int(ip_data[54: 58], 16),
            'udp_listen': int(ip_data[58: 62], 16),
            'remote_port': int(ip_data[62: 66], 16),
            'remote_ip': ipaddress.IPv4Address(int(ip_data[66: 74], 16)),
            'dhcp': ip_data[74: 76],
            'remote_domain': hex_to_ascii(ip_data[76:])
        }

    def parse_card(self, card_data):
        status_dict = {
            0: '正常状态',
            1: '挂失',
            2: '黑名单'
        }
        password = get_bcd_password(card_data[10: 18])
        expire_time = str2datetime(card_data[18: 28]).strftime('%Y-%m-%d %H:%M:%S')
        last_read = str2datetime(card_data[54:], format='%y%m%d%H%M%S')
        if last_read is not None:
            last_read = last_read.strftime('%Y-%m-%d %H:%M:%S')
        status_key = int(card_data[42: 44], 16)
        return {
            'card_no': int(card_data[:10], 16),
            'password': password,
            'expire_time': expire_time,
            'date_range_code': card_data[28: 36],
            'expire_count': int(card_data[36: 40], 16),
            'permission': card_data[40: 41],
            'privilege': card_data[41: 42],
            'status': status_dict.get(status_key),
            'vocation_code': card_data[44: 52],
            'in_out_flag': card_data[52: 54],
            'last_read': last_read
        }

    def parse_card_record(self, record_data):
        reader_dict = {
            '01': '1门',
            '02': '1门',
            '03': '2门',
            '04': '2门',
            '05': '3门',
            '06': '3门',
            '07': '4门',
            '08': '4门',
        }

        status_dict = {
            1: '合法开门',
            2: '密码开门------------卡号为密码',
            3: '卡加密码',
            4: '手动输入卡加密码',
            5: '首卡开门',
            6: '门常开   ---  常开工作方式中，刷卡进入常开状态',
            7: '多卡开门  --  多卡验证组合完毕后触发',
            8: '重复读卡',
            9: '有效期过期',
            10: '开门时段过期',
            11: '节假日无效',
            12: '非法卡',
            13: '巡更卡  --  不开门',
            14: '探测锁定',
            15: '无有效次数',
            16: '防潜回',
            17: '密码错误------------卡号为错误密码',
            18: '密码加卡模式密码错误----卡号为卡号。',
            19: '锁定时(读卡)或(读卡加密码)开门',
            20: '锁定时(密码开门)',
            21: '首卡未开门',
            22: '挂失卡',
            23: '黑名单卡',
            24: '门内上限已满，禁止入门。',
            25: '开启防盗布防状态(设置卡)',
            26: '撤销防盗布防状态(设置卡)',
            27: '开启防盗布防状态(密码)',
            28: '撤销防盗布防状态(密码)',
            29: '互锁时(读卡)或(读卡加密码)开门',
            30: '互锁时(密码开门)',
            31: '全卡开门',
            32: '多卡开门--等待下张卡',
            33: '多卡开门--组合错误',
            34: '非首卡时段刷卡无效',
            35: '非首卡时段密码无效',
            36: '禁止刷卡开门  --  【开门认证方式】验证模式中禁用了刷卡开门时',
            37: '禁止密码开门  --  【开门认证方式】验证模式中禁用了密码开门时',
            38: '门内已刷卡，等待门外刷卡。（门内外刷卡验证）',
            39: '门外已刷卡，等待门内刷卡。（门内外刷卡验证）',
            40: '请刷管理卡(在开启管理卡功能后提示)(电梯板)',
            41: '请刷普通卡(在开启管理卡功能后提示)(电梯板)',
            42: '首卡未读卡时禁止密码开门。',
            43: '控制器已过期_刷卡',
            44: '控制器已过期_密码',
            45: '合法卡开门—有效期即将过期',
        }

        return {
            'card_no': str(int(record_data[: 10], 16)),
            'record_time': str2datetime(record_data[10: 22], format='%y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M:%S'),
            'reader_no': reader_dict[record_data[22: 24]],
            'reader_key': record_data[22: 24],
            'status_desc': status_dict[int(record_data[24:], 16)],
            'status': int(record_data[24:], 16)
        }

    def validate_data(self, res):
        return self.check_sum(res[2: 64]) == res[-4: -2]

    def data_switch(self, data):
        return binascii.unhexlify(data)

    def check_sum(self, data):
        return hex(sum(self.data_list(data)))[-2:]

    def data_list(self, data):
        res = []
        while data:
            s = data[0: 2]
            int_s = int(s, 16)
            res.append(int_s)
            data = data[2:]
        return res

    # 设备参数命令
    def get_tcp_info(self):
        '''
        读取TCP参数
        '''
        command = Command('010600', '00000000')
        res = self.send_command(command)
        ip_info = self.parse_ip(res['data'])
        return ip_info

    def set_tcp_info(self, info):
        '''
        设置TCP参数
        '''
        command = Command('010601', '00000089')
        read_command = Command('010600', '00000000')
        old_info = self.send_command(read_command)['data']
        mac = old_info[: 12]
        ip = ip_to_hex(info['ip'])
        mask = ip_to_hex(info['mask'])
        gateway = ip_to_hex(info['gateway'])
        dns1 = ip_to_hex(info['dns1'])
        dns2 = ip_to_hex(info['dns2'])
        work_type = info['work_type']
        tcp_listen = hex(info['tcp_listen'])[2:]
        udp_listen = hex(info['udp_listen'])[2:]
        remote_port = hex(info['remote_port'])[2:]
        remote_ip = ip_to_hex(info['remote_ip'])
        dhcp = info['dhcp']
        remote_domain = str_to_hex(info['remote_domain'])
        data = mac + ip + mask + gateway + dns1 + dns2 + work_type + tcp_listen + udp_listen + remote_port + remote_ip + dhcp + remote_domain
        data = data.ljust(274, '0')
        res = self.send_command(command, data=data)
        return res

    def set_password(self):
        command_key = '设置通讯密码'
        pass

    def get_version(self):
        '''
        获取设备版本号
        '''
        command = Command('010800', '00000000')
        res = self.send_command(command)
        return res

    def get_run_info(self):
        '''
        获取设备运行信息
        '''
        command = Command('010900', '00000000')
        res = self.send_command(command)
        return res

    def get_all_cards(self):
        '''
        读取所有授权卡
        '''
        command = Command('070300', '00000001')
        res = self.send_command(command, data='03')
        card_data = res['data']
        card_count = int(card_data[: 8], 16)
        card_data_list = textwrap.fill(card_data[8:], width=66).split()
        cards = []
        for card in card_data_list:
            cards.append(self.parse_card(card))

        return {'count': card_count, 'cards': cards}

    def get_card_info(self):
        '''
        读取授权卡信息
        '''
        command = Command('070100', '00000000')
        res = self.send_command(command)
        return res

    async def add_cards_to_unsorted_area(self, card_list):
        '''
        添加授权卡至非排序区域
        '''
        info_code = '10000001'
        data_length = int('04', 16) + int('21', 16) * len(card_list)
        data_length = dec2hex(data_length).zfill(8)
        command = Command('070400', data_length)
        data = dec2hex(len(card_list)).zfill(8)
        for card in card_list:
            # print(card.data)
            data += card.data

        send_data = self.compose_data(info_code, command.control_code, command.data_length, data)
        await self.send_data(send_data)

    def clear_cards(self, area_code='03'):
        '''
        清空所有授权卡
        区域代码：
            值	解释
            1	排序卡区域
            2	非排序卡区域
            3	所有区域
        '''
        command = Command('070200', '00000001')
        res = self.send_command(command, data=area_code)
        return res

    def get_one_card(self, card_no):
        '''
        读取单个授权卡
        '''
        command = Command('070301', '00000005')
        data = dec2hex(int(card_no)).zfill(10)
        res = self.send_command(command, data)
        return res

    async def delete_cards(self, card_no_list):
        '''
        删除授权卡
        '''
        # print("delete cards: {}".format(card_no_list))
        info_code = '10000005'
        data_length = dec2hex(int('04', 16) + int('5', 16) * len(card_no_list)).zfill(8)
        command = Command('070500', data_length)
        data = dec2hex(len(card_no_list)).zfill(8)
        for card_no in card_no_list:
            data += dec2hex(card_no).zfill(8)

        send_data = self.compose_data(info_code, command.control_code, command.data_length, data)
        await self.send_data(send_data)

    # 记录相关接口
    def get_record_point_info(self):
        '''
        读取记录指针信息
        '''
        command = Command('080100', '00000000')
        res = self.send_command(command)
        return res

    # 实时监控相关命令
    async def get_monitor_status(self):
        '''
        读取实时监控状态
        '''
        info_code = '10000002'
        command = Command('010b02', '00000000')
        send_data = self.compose_data(info_code, command.control_code, command.data_length, '')
        await self.send_data(send_data)

    async def enable_monitor(self):
        '''
        开启监控
        '''
        info_code = '10000003'
        command = Command('010b00', '00000000')
        send_data = self.compose_data(info_code, command.control_code, command.data_length, '')
        await self.send_data(send_data)

    async def disable_monitor(self):
        '''
        关闭监控
        '''
        command = Command('010b01', '00000000')
        res = await self.send_command(command)
        return res

    # 读取数据
    async def monitor(self):
        print('start monitoring...')
        count = 1
        while True:
            package = await self.reader.read(1024)
            res = binascii.hexlify(package).decode()
            res = self.parse_res(res)
            print('第{}次收到数据： {}'.format(count, res))
            info_code = res['info_code']
            if info_code == 'ffffffff':
                self.handle_record(res)
            elif info_code == '10000002':
                await self.handle_monitor(res)
            elif info_code == '10000001':
                self.handle_card(res)
            else:
                pass
            count += 1

    def handle_record(self, res):
        record_data = self.parse_card_record(res['data'])
        res.update(record_data)
        should_upload = self.should_upload_record(res)
        if should_upload:
            taidii_client = TaidiiApi(settings.TAIDII_USERNAME, settings.TAIDII_PASSWORD)
            is_success = taidii_client.upload_record(res)
            res['is_upload'] = is_success
            db.save_record(res)
        # print(res)

    async def handle_monitor(self, res):
        monitor_status = res['data']
        if monitor_status != '01':  # 未开启
            await self.enable_monitor()

    def handle_card(self, res):
        # 添加成功返回ok代码,失败返回失败卡号(查看文档)
        control_code = res['category'] + res['command'] + res['parama']
        if control_code == self.OK_CODE:
            is_success = True
            for update_card_data in self.cards_data:
                update_card_data['is_upload'] = is_success
                db.save_card(update_card_data)
        else:
            failed_card_data = res['data']
            failed_card_count = int(failed_card_data[: 8], 16)
            failed_card_data_list = textwrap.fill(failed_card_data[8:], width=66).split()
            failed_cards = []
            for card in failed_card_data_list:
                failed_cards.append(self.parse_card(card))
            failed_cards_no = [card['card_no'] for card in failed_cards]
            for update_card_data in self.cards_data:
                if Card.validate_card_no(update_card_data['card_no']):
                    if update_card_data['card_no'] in failed_cards_no:
                        update_card_data['is_upload'] = False
                    else:
                        update_card_data['is_upload'] = True
                    db.save_card(update_card_data)

    async def send_data(self, data):
        self.writer.write(data)
        await self.writer.drain()

    # 同步卡
    async def sync_card(self):
        # print('start sync cards....')
        taidii_client = TaidiiApi(settings.TAIDII_USERNAME, settings.TAIDII_PASSWORD)
        cards_data = taidii_client.get_all_cards_from_taidii()
        if cards_data is None:
            return
        self.cards_data = cards_data
        # print("cards_data: {}".format(cards_data))

        cards_data_local = db.get_all_cards()
        upload_card_list = []
        for card_data in cards_data:
            if self.should_upload_card(card_data, cards_data_local):
                card = Card(card_no=card_data['card_no'])
                if card not in upload_card_list:
                    upload_card_list.append(card)

        delete_card_no_list = self.get_delete_cards(cards_data, cards_data_local)

        await asyncio.sleep(10)
        await self.delete_cards(delete_card_no_list)
        await asyncio.sleep(30)
        await self.add_cards_to_unsorted_area(upload_card_list)

    # 同步读卡记录
    def sync_card_record(self):
        # print('start sync records....')
        taidii_client = TaidiiApi(settings.TAIDII_USERNAME, settings.TAIDII_PASSWORD)
        sql = "SELECT * FROM card_record WHERE is_upload=0"
        db.cur.execute(sql)
        card_records_data = db.cur.fetchall()
        for card_record_data in card_records_data:
            is_success = taidii_client.upload_record(card_record_data)
            card_record_data['is_upload'] = is_success
            db.update_record(card_record_data)

    async def sync(self):
        while True:
            await self.sync_card()
            self.sync_card_record()
            await asyncio.sleep(settings.CARD_SYNC_INTERNAL)

    def should_upload_record(self, data):
        info_type_dict = {
            '190100': '读卡信息',
            '190200': '出门开关信息',
            '190300': '门磁信息',
            '190400': '远程开门信息',
            '190500': '报警信息',
            '190600': '系统信息'
        }

        upload_keys = ['190100']
        data_type_key = data['category'] + data['command'] + data['parama']
        if data_type_key in upload_keys:
            return True
        return False

    def should_upload_card(self, card, cards_local):
        if not Card.validate_card_no(card['card_no']):
            return False
        cards_dict = {c['card_no']: c['is_upload'] for c in cards_local}
        if not card['card_no'] in cards_dict.keys():
            return True
        if cards_dict[card['card_no']] == 0:
            return True
        return False

    def get_delete_cards(self, cards_data, cards_data_local):
        # # print(cards_data)
        # print(cards_data_local)
        card_no_list = [card_data['card_no'] for card_data in cards_data if Card.validate_card_no(card_data['card_no'])]
        local_card_no_list = [card_data['card_no'] for card_data in cards_data_local]
        delete_card_no_list = []
        for card_no in local_card_no_list:
            if not Card.validate_card_no(card_no):
                delete_sql = "DELETE FROM card WHERE card_no=?"
                db.cur.execute(delete_sql, (card_no,))
            if card_no not in card_no_list:
                delete_sql = "DELETE FROM card WHERE card_no=?"
                db.cur.execute(delete_sql, (card_no,))
                delete_card_no_list.append(card_no)
        db.conn.commit()

        return delete_card_no_list


def search_device():
    '''
    UDP广播搜索设备
    '''
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    client.settimeout(5)
    # client.bind(('', 8101))
    start = 0
    # host = '192.168.1.35'
    host = '<broadcast>'
    devices = []
    devices_sn = []
    while start < 5:
        print('搜索局域网设备第{}次'.format(start + 1))
        data = '7E30303030303030303030303030303030FFFFFFFF19883D9001fe00000000021234b17E'
        data = binascii.unhexlify(data)
        client.sendto(data, (host, settings.UDP_PORT))
        time.sleep(1)
        start += 1
        try:
            res, addr = client.recvfrom(1024)
            res = binascii.hexlify(res).decode()
            print(res, addr)
            device = parse_search_res(res)
            device_sn = device['sn']
            print(device)

            if device_sn not in devices_sn:
                devices_sn.append(device_sn)
                devices.append(device)
        except:
            pass
    return devices


async def create_door(conifg):
    door = Door(**conifg)
    await door.open_connection()
    return door


def parse_search_res(res):
    device = {
        'info_code': res[2: 10],
        'sn': res[10: 42],
        'password': res[42: 50],
        'control_code': res[50: 56],
        'data_length': res[56: 64],
        'mac': res[64: 76],
        'ip': ipaddress.IPv4Address(int(res[76: 84], 16)),
        'mask': ipaddress.IPv4Address(int(res[84: 92], 16)),
        'gateway': ipaddress.IPv4Address(int(res[92: 100], 16)),
        'dns1': ipaddress.IPv4Address(int(res[100: 108], 16)),
        'dns2': ipaddress.IPv4Address(int(res[108: 116], 16)),
        'work_type': res[116: 118],
        'tcp_listen': int(res[118: 122], 16),
        'udp_listen': int(res[122: 126], 16),
        'remote_port': int(res[126: 130], 16),
        'remote_ip': ipaddress.IPv4Address(int(res[130: 138], 16)),
        'dhcp': res[138: 140],
        'remote_domain': hex_to_ascii(res[140:])
    }

    return device


async def main():
    devices = search_device()
    for device in devices:
        device_sn = device['sn']
        device_ip = str(device['ip'])
        # print(device_ip, device_sn)
        config = {'host': device_ip, 'sn': device_sn}
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
            asyncio.run(main())
        except Exception as e:
            print(e)
            print('restart monitoring...')
    # asyncio.run(main())
