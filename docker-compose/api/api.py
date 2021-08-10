from functions import from_dict_to_hosp
from flask import Flask
import requests
from flask_restful import Api, Resource
from functions import predict_orange, predict_wgb, predict_totg
import pickle
import os

app = Flask(__name__)
api = Api(app)

class Predictions(Resource):
    def get(self):
        '''
            Returns a dictionary with the predictions for each trage color of each emergency room.
        '''
        hospitals = requests.get('https://servizi.apss.tn.it/opendata/STATOPS001.json').json()
        ret = {"wait_times": {}}
        for d in hospitals:
            h = from_dict_to_hosp(d) 
            ret["wait_times"][h.code] = {}  
            if h.code == '001-PS-PSC' or h.code == '001-PS-PSG':
                ret["wait_times"][h.code]["white"] = predict_totg(model_totg, h, 'white')
                ret["wait_times"][h.code]["green"] = predict_totg(model_totg, h, 'green')
                ret["wait_times"][h.code]["blue"] = predict_totg(model_totg,h, 'blue')
                ret["wait_times"][h.code]["orange"] = predict_orange(model_orange, h) 
                ret["wait_times"][h.code]["red"] = '0'
            else:
                ret["wait_times"][h.code]["white"] = predict_wgb(model_wgb, h, 'white')
                ret["wait_times"][h.code]["green"] = predict_wgb(model_wgb, h, 'green')
                ret["wait_times"][h.code]["blue"] = predict_wgb(model_wgb, h, 'blue')
                ret["wait_times"][h.code]["orange"] = predict_orange(model_orange, h)
                ret["wait_times"][h.code]["red"] = '0'

        return ret


api.add_resource(Predictions, "/")

if __name__ == "__main__":
    
    dir_path = os.path.dirname(os.path.abspath(__file__))
    model_wgb = pickle.load(open(os.path.join(dir_path,'models','model_wgb.sav'), 'rb'))
    model_orange = pickle.load(open(os.path.join(dir_path,'models','model_orange.sav'), 'rb'))
    model_totg = pickle.load(open(os.path.join(dir_path,'models','model_totg.sav'), 'rb'))

    app.run(host='0.0.0.0')