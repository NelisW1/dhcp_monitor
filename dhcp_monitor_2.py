from __future__ import print_function
from scapy.all import sniff
import time
import sqlalchemy
import sqlite3
import datetime
import pandas as pd

import requests
import json


def pushbullet_message(title, body, token):
    msg = {"type": "note", "title": title, "body": body}
    TOKEN = token
    headers = {'Authorization': 'Bearer ' + TOKEN,
               'Content-Type': 'application/json'}
    resp = requests.post('https://api.pushbullet.com/v2/pushes',
                         data=json.dumps(msg),
                         headers=headers)
    if resp.status_code != 200:
        raise Exception('Error', resp.status_code)
    else:
        print(body)


def store_in_db(df: pd.DataFrame, db_name, dir=''):

    if len(dir) == 0:
        db_create_path = f'sqlite:///{db_name}.db'
        db_path = f'{db_name}.db'
    else:
        db_create_path = f'sqlite:////{dir}/{db_name}.db'
        db_path = f'{dir}/{db_name}.db'

    # create db & connection
    engine = sqlalchemy.create_engine(db_create_path)
    con = sqlite3.connect(db_path)
    cursor = con.cursor()

    # create table
    create_q = f"""
    CREATE TABLE IF NOT EXISTS {db_name}(
        p_id INTEGER PRIMARY_KEY,
        hostname VARCHAR(100) NOT NULL,
        requested_addr VARCHAR(20) NOT NULL,
        server_id VARCHAR(20) NOT NULL,
        vendor_class_id VARCHAR(20),
        vendor VARCHAR(10) NOT NULL,
        date DATETIME NOT NULL
    )
    """
    cursor.execute(create_q)
    con.commit()

    # data to db
    df.to_sql(db_name, engine, if_exists='append', index=False)
    cursor.close()
    con.close()


def handle_dhcp_packet(packet, pb_token):
    hostname = ''
    requested_addr = ''
    server_id = ''
    vendor_class_id = ''
    pad_list = []
    vendor = ''

    # Request Message
    if 'DHCP' in packet and packet['DHCP'].options[0][1] == 3:
        print('package entered')
        print(packet['DHCP'].options)
        for item in packet['DHCP'].options:
            if item[0] == 'hostname':
                hostname = item[1].decode()
            elif item[0] == 'requested_addr':
                requested_addr = item[1]
            elif item[0] == 'server_id':
                server_id = item[1]
            elif item[0] == 'vendor_class_id':
                vendor_class_id = item[1].decode()
            elif item == 'pad':
                pad_list.append(item)

        # vendor variable
        l_vendor = vendor_class_id.lower()
        if 'msft' in l_vendor:
            vendor = 'Microsoft'
        elif 'cisco' in l_vendor:
            vendor = 'Cisco Systems'
        elif 'alcatel' in l_vendor:
            vendor = 'Alcatel'
        elif 'android' in l_vendor:
            vendor = 'Android'
        elif len(pad_list) <= 9:
            vendor = 'Apple'
        elif len(pad_list) > 9:
            vendor = 'Linux'
        else:
            vendor = 'other'

        # vendor_class_id adjustment
        if len(vendor_class_id) == 0:
            vendor_class_id = 'NVT'

        date = datetime.datetime.now()
        date = date.strftime("%Y-%m-%d %H:%M:%S")
        print(date)

        # add to DHCP db
        data = {
            'hostname': [hostname],
            'requested_addr': [requested_addr],
            'server_id': [server_id],
            'vendor_class_id': [vendor_class_id],
            'vendor': [vendor],
            'date': [date]
        }

        df = pd.DataFrame(data)
        store_in_db(df=df, db_name='DHCP')

        # Send message
        title = "DHCP"
        message = f"{hostname} connected to home."
        pushbullet_message(title, message, pb_token)



if __name__ == "__main__":
    pb_token = 'INSERT TOKEN'
    host = sniff(filter="udp and (port 67 or 68)", prn=lambda x: handle_dhcp_packet(x, pb_token))

    try:
        time.sleep(1)
    except KeyboardInterrupt:
        print("interrupted")
