from functions import from_dict_to_hosp
from flask import Flask
import requests
from flask_restful import Api, Resource
from functions import predict_white, predict_green, predict_blue, predict_orange, predict_red
#from gevent import WSGIServer

app = Flask(__name__)
api = Api(app)


codes = ["005-PS-PS", "014-PS-PS", "004-PS-PS", "010-PS-PS", "007-PS-PS","006-PS-PS","001-PS-PS",\
         "001-PS-PSP", "001-PS-PSO", "001-PS-PSG", "001-PS-PSC"]


class Predictions(Resource):
    def get(self):
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
    
    # wsgi_server = WSGIServer(('0.0.0.0', 5000), app)
    # wsgi_server.serve_forever()
    app.run(host='0.0.0.0')