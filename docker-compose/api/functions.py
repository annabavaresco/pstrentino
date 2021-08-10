from datetime import datetime
import pandas as pd


class Hospital:

    def __init__(self, code: str, waiting: dict(), managing: dict(), timestamp):
        
        self.code = code
        self.waiting = waiting
        self.managing = managing
        self.timestamp = timestamp



def from_dict_to_hosp(hospital):
    '''
        Takes as input one of the dictionaries of the json available in the apss api and converts
        it into an instance of the "hospital" class.  
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


def compute_timeslot(timestamp):
    '''
        Takes as input the timestamp corresponding to the time of arrival and outputs an integer
        identifying the specific timeslot. Since data from the apss api is updated every 10 minutes,
        the time of arrival can only assume values between 1 and 144.
    '''
    timeslot_dict = {}
    ind = 1
    for n in range(24):
        if n < 10:
            hrs = '0' + str(n)
        else:
            hrs = str(n)

        for i in range(6):
            mins = str(i) + '0'
            s = hrs + ':' + mins + ':' + '00'
            timeslot_dict[s] = ind
            ind += 1

    return timeslot_dict[timestamp.strftime("%H:%M:%S")]


def get_numeric_code(str_code):
    '''
        Takes as input the code identifying the emergency room and converts it into an integer.
        Since the emergency rooms are 11, the outputs of this finction can only range from 1
        to 11.
    '''
    hosp_dict = {'001-PS-PSC': 10,
                '001-PS-PSG': 11,
                '001-PS-PSO': 1,
                '001-PS-PS': 2,
                '001-PS-PSP': 3,
                '006-PS-PS': 4,
                '007-PS-PS': 5,
                '010-PS-PS': 6,
                '004-PS-PS': 7,
                '014-PS-PS': 8,
                '005-PS-PS': 9
                }
    return hosp_dict[str_code]

    
def predict_orange(model, hospital):
    '''
        Takes as input the loaded model and an instance of the "hospital" class containing the data which has just been
        retrieved from the apss api and outputs the expected wait time for a patient arriving at 
        the hospital specified as input with orange triage color.
    '''

    others = hospital.waiting['orange']
    wd = hospital.timestamp.weekday()
    d= {'weekday': wd, 'others': others}
    new_d = pd.DataFrame(data=d, index=['1'])
    return str(model.predict(new_d)).lstrip('[').split('.')[0]

def predict_wgb(model, hospital, triage_color):
    '''
        Takes as input the loaded model, an instance of the "hospital" class containing the data which has just been
        retrieved from the apss api and the triage color for which we would like to obtain the 
        prediction. The output is the expected wait time for a patient arriving at 
        the hospital specified as input with red triage color.
    '''
    wd = hospital.timestamp.weekday()
    ts = compute_timeslot(hospital.timestamp)
    hc = get_numeric_code(hospital.code)
    others = hospital.waiting[triage_color]
    ms = comp_more_severe(hospital.waiting, triage_color)
    color_codes = {'white': 1, 'green': 1, 'blue': 3}
    triage_color_code = color_codes[triage_color]

    d= {'triage' :triage_color_code, 'hosp_code': hc, 'others': others,\
        'more_severe': ms, 'weekday': [wd], 'timeslot':ts}
    new_d = pd.DataFrame(data=d, index=['1'])
    return str(model.predict(new_d)).lstrip('[').split('.')[0]

def predict_totg(model, hospital, triage_color):
    '''
        Takes as input the loaded model, an instance of the "hospital" class containing the data which has just been
        retrieved from the apss api and the triage color for which we would like to obtain the 
        prediction. The output is the expected wait time for a patient arriving at 
        the hospital specified as input with red triage color.
    '''
    wd = hospital.timestamp.weekday()
    others = hospital.waiting[triage_color]
    ms = comp_more_severe(hospital.waiting, triage_color)
    color_codes = {'white': 1, 'green': 2, 'blue': 3}
    triage_color_code = color_codes[triage_color]
    d = {'triage': triage_color_code, 'others': others, 'more_severe': ms, 'weekday': wd}
    new_d = pd.DataFrame(data=d, index=['1'])
    return str(model.predict(new_d)).lstrip('[').split('.')[0]


