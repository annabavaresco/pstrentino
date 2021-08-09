from Classes import Hospital, Queue, Patient
import mysql.connector 
from datetime import datetime, timedelta
import json
import requests
import time
from Converters import *
from Analyzers import comp_others, comp_more_severe, comp_less_severe


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


def extract_data(start_timestamp: str, end_timestamp: str, hospital_code):
    '''
        Connects to the db hosted by Amazon and retrieves data about the patients arrived at
        the emergency room identifies by "hospital_cose" between the "start_timestamp" and 
        the "end_timestamp".
        Hint: the timestamp string should have a format similar to the following one:

            '2021-06-17 10:40:00'
         
    ''' 
    start = datetime.strptime(start_timestamp, '%Y-%m-%d %H:%M:%S')
    end = datetime.strptime(end_timestamp, '%Y-%m-%d %H:%M:%S')

    connection = mysql.connector.connect(
    host = 'emergencyroom.ci8zphg60wmc.us-east-2.rds.amazonaws.com',
    port =  3306,
    user = 'admin',
    database = 'prova',
    password = 'emr00mtr3nt036'
    )

    connection.autocommit = True
    cursor = connection.cursor()

    query = "SELECT * FROM prova.ers2 WHERE codice_ospedale = %s AND timestamp \
             between %s AND %s"

    cursor.execute(query, [hospital_code, start, end])
    result = cursor.fetchall()
    connection.close()

    return result


def process_data_batch(data, code):

    '''
        Takes as input data retrieved from the db table er (converted into instances of the
        "hospital" class) and the code identifying the emergency room and compiles the df table 
        patients. 
        
        In order to do this, the wait time for each patient needs to be computed since it is
        NOT available in the apss api data.
    '''

    hospitals = [from_db_to_hospital(datum) for datum in data]

    #Creating a queue for each triage
    hospital_queues = {'white': Queue(code), 'giallo': Queue(code), 'green':Queue(code),\
        'blue': Queue(code), 'orange': Queue(code), 'red': Queue(code)}

    cols = ['white', 'green', 'blue', 'orange', 'red']
    prev = hospitals[0]
    
    #Initializing the queues 

    for col in cols:
        num_wait = prev.waiting[col]
        for i in range(num_wait):
           hospital_queues[col].add(Patient(code, col, \
                            comp_others(col, prev.waiting),comp_more_severe(col, prev.waiting),\
                                comp_less_severe(col, prev.waiting), prev.timestamp))
   
    for hospital in hospitals[1:]:
        
        for col in cols:
        
            if hospital.waiting[col] > prev.waiting[col]:
                increase_wait = hospital.waiting[col] - prev.waiting[col]
            
                if hospital.managing[col] > prev.managing[col]:
                    increase_manage = hospital.managing[col] - prev.managing[col]
                    n = increase_manage + increase_wait


                    for i in range(n):
                       hospital_queues[col].add(Patient(code, col, \
                            comp_others(col, hospital.waiting),comp_more_severe(col, hospital.waiting),\
                                comp_less_severe(col, hospital.waiting), hospital.timestamp))

                    hospital_queues[col].remove(increase_manage, hospital.timestamp)
            

                else:
                    n = increase_wait
            
                    for i in range(n):
                       hospital_queues[col].add(Patient(code, col, \
                            comp_others(col, hospital.waiting),comp_more_severe(col, hospital.waiting),\
                                comp_less_severe(col, hospital.waiting), hospital.timestamp))
        
            elif hospital.waiting[col] == prev.waiting[col]:
                if hospital.managing[col] > prev.managing[col]:
                    increase_manage = hospital.managing[col] - prev.managing[col]

                    for i in range(increase_manage):
                       hospital_queues[col].add(Patient(code, col, \
                            comp_others(col, hospital.waiting),comp_more_severe(col, hospital.waiting),\
                                comp_less_severe(col, hospital.waiting), hospital.timestamp))
                
                    hospital_queues[col].remove(increase_manage, hospital.timestamp)
        
            else:
                dim_wait = prev.waiting[col] - hospital.waiting[col]
                if hospital.managing[col] > prev.managing[col]:
                    increase_manage = hospital.managing[col] - prev.managing[col]
                    n = increase_manage - dim_wait

                    for i in range(n):
                       hospital_queues[col].add(Patient(code, col, \
                            comp_others(col, hospital.waiting),comp_more_severe(col, hospital.waiting),\
                                comp_less_severe(col, hospital.waiting), hospital.timestamp))
                
                    hospital_queues[col].remove(increase_manage, hospital.timestamp)
            
                else:
                   hospital_queues[col].remove(dim_wait, hospital.timestamp)
            
        prev = hospital


data = extract_data('2021-07-14 15:40:00', '2021-08-05 23:50:00', '001-PS-PSC')
process_data_batch(data, '001-PS-PSG')

        
