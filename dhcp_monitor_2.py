from scapy.all import sniff
import time
import sqlalchemy
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
    else:
        db_create_path = f'sqlite:////{dir}/{db_name}.db'

    # create db and insert data
    engine = sqlalchemy.create_engine(db_create_path)
    df.to_sql(db_name, engine, if_exists='append', index=False)


def handle_dhcp_packet(packet, pb_token):
    hostname = ''
    requested_addr = ''
    server_id = ''

    # Request Message
    if 'DHCP' in packet and packet['DHCP'].options[0][1] == 3:
        print('package entered')
        for item in packet['DHCP'].options:
            if item[0] == 'hostname':
                hostname = item[1].decode()
                print(hostname)
            elif item[0] == 'requested_addr':
                requested_addr = item[1]
                print(requested_addr)
            elif item[0] == 'server_id':
                server_id = item[1]
                print(server_id)

        date = datetime.datetime.now()
        print(date)

        # add to DHCP db
        data = {
            'hostname': [hostname],
            'requested_addr': [requested_addr],
            'server_id': [server_id],
            'date': [date]
        }

        df = pd.DataFrame(data)
        store_in_db(df=df, db_name='DHCP')

        # Send message
        title = "DHCP"
        message = f"{hostname} connected to home."
        pushbullet_message(title, message, pb_token)

def test(packet):
    print(packet['DHCP'].options)
    print("")
    print(packet['Ether'])
    print("")
    print(packet['IP'].src, packet['IP'].dst)


if __name__ == "__main__":
    pb_token = 'o.eF4QSWcyMswqDzX5b72MjPCLiHa7DpUn'
    host = sniff(filter="udp and (port 67 or 68)", prn=lambda x: handle_dhcp_packet(x, pb_token))

    try:
        time.sleep(2)
    except KeyboardInterrupt:
        print("interrupted")