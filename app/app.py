from flask import Flask, render_template, url_for, request, redirect
import requests
import json
from flask_caching import Cache

app = Flask(__name__, static_folder='static/css')
app.static_folder = 'static'
app.config.from_object('config.Config')  # Set the configuration variables to the flask application
cache = Cache(app)

@app.route('/')

def index():
    return render_template('index.html')

@cache.cached(timeout=60, query_string=True)
def get_prediction():
        req = requests.get('http://api:5000').json()
        return req

@app.route('/result', methods=['POST'])

def show_prediction():
    if request.method == 'POST':
        ospedale = request.form['ps']
        hosp_dict = {
            "005-PS-PS": 'Cles',
            "014-PS-PS": 'Cavalese',
            "004-PS-PS": 'Borgo Valsugana',
            "010-PS-PS": 'Arco',
            "007-PS-PS": 'Tione',
            "006-PS-PS": 'Rovereto',
            "001-PS-PS": 'Trento',
            "001-PS-PSP": 'Trento-pediatrico',
            "001-PS-PSO": 'Trento-ortopedico',
            "001-PS-PSG": 'Trento-ginecologico',
            "001-PS-PSC": 'Trento-oculistico'
        }

        pred = get_prediction()

        return render_template('result.html', ospedale=hosp_dict[ospedale], \
                               tempo_bianco=pred['wait_times'][ospedale]['white'], \
                               tempo_verde=pred['wait_times'][ospedale]['green'], \
                               tempo_azzurro=pred['wait_times'][ospedale]['blue'], \
                               tempo_arancio=pred['wait_times'][ospedale]['orange'],\
                               tempo_rosso=pred['wait_times'][ospedale]['red'])


@app.route('/back', methods=['POST'])
def back():
    if request.method == 'POST':
        return render_template('base.html')


if __name__ == '__main__':

    app.run(host='0.0.0.0')

