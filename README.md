# Predictions of Waiting Times in Trentino ERs
Developed by Anna Bavaresco, Sara Zuffi

Project for Big Data Technologies course at the University of Trento, academic year 2020/2021.
\
&nbsp;
Our paper *Waiting Time Predictions in Trentino ERs* related to this repository is available XXX.
This project aims to predict waiting time in the emergency department of Trentino hospitals.

## Table of content
* Overview
* Methods
* Main components

### Overview
We develop a model that predicts Trentino emergency departments (ED) waiting times in near time. The data have been collected from the Trentino Open Data portal.

### Methods
The project uses the following technologies:
* MySQL
* Redis
* Flask
* Nginx
* Docker
* Github

### Main components
The architecture of our project is based upon two main blocks. The first one, developed inside the "historical data" directory, deals with data collection, data storage and building the predictive model. The second component, available in the "docker-compose" directory, is the one responsible for getting the last data available from the apss api, computing the expected waiting time and serving it though a flask application. 

#### Historical data
In order to develop a machine learning model able to predict waiting times, it was first necessary to have some training data. The python modules present inside the "historical data" folder serve precisely for this scope. 
The apss api only contains information about the number of patients waiting or being trated at the moment of the call, divided by emergency room and triage color. However, the exact waiting time of each patient is NOT provided by the api and therefore needs to be computed. 
The best solution we could came up with in order to compute waiting times involves the following stages:
1. making a get request to the apss api
2. converting the data on each emergency room into and instance of the class Hospital, which is defined in the Classes.py module
3. temporarily storing the converted data inside the json file prev_hosp.json
4. waiting 10 minutes, which is the timespan necessary to the apss api to get updated data
5. making another request to the apss api and, again, convertin the new data into instances of the Hospital class
6. comparing, for each emergency room and each triage, the new data with the ones stored in prev_hosp.json. This is the crucial part of the computation and is perfomed by the function process_data_stream() defined in the Analyzers.py module. The main idea behind this complex function is the following. By comparing new data with the json stored ones, it is possible to understand if (a) one or mode new patients entered the waiting room, (b) one or more patients who were waiting left the queue because they are being visited or (c) nothing changed. If a new patient arrives, a new instance of the class patient (defined in the Classes.py module) is created and temporarily saved int the queues.json file. If a patient leaves the queue, he or she is removed from the queues.json file and saved in a database table along with its data. An extract of the table is available in the image below. ![image](https://user-images.githubusercontent.com/74197386/128709831-137c1b98-0865-4366-b752-ae0253507d42.png)


7. prev_hosp.json is updated with the current data.
8. Repeat everything from step 1.

#### Docker-compose
The final result of our project is a Flask app displaying the expected waiting time for each triage color at the emergency room selected bu the user. In order to work effectively, the Flask application needs to interact with several other components and services, which are all integrated in the docker-compose.yaml file and listed below, along with a brief description. 

##### Models api
This component is built upon a tensorflow/serving image and has the purpose of serving the three Neural Network we implemented in order to predict waiting times. The Dockerfile for this image is present inside the models_api directory, together with the models themselves and a configuration file listing all of the models and their path. 

##### Api
It is a Flask api which has the purpose of collecting the most recent data from the Trentino apss api, passing them to the right model-api in order to obtain the waiting time prediction and displaying all the predictions together for every triage color and every emergency room in a clean and tidy way inside a unique json file. The api directory contains the Dockerfile for this component, the api.py module where the Flask api is defined and the functions.py module which collects the auxiliary functions used to compute predictions for the new data.     

##### App
This component constitutes the serving layer of our project. It mainly consists of a Flask app which provides an interactive interface to the user, who can choose the emergency room for which he or she would like to know the expected waiting time. A screenshot of the graphical interface the user is presented with is available in the image below.
![image](https://user-images.githubusercontent.com/74197386/128715677-8e980d76-0cc0-4d3f-a239-b8dbf12333a3.png)

The Flask app then sends a request to the previously described api in order to obtain the precictions and diplays the ones relative to the emergency room selected by the user by integrating them in the result.html template. After the first api call, the predictions are going to be saved for two minutes inside a redis cache (which will de bescribed in the next section) in order to make them quickly-accessible.   
As for the application deployment, we opted for a uwsgi server, with nginx handling the http incoming requests.
Since the app directory is the one with the most complicated structure, it may be useful to give a closer look to its contents and their specific functions:
* static: this folder contains the styling sheet for the webpages and the image used as background
* templates: contains the html files rendered by the Flask app
* .env is the configuration file with all the variables necessary to set the redis cache
* config.py contains the Config() class used for cache configuration
* flask_app.py starts the app and the cache 
* uwsgi.ini defines the configuration for the uwsgi server
* wsgi.py is the module where the app defined inside flask_app.py runs and is going to be used to start the uwsgi server 

##### Redis

##### Nginx
It is used to route and handle the requests coming to the 80 port. 
