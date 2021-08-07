from functions import from_dict_to_hosp
from flask import Flask
import requests
from flask_restful import Api, Resource
from functions import predict_orange, predict_wgb, predict_totg

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
                ret["wait_times"][h.code]["white"] = predict_totg(h, 'white')
                ret["wait_times"][h.code]["green"] = predict_totg(h, 'green')
                ret["wait_times"][h.code]["blue"] = predict_totg(h, 'blue')
                ret["wait_times"][h.code]["orange"] = predict_orange(h) 
                ret["wait_times"][h.code]["red"] = '0'
            else:
                ret["wait_times"][h.code]["white"] = predict_wgb(h, 'white')
                ret["wait_times"][h.code]["green"] = predict_wgb(h, 'green')
                ret["wait_times"][h.code]["blue"] = predict_wgb(h, 'blue')
                ret["wait_times"][h.code]["orange"] = predict_orange(h)
                ret["wait_times"][h.code]["red"] = '0'

        return ret


api.add_resource(Predictions, "/")

if __name__ == "__main__":
    app.run(host='0.0.0.0')