from flask import Flask
from flask_restful import Api, Resource
from functions_lm import predict_rosso, predict_bianco, predict_verde, predict_arancio, predict_azzurro, get_data_by_code

import pickle

app = Flask(__name__)
api = Api(app)


def load_models():
    global model_bianco, model_verde, model_azzurro, model_arancio, model_rosso
    model_bianco = pickle.load(open('models/white', 'rb'))
    model_verde = pickle.load(open('models/green', 'rb'))
    model_azzurro = pickle.load(open('models/blue', 'rb'))
    model_arancio = pickle.load(open('models/orange', 'rb'))
    model_rosso = pickle.load(open('models/red', 'rb'))

codes = ["005-PS-PS", "014-PS-PS", "004-PS-PS", "010-PS-PS", "007-PS-PS","006-PS-PS","001-PS-PS",\
         "001-PS-PSP", "001-PS-PSO", "001-PS-PSG", "001-PS-PSC"]


class Predictions(Resource):
    def get(self):
        ret = {"wait_times": {}}
        for code in codes:
            data = get_data_by_code(code)
            ret["wait_times"][code] = {}
            ret["wait_times"][code]["bianco"] = predict_bianco(data, model_bianco)
            ret["wait_times"][code]["verde"] = predict_verde(data, model_verde)
            ret["wait_times"][code]["azzurro"] = predict_azzurro(data, model_azzurro)
            ret["wait_times"][code]["arancio"] = predict_arancio(data, model_arancio)
            ret["wait_times"][code]["rosso"] = predict_rosso(data, model_rosso)

        return ret



api.add_resource(Predictions, "/predict")

if __name__ == "__main__":
    load_models()
    print('Hello')
    app.run()