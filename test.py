import settings
from api import TaidiiApi
from card import Card
from db import DB, db
from door import Door, search_device


def get_tcp_info():
    door = Door(host='192.168.2.35')
    res = door.get_tcp_info()
    print(res)


def set_tcp_info():
    door = Door()
    ip_info = {
        'ip': '192.168.3.35',
        'mask': '255.255.255.0',
        'gateway': '192.168.3.1',
        'dns1': '225.5.5.5',
        'dns2': '225.6.6.6',
        'work_type': '01',
        'tcp_listen': 8000,
        'udp_listen': 8101,
        'remote_port': 9000,
        'remote_ip': '192.168.3.155',
        'dhcp': '00',
        'remote_domain': ''
    }
    res = door.set_tcp_info(ip_info)
    print(res)


def get_version():
    door = Door()
    res = door.get_version()
    print(res)


def get_run_info():
    door = Door()
    res = door.get_run_info()
    print(res)


def get_all_cards():
    door = Door()
    res = door.get_all_cards()
    print(res)


def get_card_info():
    door = Door()
    res = door.get_card_info()
    print(res)


def add_cards_to_unsorted_area():
    card1 = Card(card_no=124)
    card2 = Card(card_no=125)
    door = Door()
    res = door.add_cards_to_unsorted_area([card1, card2])
    print(res)


def get_one_card():
    card_no = 123
    door = Door()
    res = door.get_one_card(card_no)
    print(res)


def clear_cards():
    door = Door()
    door.clear_cards()

    db.clear_cards()


def get_record_point_info():
    door = Door()
    res = door.get_record_point_info()
    print(res)


def monitor():
    door = Door()
    door.monitor()


def init_data():
    db.init_data()
    db.close()


def select_test():
    res = db.get_all_cards()
    print(res)


def monitor_test():
    door = Door()
    print(door.get_monitor_status())


def search():
    door = Door('192.168.1.88')
    print(door.sn)


def get_checksum():
    door = Door()
    data = '30303030303030303030303030303030FFFFFFFF19883D9001060000000000'
    checksum = door.check_sum(data)
    print(checksum)


def test_api():
    api = TaidiiApi(settings.TAIDII_USERNAME, settings.TAIDII_PASSWORD)
    res = api.get_all_cards_from_taidii()
    print(res)


def test_sync():
    door = Door()
    door.sync()


def test_select_exists():
    exist_sql = "SELECT id FROM card WHERE people_id=? AND people_type=? AND card_no=?"
    db.cur.execute(exist_sql, (79420, 0, '0245597063'))
    exists = db.cur.fetchone()
    print(exists)


if __name__ == '__main__':
    # get_version()
    # get_run_info()
    # add_cards_to_unsorted_area()
    # get_all_cards()
    # get_card_info()
    clear_cards()
    # get_one_card()
    # get_record_point_info()
    # get_tcp_info()
    # set_tcp_info()
    # monitor()
    # init_data()
    # select_test()
    # monitor_test()
    # search()
    # get_checksum()
    # test_api()
    test_sync()
    # test_select_exists()