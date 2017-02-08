
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

# update dictionary removing pre-booked seats
for (row, seat) in zip(pb_row, pb_seat):
        num = list(d_seat.keys())[row-1]
        d_seat[num] = d_seat[num].replace(seat,"")
        d_num[row] -= 1

count_rej = 0
count_sep = 0

for (i,j) in zip(psgnames, grpsize):
    if seat_balance >= j: #booking can be accepted
        if max((d_num[x]) for x in d_num) >= j: #all members in booking can be seated together
            for k in range(1, total_rows+1):
                if len(d_seat[k]) >= j:
                    n = list(d_seat[k][:j])
                    for m in n:
                        c.execute("UPDATE seating SET name='%s' WHERE row=%d AND seat='%s';" %(i, k, m))
                    d_seat[k] = d_seat[k].replace(d_seat[k][:j],"")
                    d_num[k] -= j
                    seat_balance -= j
                    break
    elif j <= len(seat_config): #members in booking needs to be split
            count_sep += j
            c.execute("UPDATE metrics SET passengers_separated=%d;" %count_sep)
            print("Passengers are separated: %s, %d" %(i,j))
            for k in range(1, total_rows+1):
                if len(d_seat[k]) > 0:
                    y = j
                    while y != 0:
                        n = list(d_seat[k])
                        for m in n:
                            c.execute("UPDATE seating SET name='%s' WHERE row=%d AND seat='%s';" %(i, k, m))
                            y -= 1
                        d_seat[k] = d_seat[k].replace(d_seat[k][:j],"")
                        d_num[k] -= j
                        seat_balance -= j
                        break
    elif j > len(seat_config): #booking is more more than no. of seats in row and members in booking needs to be split
            count_sep += j
            c.execute("UPDATE metrics SET passengers_separated=%d;" %count_sep)
            print("Passengers are separated: %s, %d" %(i,j))
            y = j
            while y != 0:
                if y >= len(seat_config): #when unassigned booking is more than no. of seats in a row
                    for k in range(1, total_rows+1):
                        if len(d_seat[k]) == len(seat_config): #to assign booking to an empty row
                            n = list(d_seat[k][:len(seat_config)])
                            for m in n:
                                c.execute("UPDATE seating SET name='%s' WHERE row=%d AND seat='%s';" %(i, k, m))
                                y -= 1
                            d_seat[k] = d_seat[k].replace(d_seat[k][:len(seat_config)],"")
                            d_num[k] -= len(seat_config)
                            seat_balance -= len(seat_config)
                            break
                elif max((d_num[x]) for x in d_num) >= y: #if balance of unassigned booking is less than no. of seats in a row and no need to be split
                    for k in range(1, total_rows+1):
                        if len(d_seat[k]) >= y:
                            n = list(d_seat[k][:y])
                            for m in n:
                                c.execute("UPDATE seating SET name='%s' WHERE row=%d AND seat='%s';" %(i, k, m))
                                y -= 1
                                d_seat[k] = d_seat[k].replace(d_seat[k][:1],"")
                                d_num[k] -= 1
                                seat_balance -= 1
                            break
                elif j <= len(seat_config): #if unassigned booking is less than no. of seats in a row and needs to be split
                    for k in range(1, total_rows+1):
                        if len(d_seat[k]) > 0:
                            y = j
                            while y != 0:
                                n = list(d_seat[k])
                                for m in n:
                                    c.execute("UPDATE seating SET name='%s' WHERE row=%d AND seat='%s';" %(i, k, m))
                                    y -= 1
                                    d_seat[k] = d_seat[k].replace(d_seat[k][:1],"")
                                    d_num[k] -= 1
                                    seat_balance -= 1
                                break
