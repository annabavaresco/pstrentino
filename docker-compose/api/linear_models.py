import pandas as pd
pd.options.mode.chained_assignment = None
import datetime as dt
import numpy as np
import random
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from datetime import datetime
import mysql.connector
import pickle
import os 

dir_path = os.path.dirname(os.path.abspath(__file__))


def get_data():
  '''
    Creates a connection with the db hosting our data and converts it into a Pandas dataframe.
  '''
  connection = mysql.connector.connect(
      host = 'emergencyroom.ci8zphg60wmc.us-east-2.rds.amazonaws.com',
      port =  3306,
      user = 'admin',
      database = 'er_trentino',
      password = 'emr00mtr3nt036'
    )

  connection.autocommit = True
  data = pd.read_sql('SELECT * FROM er_trentino.patients', con=connection)

  connection.close()

  return data

df = get_data()
df = df.dropna()

def convert_to_mins(last: str):
    '''
        Converts a string in the format hh:mm:ss into an integer representing the number of minutes.
    '''
    l = last.split(':')
    l = [int(s) for s in l[:2]]
    mins = l[1]
    if l[0] != 0:
        hrs = l[0] * 60
        mins += hrs 
        
    return mins

def process_df(data_frame):
    '''
      Takes as input the data retrieved from the database and outputs 5 different datasets with processed data.
    '''
    data = data_frame.copy()

    hosp_dict = {'001-PS-PSC': 10,
                '001-PS-PSG': 11,
                    '001-PS-PSO': 1,
                    '001-PS-PS': 2,
                    '001-PS-PSP': 3,
                    '006-PS-PS': 4,
                    '007-PS-PS': 5,
                    '010-PS-PS': 6,
                    '004-PS-PS': 7,
                    '014-PS-PS': 8,
                    '005-PS-PS': 9
                }
    
    data['hosp_code'] = data['hospital'].apply(lambda x: hosp_dict[x])
    data['weekday'] = data['start'].apply(lambda x: x.weekday())
    data['waiting_time'] = data['waiting_time'].apply(lambda x: convert_to_mins(str(x)))
    timeslot_dict = {}
    ind = 1
    for n in range(24):
        if n < 10:
            hrs =  '0' + str(n) 
        else:
            hrs = str(n)

        for i in range(6):
            mins = str(i) + '0'
            s = hrs + ':' + mins + ':' + '00'
            timeslot_dict[s] = ind
            ind += 1

    data['timeslot'] = data['start'].apply(lambda x: timeslot_dict[x.strftime("%H:%M:%S")])
    data = data.loc[:,['triage', 'waiting_time', 'others', 'more_severe', 'hosp_code', 'weekday', 'timeslot']]
    ndf1 = data.loc[(data['hosp_code']==11) | (data['hosp_code']==10), :]
    data = data.loc[(data['hosp_code']!=11) & (data['hosp_code']!=10), :]
    data['hosp_code'] = data['hosp_code']
    ndf_white = data.loc[data['triage'] == "white",:]
    ndf_green = data.loc[data['triage'] == "green",:]
    ndf_blue = data.loc[data['triage'] == "blue",:]
    ndf_orange = data.loc[data['triage'] == "orange",:]
    ndf_red = data.loc[data['triage'] == "red",:]
    
    return ndf1, ndf_white, ndf_green, ndf_blue, ndf_orange, ndf_red

process_df(df)[0]


dtf1, white, green, blue, orange, red = process_df(df)

#-----------------------------------------------------------------------------------------

# White, green and blue model

df_list = [white, green, blue]

for dataframe in df_list:

  #this preprocessing step is done in order to deal with potential outliers
    upper_lim = dataframe.loc[:, 'waiting_time'].quantile(0.99)
    dataframe.loc[dataframe['waiting_time']>upper_lim, 'waiting_time'] = round(upper_lim)
    

dataset = pd.concat([white, green, blue]) 

# turning the triage variable into numeric factors
d= {'white': 1, 'green': 2, 'blue': 3}
dataset['triage'] = dataset['triage'].apply(lambda x: d[x])

dataset.head()

X = dataset.loc[:,['triage','hosp_code', 'others', 'more_severe', 'weekday', 'timeslot']]
y = dataset['waiting_time']


trainX, testX, trainy, testy = train_test_split(X, y, test_size=0.1, random_state=0)
regressor_wgb = LinearRegression().fit(trainX, trainy)


pickle.dump(regressor_wgb, open(os.path.join(dir_path,'models','model_wgb.sav'), 'wb'))

#-----------------------------------------------------------------
## Orange model


dataset = orange
upper_lim = dataset.loc[:, 'waiting_time'].quantile(0.99)
dataset.loc[dataset['waiting_time']>upper_lim, 'waiting_time'] = round(upper_lim)
dataset.head()

X = dataset.loc[:,['others', 'weekday']]
y = dataset['waiting_time']


trainX, testX, trainy, testy = train_test_split(X, y, test_size=0.1, random_state=0)

regressor_orange = LinearRegression().fit(trainX, trainy)

pickle.dump(regressor_orange, open(os.path.join(dir_path,'models','model_orange.sav'), 'wb'))


#-----------------------------------------------------------------
## Trento-oculistico and Trento-ginecologico

dataset = dtf1

dataset = dataset.loc[(dataset['triage']!= 'orange')&(dataset['triage']!= 'red'),:]
coldict = {'white':1, 'green':2, 'blue':3}
dataset['triage'] = dataset['triage'].apply(lambda x: coldict[x])
for i in range(1,4):
    upper_lim = dataset.loc[dataset['triage']==i, 'waiting_time'].quantile(0.9)
    dataset.loc[(dataset['triage']==i)&(dataset['waiting_time']>upper_lim), 'waiting_time'] = upper_lim

dataset.head()

X = dataset.loc[:,['triage', 'others', 'more_severe', 'weekday']]
y = dataset['waiting_time']


trainX, testX, trainy, testy = train_test_split(X, y, test_size=0.1, random_state=0)

regressor_totg = LinearRegression().fit(trainX, trainy)

pickle.dump(regressor_totg, open(os.path.join(dir_path,'models','model_totg.sav'), 'wb'))