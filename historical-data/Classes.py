import mysql.connector
   
   
   
class Hospital:

    def __init__(self, code: str, waiting: dict(), managing: dict(), timestamp):
        
        self.code = code
        self.waiting = waiting
        self.managing = managing
        self.timestamp = timestamp

      
      
class Patient:
   
    def __init__(self, hospital, triage, others, more_severe, less_severe, t_start, previous = None):
        self.hospital = hospital
        self.triage = triage
        self.others = others
        self.more_severe = more_severe
        self.less_severe = less_severe
        self.t_start = t_start
        self.t_end = None
        self.waiting_time = 0
        self.previous = previous

      
      
class Queue: 
   
    def __init__(self, hospital_code):
        self.hospital_code = hospital_code
        self.head = None
        self.tail = None
        self.length = 0
    
    def add(self, patient: Patient):
        if self.length == 0:
            self.head = patient
            self.tail = patient
            self.length = 1
        elif self.length == 1: 
            self.tail = patient
            patient.previous = self.head
            self.length = 2
        else:
            patient.previous = self.tail
            self.tail = patient
            self.length += 1
    
    def remove(self, num: int, timestamp_end):
        if num > self.length:
            raise Exception('You are trying to remove more patients than the ones waiting!')
        if self.length == 0:
            raise Exception('Queue is empty: it is not possible to remove patients!')
        for i in range(num):
            p = self.tail
            p.t_end = timestamp_end

            p.waiting_time = p.t_end - p.t_start
            connection = mysql.connector.connect(
                host = 'emergencyroom.ci8zphg60wmc.us-east-2.rds.amazonaws.com',
                port =  3306,
                user = 'admin',
                database = 'er_trentino',
                password = 'emr00mtr3nt036'
                )

            connection.autocommit = True
            cursor = connection.cursor()

            query = "insert into er_patients_stream (triage, hospital, start, end, wait_time,\
                others, more_severe, less_severe)\
                    values (%s, %s, %s, %s, %s, %s, %s, %s)"

            cursor.execute(query, [p.triage, p.hospital, p.t_start, p.t_end, \
                        p.waiting_time, p.others, p.more_severe, p.less_severe])
            connection.close()
            
            if self.length == 1 :
                self.head = None
                self.tail = None
                self.length = 0
            elif self.length == 2:
                p.previous = None
                self.tail = self.head
                self.length -= 1
            else:
                self.tail = p.previous
                p.previous = None
                self.length -= 1

