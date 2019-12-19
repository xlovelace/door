import os
import sqlite3


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class DB(object):
    def __init__(self):
        self.conn = self.connect()
        self.cur = self.conn.cursor()

    def connect(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, 'sqlite3.db')
        conn = sqlite3.connect(path)
        conn.row_factory = dict_factory
        return conn

    def close(self):
        self.conn.close()

    def init_data(self):
        # 创建考勤卡表
        self.conn.execute('''
              CREATE TABLE IF NOT EXISTS card
                 (id INTEGER  PRIMARY KEY NOT NULL,
                  people_id INT NOT NULL,
                  people_type INT NOT NULL,
                  card_no TEXT,
                  name TEXT,
                  is_upload INT DEFAULT 0
                 );
                 ''')

        # 创建刷卡记录表
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS card_record
            (id INTEGER PRIMARY KEY NOT NULL ,
            card_no TEXT,
            record_time TEXT,
            reader_no TEXT,
            status INT,
            is_upload INT DEFAULT 0
            );
        ''')

        self.conn.commit()
        self.close()

    def save_record(self, data):
        insert = "INSERT INTO card_record (card_no, record_time, reader_no, status, is_upload) VALUES (?, ?, ?, ?, ?)"
        self.cur.execute(insert,
                         (data['card_no'], data['record_time'], data['reader_no'], data['status'], data['is_upload']))
        self.conn.commit()

    def get_one_card(self, card_no):
        sql = "SELECT * FROM card WHERE card_no=?"
        self.cur.execute(sql, (card_no,))
        return self.cur.fetchone()

    def insert_card(self, card_data):
        sql = "INSERT INTO card (people_id, people_type, card_no, name , is_upload) VALUES (?, ?, ?, ?, ?)"
        self.cur.execute(sql, (
            card_data['people_id'], card_data['people_type'], card_data['card_no'], card_data['name'],
            card_data.get('is_upload', 0)))
        self.conn.commit()

    def update_card(self, card_data):
        sql = "UPDATE card SET people_id=?, people_type=?, name=?, is_upload=? WHERE card_no=?"
        self.cur.execute(sql, (
            card_data['people_id'], card_data['people_type'], card_data['name'], card_data['is_upload'],
            card_data['card_no']))
        self.conn.commit()

    def get_all_cards(self):
        sql = "SELECT * FROM card"
        self.cur.execute(sql)
        return self.cur.fetchall()

    def save_card(self, card_data):
        if self.get_one_card(card_data['card_no']) is None:
            self.insert_card(card_data)
        else:
            self.update_card(card_data)

    def clear_cards(self):
        sql = "DELETE FROM card"
        self.cur.execute(sql)
        self.conn.commit()


db = DB()
