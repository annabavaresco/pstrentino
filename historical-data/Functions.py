from Classes import Hospital, Queue, Patient
import mysql.connector 
from datetime import datetime, timedelta
import json
import requests
import time

def from_dict_to_hosp(hospital):
    '''
        Takes as input a dictionary retrieved from the apss api json and converts it into an 
        instance of the "hospital" class.
    '''

    wait = {'white':int(hospital['risposta']['pronto_soccorso']['reparto']['attesa']['bianco']),\
            'green': int(hospital['risposta']['pronto_soccorso']['reparto']['attesa']['verde']),\
                'blue': int(hospital['risposta']['pronto_soccorso']['reparto']['attesa']['azzurro']),\
                    'orange': int(hospital['risposta']['pronto_soccorso']['reparto']['attesa']['arancio']),\
                        'red': int(hospital['risposta']['pronto_soccorso']['reparto']['attesa']['rosso'])}

    manage = {'white': int(hospital['risposta']['pronto_soccorso']['reparto']['ambulatorio']['bianco']) +
                      int(hospital['risposta']['pronto_soccorso']['reparto']['osservazione']['bianco']), \
            'green': int(hospital['risposta']['pronto_soccorso']['reparto']['ambulatorio']['verde']) +
                     int(hospital['risposta']['pronto_soccorso']['reparto']['osservazione']['verde']), \
            'blue': int(hospital['risposta']['pronto_soccorso']['reparto']['ambulatorio']['azzurro']) +
                       int(hospital['risposta']['pronto_soccorso']['reparto']['osservazione']['azzurro']), \
            'orange': int(hospital['risposta']['pronto_soccorso']['reparto']['ambulatorio']['arancio']) +
                       int(hospital['risposta']['pronto_soccorso']['reparto']['osservazione']['arancio']), \
            'red': int(hospital['risposta']['pronto_soccorso']['reparto']['ambulatorio']['rosso']) +
                     int(hospital['risposta']['pronto_soccorso']['reparto']['osservazione']['rosso'])}
  


    ret = Hospital(hospital['risposta']['pronto_soccorso']['reparto']['codice'],
                    manage,
                    wait,
                    datetime.strptime(hospital['risposta']['timestamp'].replace(' ore',''), "%d/%m/%Y %H:%M"),       # ore in italiano  
    )
    return ret



def from_lod_to_los(dictionaries_list):
    '''
        Takes as input a list of dictionaries and returns them converted into instances of the 
        "hospital" class. 
    '''
    ret = []
    for dictionary in dictionaries_list:
        ret.append(from_dict_to_hosp(dictionary))
    return ret


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

    query = "SELECT * FROM prova.ers2 WHERE hospital_code = %s AND timestamp \
             between %s AND %s"

    cursor.execute(query, [hospital_code, start, end])
    result = cursor.fetchall()
    connection.close()

    return result


def from_db_to_hospital(db_row):
    '''
        Takes as input data stored in one record of the database and converts it into 
        an instance of the "hospital" class.
    '''

    wait = {'white':db_row[2], 'green': db_row[6], \
        'blue': db_row[8], 'orange': db_row[10], 'red': db_row[12]}
    manage = {'white': db_row[3], 'green': db_row[7],\
        'blue': db_row[9], 'orange': db_row[11], 'red': db_row[13]}
    h = Hospital(db_row[1], manage, wait, db_row[0])

    return h




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
                            comp_others(col, prev),comp_more_severe(col, prev),\
                                comp_less_severe(col, prev), prev.timestamp))
   
    for hospital in hospitals[1:]:
        
        for col in cols:
        
            if hospital.waiting[col] > prev.waiting[col]:
                increase_wait = hospital.waiting[col] - prev.waiting[col]
            
                if hospital.managing[col] > prev.managing[col]:
                    increase_manage = hospital.managing[col] - prev.managing[col]
                    n = increase_manage + increase_wait


                    for i in range(n):
                       hospital_queues[col].add(Patient(code, col, \
                            comp_others(col, hospital),comp_more_severe(col, hospital),\
                                comp_less_severe(col, hospital), hospital.timestamp))

                    hospital_queues[col].remove(increase_manage, hospital.timestamp)
            

                else:
                    n = increase_wait
            
                    for i in range(n):
                       hospital_queues[col].add(Patient(code, col, \
                            comp_others(col, hospital),comp_more_severe(col, hospital),\
                                comp_less_severe(col, hospital), hospital.timestamp))
        
            elif hospital.waiting[col] == prev.waiting[col]:
                if hospital.managing[col] > prev.managing[col]:
                    increase_manage = hospital.managing[col] - prev.managing[col]

                    for i in range(increase_manage):
                       hospital_queues[col].add(Patient(code, col, \
                            comp_others(col, hospital),comp_more_severe(col, hospital),\
                                comp_less_severe(col, hospital), hospital.timestamp))
                
                    hospital_queues[col].remove(increase_manage, hospital.timestamp)
        
            else:
                dim_wait = prev.waiting[col] - hospital.waiting[col]
                if hospital.managing[col] > prev.managing[col]:
                    increase_manage = hospital.managing[col] - prev.managing[col]
                    n = increase_manage - dim_wait

                    for i in range(n):
                       hospital_queues[col].add(Patient(code, col, \
                            comp_others(col, hospital),comp_more_severe(col, hospital),\
                                comp_less_severe(col, hospital), hospital.timestamp))
                
                    hospital_queues[col].remove(increase_manage, hospital.timestamp)
            
                else:
                   hospital_queues[col].remove(dim_wait, hospital.timestamp)
            
            prev = hospital


def from_patient_to_dict(pat: Patient):
    '''
        Takes as input an instance of the "Patient" class and converts it into a dict. 
    '''
    ret = {
        "hospital" : pat.hospital,
        "triage" : pat.triage,
        "others" : pat.others,
        "more_severe" : pat.more_severe,
        "less_severe" : pat.less_severe,
        "t_start" : str(pat.t_start),
        "t_end" : str(pat.t_end),
        "waiting_time": str(pat.waiting_time)
    }
    return ret

def from_dict_to_patient(d: dict):
    '''
        Takes as input a dict and returns an instance of the class "Patient".
    '''
    start = datetime.strptime(d["t_start"], '%Y-%m-%d %H:%M:%S')
    if (d["t_end"] is None) or (d["t_end"] == 'None'):
        end = None
        last = 0
    else:

        end = datetime.strptime(d["t_end"], '%Y-%m-%d %H:%M:%S')
        last = end - start

    pat = Patient(
        d["hospital"],
        d["triage"],
        d["others"],
        d["more_severe"],
        d["less_severe"],
        start)
    pat.t_end = end
    pat.waiting_time = last
    
    return pat

def from_loh_to_dict(hospitals):
    '''
    Takes as input a list of hospitals (meaning instances of the class "hospital") and returns
    a dict where each key is the code of the hospital.
    '''
    ret = dict()
    for h in hospitals:
        ret[h.code] = {"waiting": h.waiting, "managing": h.managing,
        "timestamp": str(h.timestamp)}
    return ret
    
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

        query = "insert into er_trentino.er_patients_stream (triage, hospital, start, end, wait_time,\
            others, more_severe, less_severe)\
                values (%s, %s, %s, %s, %s, %s, %s, %s)"

        cursor.execute(query, [p.triage, p.hospital, p.t_start, p.t_end, \
                        p.waiting_time, p.others,p.more_severe, p.less_severe])
        connection.close()
        
    with open("queues.json", "w") as f:
        json.dump(hospitals, f)
            


def get_prev():
    '''
        Retrieves data about the previous hospital from the prev.hosp json file.-
    '''
    with open("prev_hosp.json", "r") as f:
        ret = json.load(f)
    
    return ret


def set_prev(hospitals: dict):
    '''
    Takes as input a dict where each key is the code associated with a hospital and writes
    it in the json file "prev_hosp.json"
    ''' 

    with open("prev_hosp.json", "w") as f:
        json.dump(hospitals, f)



def process_data_stream():

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

def empty_prev():
    '''
        Removes all data present in the "prev_hosp.json" file. 
    '''
    with open("prev_hosp.json", "r") as f:
        prev = json.load(f)
        prev = {}

    with open("prev_hosp.json", "w") as f:
        json.dump(prev, f)
        


