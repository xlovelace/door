import socket
import struct
import binascii
from urllib import request

HOST = '192.168.2.35'  # The remote host
PORT = 8000  # The same port as used by the server


def data_list(data):
    res = []
    while data:
        str1 = data[0: 2]
        int_s = int(str1, 16)
        res.append(int_s)
        data = data[2:]
    return res


# 将16进制数据当做字节流传递
def dataSwitch(data):
    return binascii.unhexlify(data)


def check_sum(data):
    return hex(sum(data_list(data)))[-2:]


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        # data = b'\x7E\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\xFF\xFF\xFF\xFF\x19\x88\x3D\x90\x01\x02\x00\x00\x00\x00\x00\x6D\x7E'
        # data = b'\x7e\x4d\x43\x2d\x35\x38\x32\x34\x54\x32\x39\x30\x34\x35\x36\x39\x37\xff\xff\xff\xff\x19\x88\x3d\x90\x01\x06\x00\x00\x00\x00\x00\x6d\x7e'
        data = b'~0000000000000000\xff\xff\xff\xff\x19\x88=\x90\x01\x02\x00\x00\x00\x00\x00m~'
        data = '7e4d432d35383234543239303435363937ffffffff19883d9001060000000000ff7e'
        data = '7E30303030303030303030303030303030FFFFFFFF19883D90010200000000006d7E'
        data = dataSwitch(data)
        print(data)
        s.sendall(data)
        data = s.recv(1024)
    print(repr(data))
    print('Received', binascii.hexlify(data).decode())


if __name__ == '__main__':
    main()
