
import requests
import json
import time
from pprint import pprint
from Functions import from_lod_to_los
import mysql.connector

def update_er_table():
    resp = requests.get('https://servizi.apss.tn.it/opendata/STATOPS001.json')
    hosp = resp.json()

    hospitals = from_lod_to_los(hosp)

    connection = mysql.connector.connect(
        host = 'emergencyroom.ci8zphg60wmc.us-east-2.rds.amazonaws.com',
        port =  3306,
        user = 'admin',
        database = 'prova',
        password = 'emr00mtr3nt036'
    )

    connection.autocommit = True
    cursor = connection.cursor()

    query = "insert into ers2 (timestamp, hospital_code, white_waiting,\
        white_managing, yellow_waiting, yellow_managing, green_waiting,\
            green_managing, blue_waiting, blue_managing, orange_waiting,\
                orange_managing, red_waiting, red_managing)\
                    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

    for hospital in hospitals:
        cursor.execute(query, [hospital.timestamp, hospital.code, hospital.waiting.white,\
            hospital.managing.white, hospital.waiting.yellow, hospital.managing.yellow,\
                hospital.waiting.green, hospital.managing.green, hospital.waiting.blue,\
                    hospital.managing.blue, hospital.waiting.orange, hospital.managing.orange,\
                        hospital.waiting.red, hospital.managing.red])

    connection.close()

if __name__=="__main__":
    update_er_table()




