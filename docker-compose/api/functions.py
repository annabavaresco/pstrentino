import requests
from datetime import datetime



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
    osp_dict = {'001-PS-PSC': 1,
                '001-PS-PSG': 2,
                '001-PS-PSO': 3,
                '001-PS-PS': 4,
                '001-PS-PSP': 5,
                '006-PS-PS': 6,
                '007-PS-PS': 7,
                '010-PS-PS': 8,
                '004-PS-PS': 9,
                '014-PS-PS': 10,
                '005-PS-PS': 11
                }
    return osp_dict[str_code]


def predict_white(hospital):
    '''
    Takes as input an instance of the "hospital" class containing the data which has just been
    retrieved from the apss api and outputs the expected wait time for a patient arriving at 
    the hospital specified as input with white triage color.
    '''
    
    wd = hospital.timestamp.weekday()
    ts = compute_timeslot(hospital.timestamp)
    hc = get_numeric_code(hospital.code)
    others = hospital.waiting['white']
    ms = comp_more_severe(hospital.waiting, 'white')
    d = {"instances": [[wd, ts, hc, others, ms]]}
    pred = requests.post('http://models_api:8501/v1/models/model_WHITE:predict', json=d).json()
    return str(pred['predictions'][0][0]).split('.')[0]

def predict_green(hospital):
    '''
        Takes as input an instance of the "hospital" class containing the data which has just been
        retrieved from the apss api and outputs the expected wait time for a patient arriving at 
        the hospital specified as input with green triage color.
    '''
    
    wd = hospital.timestamp.weekday()
    ts = compute_timeslot(hospital.timestamp)
    hc = get_numeric_code(hospital.code)
    others = hospital.waiting['green']
    ms = comp_more_severe(hospital.waiting, 'green')
    d = {"instances": [[wd, ts, hc, others, ms]]}
    pred = requests.post('http://models_api:8501/v1/models/model_GREEN:predict', json=d).json()
    return str(pred['predictions'][0][0]).split('.')[0]

def predict_blue(hospital):
    '''
        Takes as input an instance of the "hospital" class containing the data which has just been
        retrieved from the apss api and outputs the expected wait time for a patient arriving at 
        the hospital specified as input with blue triage color.
    '''
    wd = hospital.timestamp.weekday()
    ts = compute_timeslot(hospital.timestamp)
    hc = get_numeric_code(hospital.code)
    others = hospital.waiting['blue']
    ms = comp_more_severe(hospital.waiting, 'blue')
    d = {"instances": [[wd, ts, hc, others, ms]]}
    pred = requests.post('http://models_api:8501/v1/models/model_BLUE:predict', json=d).json()
    return str(pred['predictions'][0][0]).split('.')[0]
    
def predict_orange(hospital):
    '''
        Takes as input an instance of the "hospital" class containing the data which has just been
        retrieved from the apss api and outputs the expected wait time for a patient arriving at 
        the hospital specified as input with orange triage color.
    '''
    wd = hospital.timestamp.weekday()
    ts = compute_timeslot(hospital.timestamp)
    hc = get_numeric_code(hospital.code)
    others = hospital.waiting['orange']
    ms = comp_more_severe(hospital.waiting, 'orange')
    d = {"instances": [[wd, ts, hc, others, ms]]}
    pred = requests.post('http://models_api:8501/v1/models/model_ORANGE:predict', json=d).json()
    return str(pred['predictions'][0][0]).split('.')[0]
    

def predict_red(hospital):
    '''
        Takes as input an instance of the "hospital" class containing the data which has just been
        retrieved from the apss api and outputs the expected wait time for a patient arriving at 
        the hospital specified as input with red triage color.
    '''
    wd = hospital.timestamp.weekday()
    ts = compute_timeslot(hospital.timestamp)
    hc = get_numeric_code(hospital.code)
    others = hospital.waiting['red']
    ms = comp_more_severe(hospital.waiting, 'red')
    d = {"instances": [[wd, ts, hc, others, ms]]}
    pred = requests.post('http://models_api:8501/v1/models/model_RED:predict', json=d).json()
    return str(pred['predictions'][0][0]).split('.')[0].strip('-')

