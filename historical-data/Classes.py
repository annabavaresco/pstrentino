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
     
      


