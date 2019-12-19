'''
授权卡
'''
import datetime

from utils import dec2hex


class Card(object):
    '''
    授权卡格式：
第一(5byte)	第三(4byte)	第四(5byte)	第五（4byte）	第六（2byte）	第七(0.5byte)	第八(0.5byte)	第九(1byte)	第十(4byte)	第十一(1byte)	第十二(6byte)
卡号	密码	有效期	开门时段	有效次数	权限	特权	状态	节假日	出入标志	最近读卡时间
总33字节 0x21
密码：4字节，格式为BCD码，即0x12345678表示密码是12345678，密码是8个数字，每个数字的取值是0-9，如果密码不足8为则在后面空位上写入占位符0xF，例如密码是8765这四个数字，则密码应发送为0x8745FFFF
有效期：BCD码，格式《年月日时分》，最大2099年12月31日23时59分，秒部分自动为59秒。
有效次数：取值范围0-65534，0表示次数用光了。65535表示不受限制。
开门时段：4个字节每个字节对应一个端口，顺序从左至右，分别对应1-4号门，即低位为1门高位为4号门。每字节取值范围：1-64，0表示不受限制。例如：0x01020304 表示1号门对应1号开门时段，——，4号门对应4号开门时段。
权限：每一位代表一个门，从右至左，依次是1、2、3、4门。例如0011表示第一门和第二门有效。
Bit3	Bit2	Bit1	Bit0
4号门	3号门	2号门	1号门

状态：0：正常状态；1：挂失；2：黑名单；
特权：从右至左一次表示第1、2、3、4位，具体内容如下：
Bit0--Bit2	特权
0	普通卡
1(001b)	首卡
2(010b)	常开
3(011b)	巡更
4(100b)	防盗设置卡

Bit3	节假日受限制

节假日：从左至右，依次是1-32组节假日。  1 -> 32
出入标志：每两位个位代表一个门，从左至右1->4，参看表：
顺序：
Bit6、Bit7	1门
Bit4、Bit5	2门
Bit2、Bit3	3门
Bit0、Bit1	4门
值：
值	解释
3、0	出入有效
1	入有效
2	出有效

最近读卡时间：此参数由设备设置，写入时填写&HFFFFFFFFFFFF即可。此参数表示卡片上次读卡时间。
    '''

    def __init__(self, card_no, password='ffffffff', expire_time='9912312359', date_range_code='00000000',
                 expire_count=65535, permission='F',
                 privilege='0', status='00', vocation_code='00000000', in_out_flag='00', last_read='FFFFFFFFFFFF'):
        data = '7E4D432D35383234543239303435363937FFFFFFFF51438B140704000000002500000001000000007BFFFFFFFF200108113201010101FFFFF0000000000000191208114002497E'
        data = '000000007BFFFFFFFF200108113201010101FFFFF0000000000000191208114002'
        self.card_no = dec2hex(int(card_no)).zfill(10)
        self.password = password
        self.expire_time = expire_time
        self.date_range_code = date_range_code
        self.expire_count = dec2hex(expire_count)
        self.permission = permission
        self.privilege = privilege
        self.status = status
        self.vocation_code = vocation_code
        self.in_out_flag = in_out_flag
        self.last_read = last_read

    def __eq__(self, other):
        return self.card_no == other.card_no

    @property
    def data(self):
        return self.card_no + self.password + self.expire_time + self.date_range_code + self.expire_count + self.permission + self.privilege + self.status + self.vocation_code + self.in_out_flag + self.last_read

    @staticmethod
    def validate_card_no(card_no):
        if isinstance(card_no, str):
            if not card_no:
                return False
            if len(card_no) > 10:
                return False
            try:
                card_no = int(card_no)
            except ValueError:
                return False

        if isinstance(card_no, int):
            return True
        else:
            return False


