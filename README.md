# Predictions of Waiting Times in Trentino ERs
Developed by Anna Bavaresco, Sara Zuffi

Project for Big Data Technologies course at the University of Trento, academic year 2020/2021.
\
&nbsp;
Our paper *Waiting Times in Trentino ERs* is related to this repository.
This project aims at predicticting the waiting times by triage in the emergency rooms of Trentino hospitals.

## Table of content
* Overview
* Methods
* Main components

## Overview
&nbsp;
We developed a big data system that predicts Trentino emergency rooms' (ERs) waiting times in near-time. Data on hospital status has been collected from the Trentino Open Data portal.
[Here](http://ec2-35-177-232-103.eu-west-2.compute.amazonaws.com) it is possible to see the web app we created running on an Amazon EC2 instance.  

## Methods
&nbsp;
The project uses the following technologies:
* AWS
* MySQL
* Flask
* Redis
* Nginx
* uWSGI
* Docker

## Main components
&nbsp;
The architecture of our project is based upon two main blocks. The first one, developed inside the "historical data" directory, deals with data collection, data storage and building the predictive model. The second component, available in the "docker-compose" directory, is the one responsible for getting the last data available from the APSS (Azienda Provinciale per i Servizi Sanitari) API, computing the expected waiting times and serving them though a Flask application. 

### Historical data
&nbsp;
In order to develop a machine learning model able to predict waiting times, firstly it was necessary to collect some training data. The Python modules present inside the "historical data" folder serve precisely for this scope. 
The Trentino APSS API only contains information about the number of patients waiting or being treated at the moment of the call, divided by emergency room and triage level. However, the exact waiting time of each patient is NOT provided by the API and therefore needed to be computed. 
The best solution we could came up with in order to compute waiting times involves the following stages:
1. making a GET request to the APSS API;
2. converting the data of each emergency room into an instance of the class Hospital, which is defined in the Classes.py module;
3. temporarily storing the converted data inside the JSON file prev_hosp.json;
4. waiting 10 minutes, which is the timespan necessary to the APSS API to update data;
5. making another request to the APSS API and, again, converting the new data into instances of the Hospital class;
6. comparing, for each emergency room and each triage, the new data with the ones stored in prev_hosp.json. This is the crucial part of the computation and is perfomed by the function process_data_stream() defined in the Analyzers.py module. The main idea behind this complex function is the following: by comparing new data with the json stored ones, it is possible to understand if (a) one or mode new patients entered the waiting room, (b) one or more patients who were waiting left the queue because they are being visited or (c) nothing changed. If a new patient arrives, a new instance of the class patient (defined in the Classes.py module) is created and temporarily saved int the queues.json file. If a patient leaves the queue, he/she is removed from the queues.json file and saved in a database table along with its data. An extract of the table is available in the image below: 
7. ![image](https://user-images.githubusercontent.com/74197386/128709831-137c1b98-0865-4366-b752-ae0253507d42.png)


7. prev_hosp.json is updated with the current data;
8. repeat everything from step 1.

### Docker-compose
&nbsp;
The final result of our project is a Flask app displaying the expected waiting time for each triage color at the emergency room selected bu the user. In order to work effectively, the Flask application needs to interact with several other components and services, which are all integrated in the docker-compose.yaml file and listed below, along with a brief description. 

#### API
&nbsp;
This is the component where the actual Machine Learning happens. The easiest way to explain how it works is looking at the Dockerfile. After copying everything from the local folder to the Docker environment, the Dockerfile runs the module linear_models.py. This module retrieves the historical data by querying the Amazon-hosted database where it is stored, fits three linear models to it and finally saves them in the "models" directory. The same code we used in the linear_models.py module to develop the linear models is described in more depth, with appropriate explanations and annotations, inside the Colab Notebook "Emergency Room Trentino - Linear Models".
The second important module launched by the Dockerfile is api.py, which creates a Flask api collecting all the predictions for all the emergency rooms in a unique json file. More in detail, the module loads the linear models from the models folder, makes a GET request to the Trentino APSS API in order to obtain the most recent data about the number of patients waiting in the emergency rooms and passes it to the model, which then computes the predictions. 
All the predictions are saved in JSON format and become available whenever making a request to the localhost:5002 address. The functions.py module contains some auxiliary functions which are called by the api.py module and serves for data preparation and applying the predictive models to new data.   

#### App
&nbsp;
This component constitutes the main serving layer of our project. It consists of a Flask app which provides an interactive interface to the user, who can choose the emergency room for which he or she would like to know the expected waiting time. A screenshot of the graphical interface the user is presented with is available in the image below:
![image](https://user-images.githubusercontent.com/74197386/129215534-895819c5-b1a3-48b7-9984-64ae3dfaf28a.png)


Then, the Flask app sends a request to the previously described API in order to obtain the predictions and displays the ones relative to the emergency room selected by the user, integrating them in the result.html template. After the first API call, the predictions are saved for two minutes inside a Redis cache in order to make them more quickly accessible.   
As for the application deployment, we opted for a uWSGI server, with NGINX handling the http incoming requests.
Since the app directory is the one with the most complicated structure, it may be useful to give a closer look to its contents and their specific functions:
* static: this folder contains the styling sheet for the webpages and the image used as background
* templates: contains the html files rendered by the Flask app
* .env is the configuration file with all the variables necessary to set the redis cache
* config.py contains the Config() class used for cache configuration
* flask_app.py starts the app and the cache 
* uwsgi.ini defines the configuration for the uWSGI server
* wsgi.py is the module where the app defined inside flask_app.py runs and is going to be used to start the uWSGI server 

#### Redis
&nbsp;
The purpose of the Redis container is serving as a cache. As it is specified in the flask_app.py module, the cache timeout is 2 minutes.

#### NGINX
&nbsp;
It is used to route and handle the requests coming to port 80. 
