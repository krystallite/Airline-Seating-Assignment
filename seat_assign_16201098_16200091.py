# Analytics Research and Implementation - Programming Assignment
# Ezra Priya (16200091) and Yinxiu Chen (16201098)

import sqlite3
import pandas as pd
import numpy as np
import sys

airline_database = sys.argv[1]                                         # read the first argument in command line as the db file
bookings = sys.argv[2]                                                 # read the second argument in command line as booking file

conn = sqlite3.connect(airline_database)                               # connect to sqlite
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table';")        # inspect database structure for tables inside it

def read_file(filename):                                               # function to import bookings.csv file and split into booking name and total passengers
    df = pd.read_csv(filename, sep = ",", names = ["name", "grpsize"])
    psgnames = df.reset_index()['name'].values.astype(str).tolist()    # list of passenger names
    grpsize = df.reset_index()['grpsize'].values.astype(int).tolist()  # corresponding list of group size
    
    return psgnames, grpsize
    

def read_db():                                                         # read rows_cols table from database for seating configuration
    total_rows = c.execute("SELECT * FROM rows_cols;").fetchone()[0]   # no. of rows in plane
    seat_config = c.execute("SELECT * FROM rows_cols;").fetchone()[1]  # seat configuration
    seat_balance = total_rows*len(seat_config)                         # setting the amount of available seats based on the seat configuration of aircraft

    # create 2 dictionaries of rows as keys and seat_config as values
    # the dictionaries indicate the assignment of passengers to the seating
    num_row = [a for a in range(1,total_rows+1)]                       # list for number of rows in seating configuration
    d_seat = {r: seat_config for r in num_row}                         # dictionary for seat_config balance in each row
    d_num = {r: len(seat_config) for r in num_row}                     # dictionary for no. of seats balance in each row
    
    # check seating file and create list of pre-booked seats        
    c.execute("SELECT * FROM seating where name != '';")
    pb_row = []                                                        # list of rows taken
    pb_seat = []                                                       # corresponding seat_config taken
    for item in c:                                                     # gathering the names and seats of pre-booked passengers to the list
        row, seat, psgname = item
        pb_row.append(row)
        pb_seat.append(seat)

    seat_balance -= len(pb_row)                                        # substracting the number of pre-booked seats from the remaining available seats

    # update dictionary removing pre-booked seats
    for (row, seat) in zip(pb_row, pb_seat):
        num = list(d_seat.keys())[row-1]
        d_seat[num] = d_seat[num].replace(seat,"")
        d_num[row] -= 1
    
    return total_rows, seat_config, seat_balance, num_row, d_seat, d_num

# main function of the seat assignment
def seat_assign(bookings):
    psgnames, grpsize = read_file(bookings)                             # run read_file function to read csv file
    total_rows, seat_config, seat_balance, num_row, d_seat, d_num = read_db()
    count_rej = 0                                                       # counter to count how many passengers have been refused outright
    count_sep = 0                                                       # counter to count how many passengers are seated away from any o/r member of their party
    for (i,j) in zip(psgnames, grpsize):                                # going through each booking in the booking list
        
        # SCENARIO A: We can accommodate the booking because there are still enough seats in the airplane
        #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
        if seat_balance >= j:                                           # if there are still enough available seats for the group in the booking
            
            # SCENARIO A 1: All passengers within the booking can be seated without splitting them apart
            #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
            if max((d_num[x]) for x in d_num) >= j:                     # checking all rows and compare if any rows can accommodate all members in booking still can be seated together in one row
                for k in range(1, total_rows+1):                        # going through all rows to accommodate all members for this particular booking
                    if len(d_seat[k]) >= j:                             # if it finds an available row for this booking
                        n = list(d_seat[k][:j])                         # breaking down the seats in the available row for this booking
                        for m in n:                                     # we want to assign each empty seat in this row k
                            c.execute("UPDATE seating SET name='%s' WHERE row=%d AND seat='%s';" %(i, k, m)) # assign 1 person to this seat and update database
                        d_seat[k] = d_seat[k].replace(d_seat[k][:j],"") # update the alphabetic dictionary after assigning a seat to a group of booking
                        d_num[k] -= j                                   # update the numerical dictionary after assigning a seat to a group of booking
                        seat_balance -= j                               # substract the remaining available seats after assigning seats to this group of booking
                        break
            
            # SCENARIO A 2: There booking can be accommodated but some members in booking needs to be seated apart
            #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
            elif j <= len(seat_config):                                 # check that the total number of passengers in the booking is still within maximum seats in a row 
                count_sep += j                                          # update counter for separated passengers
                c.execute("UPDATE metrics SET passengers_separated=%d;" %count_sep) # update database for metrics of separated passengers
                print("Passengers are separated: %s, %d" %(i,j))
                for k in range(1, total_rows+1):                        # checking each row for empty seats
                    if len(d_seat[k]) > 0:                              # if empty seats in a row is found
                        y = j                                           # counter for the number of passengers in the booking that have not been allocated seats 
                        while y != 0:                                   # while there is still a passenger in the booking who has not been allocated a seat 
                            n = list(d_seat[k])                         # break down the seats in the available row for this booking
                            for m in n:                                 # we want to assign each empty seat in this row k
                                c.execute("UPDATE seating SET name='%s' WHERE row=%d AND seat='%s';" %(i, k, m)) # assign 1 person to this seat and update database
                                y -= 1                                  # reduce the number of passengers in the booking who have not been allocated seats 
                            d_seat[k] = d_seat[k].replace(d_seat[k][:j],"") # update alphabetical dictionary for seat that has just been taken
                            d_num[k] -= j                               # update numerical dictionary for taken seat
                            seat_balance -= j                           # reduce number of remaining available seats by the number of passengers in the booking
                            break
            
            # SCENARIO A 3: This is for a large booking. There are available seats in the airplane but certainly passengers must be split apart
            # In this scenario, we try to accommodate members in the booking to be seated together whenever possible
            # However, when there is no more empty row, remaining passengers will be seated to any available rows
            #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
            elif j > len(seat_config):                                  # check if booking is more than no. of seats in row
                count_sep += j                                          # update counter for separated passengers by the total passengers in the booking
                c.execute("UPDATE metrics SET passengers_separated=%d;" %count_sep) # update database
                print("Passengers are separated: %s, %d" %(i,j))
                # From this point, the same principle is used as applied for Scenario 1B: finding available seats in each row to assign each passenger in the large booking
                y = j
                while y != 0:
                    if y >= len(seat_config):                           # when unassigned booking is more than no. of seats in a row
                        for k in range(1, total_rows+1):
                            if len(d_seat[k]) == len(seat_config):      # If there is a row that can accommodate the remaining members of the group, they will be seated together
                                n = list(d_seat[k][:len(seat_config)])  # break down available seats in the row. For example, if 3A is taken, then this will contain [C, D, F]
                                for m in n:
                                    c.execute("UPDATE seating SET name='%s' WHERE row=%d AND seat='%s';" %(i, k, m))
                                    y -= 1
                                d_seat[k] = d_seat[k].replace(d_seat[k][:len(seat_config)],"")
                                d_num[k] -= len(seat_config)
                                seat_balance -= len(seat_config)
                                break
                    elif max((d_num[x]) for x in d_num) >= y:           # Finding if there are still empty rows (max available seats in all rows) that can accommodate the remaining members to be seated together
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
                    elif j <= len(seat_config):                         # find any seat for the remaining members of the group that have not been allocated seats
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
        
        # SCENARIO B: The airplane is full and hence the next booking will be rejected
        #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
        else:
            count_rej += j                                             # counter to update database for the number of rejected passengers 
            c.execute("UPDATE metrics SET passengers_refused=%d;" %count_rej)       
            print("Passenger is rejected: %s" %i)
    return 

seat_assign(bookings)

conn.commit()                                                           # update db file with all the UPDATEs we have done so far
conn.close()                                                            # Close connection to sqlite
