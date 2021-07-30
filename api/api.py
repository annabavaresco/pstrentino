from functions import from_dict_to_hosp
from flask import Flask
import requests
from flask_restful import Api, Resource
from functions import predict_white, predict_green, predict_blue, predict_orange, predict_red

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
            ret["wait_times"][h.code]["white"] = predict_white(h)
            ret["wait_times"][h.code]["green"] = predict_green(h)
            ret["wait_times"][h.code]["blue"] = predict_blue(h)
            ret["wait_times"][h.code]["orange"] = predict_orange(h)
            ret["wait_times"][h.code]["red"] = predict_red(h)

        return ret


api.add_resource(Predictions, "/")

if __name__ == "__main__":
    app.run(host='0.0.0.0')