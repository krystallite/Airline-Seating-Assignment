
# coding: utf-8

# In[ ]:

import sqlite3
import pandas as pd
import numpy as np

conn = sqlite3.connect('airline_seating.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table';") #inspect database for tables
print(c.fetchall())

def read_file(filename):
    df = pd.read_csv(filename, sep = ",", names = ["name", "grpsize"])
    psgnames = df.reset_index()['name'].values.astype(str).tolist()
    grpsize = df.reset_index()['grpsize'].values.astype(int).tolist()
    #print(psgnames)
    #print(grpsize)
    
read_file("bookings.csv")

# read rows_cols table from database for seating configuration
total_rows = c.execute("SELECT * FROM rows_cols;").fetchone()[0] # no. of rows in plane
seat_config = c.execute("SELECT * FROM rows_cols;").fetchone()[1] # seat configuration
seat_balance = total_rows*len(seat_config)

print("Total rows in this airplane: %d" %total_rows)
print("Seat configuration: %s" %seat_config)

# create dictionary of rows as keys and seat_config as values
num_row = [a for a in range(1,total_rows+1)]
d_seat = {r: seat_config for r in num_row}     #dictionary for seat_config balance in each row
d_num = {r: len(seat_config) for r in num_row} #dictionary for no. of seats balance in each row

# check seating file and create list of pre-booked seats 
c.execute("SELECT * FROM seating where name != '';")
pb_row = [] # list of rows taken
pb_seat = [] # corresponding seat_config taken
for item in c:
    #pre_booked.append(c)
    row, seat, psgname = item
    pb_row.append(row)
    pb_seat.append(seat)

seat_balance -= len(pb_row)
print("seat balance = %d" %seat_balance)

