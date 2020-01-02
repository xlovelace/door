import datetime
import ipaddress
import textwrap


def hex_to_ascii(hex_str):
    hex_list = textwrap.fill(hex_str, width=2).split()
    return ''.join([chr(int(s, 16)) for s in hex_list])


def ip_to_hex(ip_str):
    return hex(int(ipaddress.IPv4Address(ip_str)))[2:]


def str_to_hex(s):
    return ''.join([hex(ord(c)).replace('0x', '') for c in s])


def dec2bin(n):
    try:
        n = int(n)
    except ValueError:
        return ''
    return bin(n)[2:]


def dec2hex(n):
    try:
        n = int(n)
    except ValueError:
        return ''
    return hex(n)[2:]


def parse_bcd(data):
    '''
    BCD码转换成10进制数列表
    '''
    return [int(c, 16) for c in data]


def get_bcd_password(data):
    bcd_list = parse_bcd(data)
    password = ''
    for n in bcd_list:
        if n > 9:
            break
        password += str(n)
    return password


def str2datetime(datetime_str, format='%y%m%d%H%M'):
    try:
        dt = datetime.datetime.strptime(datetime_str, format)
        dt = dt.replace(second=59)
    except ValueError as e:
        print(e)
        return None
    return dt
