# Seat Assignment


To run the python script, do the following:

1. Open up command prompt

2. At the command line, key in python seat_assign_16201098_16200091.py data.db bookings.csv, 
    where data.db is the name of an SQLite database and bookings.csv is a file representing the bookings, one per line

This python script has been written to carry out the following before assigning seats to passengers in the booking.csv file:

1. read user command and input as above
2. connect to the data.db file via sqlite3
3. read a csv file which contains a list of passenger names and their groupsize and convert the data into two lists
4. read the data.db file to check configuration of plane and check for occupied seats
5. two dictionaries are created to keep count of the seats assigned and the number of available seats in each row
6. three counters are also created to count the number of total available seats left (seat_balance), number of passengers refused outright (count_rej) and number of passengers seated away from any other member of their party (count_sep)


Assumptions made:

1. As long as passengers are allocated seats in the same row, next to one another consecutively as given in the seating configuration, any  aisle between seats are ignored. For example, if the seating congifuration of a plane is ACDF with an aisle between seats C and D, and a booking of size three are assigned seats 2C, 2D and 2F, they are considered to be seated together and not separated.

2. Seat assignment is carried out on a left to right basis, regardless of when booking is made, including prebooked seats. Hence, with seating configuration of ACDF, in any row, seats will be assigned in the order A, C, D and F. Seats will not be assigned if the preceding seat has not been assigned. For example, for a booking of party size 1, seat C will not be assigned if seat A is available, seat A will be assigned instead of C.


The following steps will run to assign seats until all bookings in the csv file has been considered:

Step 0

Read the first item in the two lists containing data from the csv file.

Step 1

If seat_balance is more than the party size, booking can be accepted (Scenario A). Proceed to Step 2. Else, proceed to Step 7.

Step 2 

Check if the maximum available seats in each row can accommodate the booking. If yes, proceed to Step 3. Else, proceed to Step  4.

Step 3 (Scenario A1 - small party size and memebers can be seated together) 

Assign seats to the row that can accommodate all members in the party together. Update dictionaries, counter seat_balance and seating table in database. Proceed to Step 8.

Step 4 

Check if the party size is less than or equal to the maximum number of seats in a row in the plane configuration. If yes, proceed to Step 5. If no, proceed to Step 6.

Step 5 (Scenario A2 - small party size but members need to be split up)

Members in the party need to be split up. Update counter count_sep and metrics table in database. Find next available seats and assign seats. Update dictionaries, counter seat_balance and seating table in database. Proceed to Step 8.

Step 6 (Scenario A3 - large party size and members need to be split up)

Party size is bigger than the maximum number of seats in a row. Update counter count_sep and metrics table in database. Seats are assigned by checking for entirely empty rows first. If empty rows are filled and not all party members are assigned a seat, then we check for the next available seat from the first row. Update dictionaries, counter seat_balance and seating table in database. Proceed to Step 8.

Step 7 (Scenario B - booking cannot be accepted)

Booking cannot be accepted as number of available seats is less than party size. Update counter count_rej and metrics table in database. Proceed to Step 8.

Step 8

Retrieve next booking and return to Step 1.

End of README file.
