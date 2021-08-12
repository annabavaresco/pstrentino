from Classes import Hospital, Patient
import mysql.connector 
from datetime import datetime, timedelta
import json
import requests
import time
from Converters import *


def comp_more_severe(triage, t_waiting):
    '''
        Takes as input the triage color and the attribute .waiting of an instance of the sclass "Hospital"
        and outputs the number of patients having a level of priority which is higher than that of the 
        input color.  
    '''
    col_list = ['green', 'blue', 'orange', 'red']
    res = 0
    if triage == 'white':
        for c in col_list:
            res += t_waiting[c]
    elif triage == 'green':
        for c in col_list[1:]:
            res += t_waiting[c]
    elif triage == 'blue':
        for c in col_list[2:]:
            res += t_waiting[c]
    elif triage == 'orange':
        res += t_waiting['red']
    return res



def comp_less_severe(triage, t_waiting):
    '''
        Takes as input the triage color and the attribute .waiting of an instance of the sclass "Hospital"
        and outputs the number of patients having a level of priority which is higher than that of the 
        input color.  
    '''
    col_list = ['orange', 'blue', 'green', 'white']
    res = 0
    if triage == 'red':
        for c in col_list:
            res += t_waiting[c]
    elif triage == 'orange':
        for c in col_list[1:]:
            res += t_waiting[c]
    elif triage == 'blue':
        for c in col_list[2:]:
            res += t_waiting[c]
    elif triage == 'green':
        res += t_waiting['white']
    
    return res



def comp_others(triage, t_waiting):
    '''
        Takes as input the triage color and the attribute .waiting of an instance of the "hospital"
        class and returns the number of patients for the triage color decreased by one. 
    '''
    res = 0
    if t_waiting[triage]>1:
        res += t_waiting[triage]-1
    return res


    
def add_patient(pat: Patient, code: str, triage: str):
    '''
        Adds a patient to the queues json based on the hospital hode and triage color
        passed as input.
    '''
    with open("queues.json", "r") as f:
        hospitals = json.load(f)
    p = from_patient_to_dict(pat)
    hospitals[code][triage].append(p)

    with open("queues.json", "w") as f:
        json.dump(hospitals, f)
  

    
def remove_patient(num: int, end_timestamp, code, triage):
    '''
        Removes a patient from the quques json and stores it inside the database.
    '''
    with open("queues.json", "r") as f:
        hospitals = json.load(f)
    if num > len(hospitals[code][triage]):
        raise Exception('You are trying to remove more patients than the ones waiting!')
    if len(hospitals[code][triage]) == 0:
        raise Exception('Queue is empty: cannot remove patients!')
    for i in range(num):
        p = from_dict_to_patient(hospitals[code][triage].pop(0))
        p.t_end = str(end_timestamp)
        p.t_end = datetime.strptime(p.t_end, '%Y-%m-%d %H:%M:%S')
        p.waiting_time = p.t_end - p.t_start
        connection = mysql.connector.connect(
            host = 'emergencyroom.ci8zphg60wmc.us-east-2.rds.amazonaws.com',
            port =  3306,
            user = 'admin',
            database = 'er_trentino',
            password = 'emr00mtr3nt036'
            )

        connection.autocommit = True
        cursor = connection.cursor()

        query = "insert into er_trentino.patients (triage, hospital, start, end, wait_time,\
            others, more_severe, less_severe)\
                values (%s, %s, %s, %s, %s, %s, %s, %s)"

        cursor.execute(query, [p.triage, p.hospital, p.t_start, p.t_end, \
                        p.waiting_time, p.others,p.more_severe, p.less_severe])
        connection.close()
        
    with open("queues.json", "w") as f:
        json.dump(hospitals, f)
            


def get_prev():
    '''
        Retrieves data about the previous hospital from the prev.hosp json file.
    '''
    with open("prev_hosp.json", "r") as f:
        ret = json.load(f)  
    return ret



def set_prev(hospitals: dict):
    '''
    Takes as input a dict where each key is the code associated with a hospital and writes.
    it in the json file "prev_hosp.json"
    ''' 
    with open("prev_hosp.json", "w") as f:
        json.dump(hospitals, f)



def process_data_stream():
    '''
    Process data ingested as json file and compute patients and related values: others, more_severe, less_severe.
    '''
    triages = ['white', 'green', 'blue', 'orange', 'red']
    queues = ['001-PS-PSC','001-PS-PSG','001-PS-PSO','001-PS-PSP','001-PS-PS','006-PS-PS',\
        '007-PS-PS','010-PS-PS','004-PS-PS','014-PS-PS','005-PS-PS']

    prev = get_prev()

    if len(prev) == 0:
        prev_raw_data = requests.get('https://servizi.apss.tn.it/opendata/STATOPS001.json').json()
        prev_data_list = [from_dict_to_hosp(h) for h in prev_raw_data]
        
        for h in prev_data_list:
            for c in triages:
                n = h.waiting[c]
                
                p = Patient(h.code, c, comp_others(c, h.waiting),\
                    comp_more_severe(c, h.waiting),\
                            comp_less_severe(c, h.waiting), str(h.timestamp))

                for i in range(n):
                    add_patient(p, h.code, c)

        prev = from_loh_to_dict(prev_data_list)        
        time.sleep(600)
    
    current_raw_data = requests.get('https://servizi.apss.tn.it/opendata/STATOPS001.json').json()
    current_data_list = [from_dict_to_hosp(h) for h in current_raw_data]
    current = from_loh_to_dict(current_data_list)  

    for c in queues:
        for col in triages:

            if current[c]['waiting'][col] > prev[c]['waiting'][col]:
                increase_wait = current[c]['waiting'][col] - prev[c]['waiting'][col]
            

                if current[c]['managing'][col] > prev[c]['managing'][col]:
                    increase_manage = current[c]['managing'][col] - prev[c]['managing'][col]
                    n = increase_manage + increase_wait


                    for i in range(n):
                        add_patient(Patient(c, col, comp_others(col, current[c]['waiting']),\
                            comp_more_severe(col, current[c]['waiting']),\
                                comp_less_severe(col, current[c]['waiting']), current[c]['timestamp']),c,col)

                    remove_patient(increase_manage, current[c]['timestamp'], c, col)   

                else:
                    n = increase_wait
            
                    for i in range(n):
                        add_patient(Patient(c, col, comp_others(col, current[c]['waiting']),\
                            comp_more_severe(col, current[c]['waiting']),\
                                comp_less_severe(col, current[c]['waiting']), current[c]['timestamp']), c, col)
        
            elif current[c]['waiting'][col] == prev[c]['waiting'][col]:
                if current[c]['managing'][col] > prev[c]['managing'][col]:
                    increase_manage = current[c]['managing'][col] - prev[c]['managing'][col]

                    for i in range(increase_manage):
                        add_patient(Patient(c, col, comp_others(col, current[c]['waiting']),\
                            comp_more_severe(col, current[c]['waiting']),\
                                comp_less_severe(col, current[c]['waiting']), current[c]['timestamp']), c, col)
                
                    remove_patient(increase_manage, current[c]['timestamp'], c, col)
        
            else:
                dim_att = prev[c]['waiting'][col] - current[c]['waiting'][col]
                if current[c]['waiting'][col] > prev[c]['managing'][col]:
                    increase_manage = current[c]['managing'][col] - prev[c]['managing'][col]
                    n = increase_manage - dim_att

                    for i in range(n):
                        add_patient(Patient(c, col, comp_others(col, current[c]['waiting']),
                        comp_more_severe(col, current[c]['waiting']),\
                                comp_less_severe(col, current[c]['waiting']), current[c]['timestamp']), c, col)
                
                    remove_patient(increase_manage, current[c]['timestamp'], c, col)
            
                else:
                    remove_patient(dim_att, current[c]['timestamp'], c, col)
            
    set_prev(current)

    
    
def empty_queues():
    '''
        Removes all the queues presente in the "queues.json" file.
    '''
    with open("queues.json", "r") as f:
        hospitals = json.load(f)
        for h in hospitals:
            for color in hospitals[h]:
                hospitals[h][color] = [] 

    with open("queues.json", "w") as f:
        json.dump(hospitals, f)

        


# Batch processing version


def empty_prev():
    '''
        Removes all data present in the "prev_hosp.json" file. 
    '''
    with open("prev_hosp.json", "r") as f:
        prev = json.load(f)
        prev = {}

    with open("prev_hosp.json", "w") as f:
        json.dump(prev, f)

