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
6. comparing, for each emergency room and each triage, the new data with the ones stored in prev_hosp.json. This is the crucial part of the computation and is perfomed by the function process_data_stream() defined in the Analyzers.py module. The main idea behind this complex funxtion is the following. By comparing new data with the json stored ones, it is possible to understand if (a) one or mode new patients entered the waiting room, (b) one or more patients which were waiting left the queue because they are being visited or (c) nothing changed. 
