from Classes import *
from Functions import process_data_stream
import time

while True:
    process_data_stream()
    time.sleep(60)