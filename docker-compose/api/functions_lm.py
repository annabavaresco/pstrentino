
import requests
import numpy as np
import pandas as pd
import json
from pprint import pprint
import datetime as dt

# GETTING NEW DATA FROM TRENTINO API by hospital code

# classe copiaincollata dal file che su github si chiama Ospedali.py
class Hospital:

    def __init__(self, code: str, in_gestione: dict(), in_attesa: dict(), timestamp):
        self.in_attesa = in_attesa
        self.codice = code
        self.in_gestione = in_gestione
        self.timestamp = timestamp


#Funzione copiaincollata dal file che su github si chiama Ospedali.py
def from_dict_to_hosp(ospedale):
    att = {'bianco': int(ospedale['risposta']['pronto_soccorso']['reparto']['attesa']['bianco']), \
           'verde': int(ospedale['risposta']['pronto_soccorso']['reparto']['attesa']['verde']), \
           'azzurro': int(ospedale['risposta']['pronto_soccorso']['reparto']['attesa']['azzurro']), \
           'arancio': int(ospedale['risposta']['pronto_soccorso']['reparto']['attesa']['arancio']), \
           'rosso': int(ospedale['risposta']['pronto_soccorso']['reparto']['attesa']['rosso'])}

    gest = {'bianco': int(ospedale['risposta']['pronto_soccorso']['reparto']['ambulatorio']['bianco']) +
                      int(ospedale['risposta']['pronto_soccorso']['reparto']['osservazione']['bianco']), \
            'verde': int(ospedale['risposta']['pronto_soccorso']['reparto']['ambulatorio']['verde']) +
                     int(ospedale['risposta']['pronto_soccorso']['reparto']['osservazione']['verde']), \
            'azzurro': int(ospedale['risposta']['pronto_soccorso']['reparto']['ambulatorio']['azzurro']) +
                       int(ospedale['risposta']['pronto_soccorso']['reparto']['osservazione']['azzurro']), \
            'arancio': int(ospedale['risposta']['pronto_soccorso']['reparto']['ambulatorio']['arancio']) +
                       int(ospedale['risposta']['pronto_soccorso']['reparto']['osservazione']['arancio']), \
            'rosso': int(ospedale['risposta']['pronto_soccorso']['reparto']['ambulatorio']['rosso']) +
                     int(ospedale['risposta']['pronto_soccorso']['reparto']['osservazione']['rosso'])}

    ret = Hospital(ospedale['risposta']['pronto_soccorso']['reparto']['codice'],
                   gest,
                   att,
                   dt.datetime.strptime(ospedale['risposta']['timestamp'].replace(' ore', ''), "%d/%m/%Y %H:%M"),
                   )
    return ret

#funzione copiaincollata dal file che in github si chiama pazienti.py

def comp_piu_gravi(colore, attesa):
    #dato un oggetto della classe ospedale, calcola quanti pazienti in attesa sono più gravi
    # di quello del parametro 'colore'
    col_list = ['verde', 'azzurro', 'arancio', 'rosso']
    res = 0
    if colore == 'bianco':
        for c in col_list:
            res += attesa[c]
    elif colore == 'verde':
        for c in col_list[1:]:
            res += attesa[c]
    elif colore == 'azzurro':
        for c in col_list[2:]:
            res += attesa[c]
    elif colore == 'arancio':
        res += attesa['rosso']
    return res


def get_data_by_code(code):
    hospitals = requests.get('https://servizi.apss.tn.it/opendata/STATOPS001.json').json()
    h = None
    for d in hospitals:
        if d['risposta']['pronto_soccorso']['reparto']['codice'] == code:
            h = from_dict_to_hosp(d)
    return h

def compute_timeslot(timestamp):
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


def predict_bianco(h, model):
    '''
    input: h è un oggetto della classe ospedale, model è un oggetto di tipo model.load di keras
    output: tempo di attesa previsto per ipotetico paziente che arriva con codice bianco
    nell'ospedale dell'input.
    '''
    wd = h.timestamp.weekday()
    ts = compute_timeslot(h.timestamp)
    oc = get_numeric_code(h.codice)
    altri = h.in_attesa['bianco']
    pg = comp_piu_gravi(h.in_attesa, 'bianco')
    diz = {'others': [altri], 'more_severe': [pg], 'weekday': [wd], 'timeslot': [ts], 'hosp_code': [oc]}
    new_data = pd.DataFrame(data=diz, index=['1'])
    return str(model.predict(new_data))
    

def predict_verde(h, model):
    '''
    input: h è un oggetto della classe ospedale, model è un oggetto di tipo model.load di keras
    output: tempo di attesa previsto per ipotetico paziente che arriva con codice verde
    nell'ospedale dell'input.
    '''
    wd = h.timestamp.weekday()
    ts = compute_timeslot(h.timestamp)
    oc = get_numeric_code(h.codice)
    altri = h.in_attesa['verde']
    pg = comp_piu_gravi(h.in_attesa, 'verde')
    diz = {'others': [altri], 'more_severe': [pg], 'weekday': [wd], 'timeslot': [ts], 'hosp_code': [oc]}
    new_data = pd.DataFrame(data=diz, index=['1'])
    return str(model.predict(new_data))
    

def predict_azzurro(h, model):
    '''
    input: h è un oggetto della classe ospedale, model è un oggetto di tipo model.load di keras
    output: tempo di attesa previsto per ipotetico paziente che arriva con codice azzurro
    nell'ospedale dell'input.
    '''
    wd = h.timestamp.weekday()
    ts = compute_timeslot(h.timestamp)
    oc = get_numeric_code(h.codice)
    altri = h.in_attesa['azzurro']
    pg = comp_piu_gravi(h.in_attesa, 'azzurro')
    diz = {'others': [altri], 'more_severe': [pg], 'weekday': [wd], 'timeslot': [ts], 'hosp_code': [oc]}
    new_data = pd.DataFrame(data=diz, index=['1'])
    return str(model.predict(new_data))
    

def predict_arancio(h, model):
    '''
    input: h è un oggetto della classe ospedale, model è un oggetto di tipo model.load di keras
    output: tempo di attesa previsto per ipotetico paziente che arriva con codice arancio
    nell'ospedale dell'input.
    '''
    wd = h.timestamp.weekday()
    ts = compute_timeslot(h.timestamp)
    oc = get_numeric_code(h.codice)
    altri = h.in_attesa['arancio']
    pg = comp_piu_gravi(h.in_attesa, 'arancio')
    diz = {'others': [altri], 'more_severe': [pg], 'weekday': [wd], 'timeslot': [ts], 'hosp_code': [oc]}
    new_data = pd.DataFrame(data=diz, index=['1'])
    return str(model.predict(new_data))
    

def predict_rosso(h, model):
    '''
    input: h è un oggetto della classe ospedale, model è un oggetto di tipo model.load di keras
    output: tempo di attesa previsto per ipotetico paziente che arriva con codice rosso
    nell'ospedale dell'input.
    '''
    wd = h.timestamp.weekday()
    ts = compute_timeslot(h.timestamp)
    oc = get_numeric_code(h.codice)
    altri = h.in_attesa['rosso']
    pg = comp_piu_gravi(h.in_attesa, 'rosso')
    diz = {'others': [altri], 'more_severe': [pg], 'weekday': [wd], 'timeslot': [ts], 'hosp_code': [oc]}
    new_data = pd.DataFrame(data=diz, index=['1'])
    return str(model.predict(new_data))
    