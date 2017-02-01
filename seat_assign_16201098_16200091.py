
# coding: utf-8

# In[ ]:

import sqlite3
import pandas as pd
import numpy as np

conn = sqlite3.connect('airline_seating.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table';") #inspect database for tables
print(c.fetchall())

