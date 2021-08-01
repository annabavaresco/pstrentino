from Classes import *
from datetime import datetime


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
