import datetime

import requests

from card import Card
from db import db
from utils import str2datetime


class TaidiiApi(object):
    taidii_base_url = 'https://www.taidii.cn'

    def __init__(self, username, password):
        self.token = self.auth(username, password)
        self.session = self.get_session()

    # taidii账户认证
    def auth(self, username, password):
        auth_url = self.taidii_base_url + '/jwt-token-auth/'
        try:
            r = requests.post(auth_url, json={'username': username, 'password': password})
        except:
            r = None

        token = None
        if r:
            data = r.json()
            token = data['token']
        return token

    # 初始化session
    def get_session(self):
        s = requests.Session()
        headers = {
            'Authorization': f'JWT {self.token}'
        }
        s.headers = headers
        return s

    def upload_record(self, data):
        reader_dict = {
            '1门': '01',
            '2门': '02',
            '3门': '03',
            '4门': '04',
        }
        card = db.get_one_card(data['card_no'])
        if card is None:
            print('no card')
            return True
        device_no = f"{data['sn']}-{reader_dict[data['reader_no']]}"
        record_datetime = int(str2datetime(data['record_time'], format='%Y-%m-%d %H:%M:%S').timestamp()) * 1000

        url = self.taidii_base_url + '/api/attendance/attendance_device/card_attendance/'
        post_data = {
            'device_no': device_no,
            'attendance_list': [
                {
                    'people_id': card['people_id'],
                    'people_type': card['people_type'],
                    'record_datetime': record_datetime
                }
            ]
        }
        print(post_data)
        try:
            r = self.session.post(url, json=post_data)
        except:
            return False

        return True

    def get_all_cards_from_taidii(self):
        url = self.taidii_base_url + '/api/attendance/attendance_device/card_info/'
        try:
            r = self.session.get(url)
        except Exception as e:
            print(e)
            return None

        data = r.json()
        guardian_list = data['guardian_list']
        teacher_list = data['teacher_list']

        cards_data = []
        for guardian in guardian_list:
            if not self.validate_card(guardian):
                continue
            card_data = {}
            card_data['people_id'] = guardian['student_id']
            card_data['people_type'] = 0
            card_data['card_no'] = str(int(guardian['rfid']))
            card_data['name'] = guardian['student_name']
            cards_data.append(card_data)

        for teacher in teacher_list:
            if not self.validate_card(teacher):
                continue
            card_data = {}
            card_data['people_id'] = teacher['teacher_id']
            card_data['people_type'] = 1
            card_data['card_no'] = str(int(teacher['rfid']))
            card_data['name'] = teacher['teacher_name']
            cards_data.append(card_data)

        return cards_data

    def validate_card(self, card_data):
        return Card.validate_card_no(card_data['rfid'])
