# Samson Nguyen, Anh Duy Tran, Mohammad Abdellatif
# 5/7/2021

# Project 2 Part 3 Task 2

import mysql.connector

# Connection to localhost mysql db
mydb = mysql.connector.connect(
    host="localhost",
    user="Sam",
    password="@Sammysamsam79",
    database="mydb"
)

cursor = mydb.cursor()


def add_customer(name, phone):
    # Insert row into customer table, not including CustID value which will auto-increment
    sql = "INSERT INTO Customer (Name, Phone) VALUES (%s, %s)"
    val = name, phone
    cursor.execute(sql, val)
    mydb.commit()


def add_vehicle(vin, description, year, type, category):
    # Insert row into vehicle table with vin, description, year, type, and category values
    sql = "INSERT INTO Vehicle VALUES (%s, %s, %s, %s, %s)"
    val = vin, description, year, type, category
    cursor.execute(sql, val)
    mydb.commit()


def add_rental(custID, v_type, v_category, start_date, order_date, rental_type, qty, return_date, payment_date=None):
    # Try to find a vehicle with the appropriate type and category which is available at the req time
    cursor.execute(
        """SELECT 
        *
    FROM
        Rental AS R
            RIGHT JOIN
        Vehicle AS V ON R.VehicleID = V.VehicleID
    WHERE
        Type = %s AND Category = %s
            AND (StartDate > CAST('%s' AS DATE)
            OR ReturnDate < CAST('%s' AS DATE)
            OR R.VehicleID IS NULL);""" % (v_type, v_category, return_date, start_date))
    result = cursor.fetchall()
    if len(result) == 0:
        print("No such vehicle found.")
        return
    else:
        # get rate from rate table with type and category
        cursor.execute("SELECT * FROM Rate WHERE Type = %s AND Category = %s" % (v_type, v_category))
        result1 = cursor.fetchall()
        rate = result1[0][2 if rental_type == 7 else 3]
        vehicle_ID = result[0][1]
        if payment_date is None:
            sql = "INSERT INTO Rental VALUES (%s, '%s', CAST('%s' AS DATE), CAST('%s' AS DATE), %s, %s, CAST('%s' AS DATE), %s, NULL, 0)"
            val = custID, vehicle_ID, start_date, order_date, rental_type, qty, return_date, str(int(rate) * int(qty))
        else:
            # Insert rental row with payment date
            sql = "INSERT INTO Rental VALUES (%s, '%s', CAST('%s' AS DATE), CAST('%s' AS DATE), %s, %s, CAST('%s' AS DATE), %s, CAST('%s' AS DATE), 1)"
            val = custID, vehicle_ID, start_date, order_date, rental_type, qty, return_date, str(
                int(rate) * int(qty)), payment_date
        sql = sql % val
        cursor.execute(sql)
        mydb.commit()


def return_rental(return_date, customer_name, v_desc):
    # get custID with name
    cursor.execute("SELECT CustID FROM Customer WHERE Customer.Name = '%s'" % customer_name)
    custID = cursor.fetchall()[0][0]
    # get vehicleID with description
    cursor.execute("SELECT VehicleID FROM Vehicle WHERE Description = '%s'" % v_desc)
    vehicleID = cursor.fetchall()[0][0]
    # get total amount due for rental with above custID and vehicleID
    cursor.execute("SELECT TotalAmount from Rental WHERE custID = '%s' AND VehicleID = '%s' AND ReturnDate = '%s'" % (
        custID, vehicleID, return_date))
    total_amount = cursor.fetchall()[0][0]
    print("Total customer payment due for this rental: %d" % total_amount)
    # update rental row with payment date and returned status
    cursor.execute("UPDATE Rental SET PaymentDate = CAST('%s' AS DATE), Returned = 1" % return_date)
    mydb.commit()


def view_customer(custID=None, customer_name=None):
    if custID is None:
        if customer_name is None:
            # list customers without filters
            cursor.execute(
                "SELECT CustID, Name, SUM(CASE WHEN Returned = 0 THEN TotalAmount ELSE 0 END) AS Balance FROM Customer NATURAL LEFT OUTER JOIN Rental GROUP BY CustID ORDER BY Balance DESC")
        else:
            # list customers filtered by name
            cursor.execute(
                "SELECT CustID, Name, SUM(CASE WHEN Returned = 0 THEN TotalAmount ELSE 0 END) AS Balance FROM Customer NATURAL LEFT OUTER JOIN Rental WHERE Name LIKE '%" + customer_name + "%' GROUP BY CustID")
    else:
        if customer_name is None:
            # list customers filtered by custID
            cursor.execute(
                "SELECT CustID, Name, SUM(CASE WHEN Returned = 0 THEN TotalAmount ELSE 0 END) AS Balance FROM Customer NATURAL LEFT OUTER JOIN Rental WHERE CustID='%s' GROUP BY CustID" % custID)
        else:
            # list customers filtered by both custID and name
            cursor.execute(
                "SELECT CustID, Name, SUM(CASE WHEN Returned = 0 THEN TotalAmount ELSE 0 END) AS Balance FROM Customer NATURAL LEFT OUTER JOIN Rental WHERE Name LIKE '%" + customer_name + "%'" + " AND CustID='" + str(
                    custID) + "' GROUP BY CustID")
    results = cursor.fetchall()
    if len(results) == 0:
        print("No such customer found.")
    else:
        print("CustomerID |   CustomerName   | Remaining Balance")
        print("-----------|------------------|------------------")
        for l in results:
            if l[2] != None:
                txt = "{cid:>10d} | {name:>16s} | ${balance:.2f}"
                print(txt.format(cid=l[0], name=l[1], balance=float(l[2])))
            else:
                print("%10d | %16s | $0.00" % (l[0], l[1]))
    print("{} rows returned.".format(len(results)))


def view_vehicle(VIN=None, description=None):
    if VIN is None:
        if description is None:
            # list vehicles with no filer
            cursor.execute(
                "SELECT VehicleID AS VIN, Description, AVG(TotalAmount / (RentalType * Qty)) AS ADP FROM vehicle NATURAL LEFT OUTER JOIN Rental GROUP BY VehicleID ORDER BY ADP DESC")
        else:
            # list vehicles filtered by description
            cursor.execute(
                "SELECT VehicleID AS VIN, Description, AVG(TotalAmount / (RentalType * Qty)) AS ADP FROM vehicle NATURAL LEFT OUTER JOIN Rental WHERE Description LIKE '%" + description + "%' GROUP BY VIN")
    else:
        if description is None:
            # list vehicles filtered by VIN
            cursor.execute(
                "SELECT VehicleID AS VIN, Description, AVG(TotalAmount / (RentalType * Qty)) AS ADP FROM vehicle NATURAL LEFT OUTER JOIN Rental WHERE VehicleID='%s'" % VIN)
        else:
            # list vehicles filtered by VIN and description
            cursor.execute(
                "SELECT VehicleID AS VIN, Description, AVG(TotalAmount / (RentalType * Qty)) AS ADP FROM vehicle NATURAL LEFT OUTER JOIN Rental WHERE Description LIKE '%" + description + "%' AND VehicleID='" + VIN + "'")
    results = cursor.fetchall()
    if len(results) == 0:
        print("No such vehicle found.")
    else:
        print("         VIN        |       Description      | Average DAILY Price")
        print("--------------------|------------------------|--------------------")
        for l in results:
            if l[2] != None:
                txt = "{vin:>19s} | {desc:>22s} | ${balance:.2f}"
                print(txt.format(vin=l[0], desc=l[1], balance=float(l[2])))
            else:
                print("%19s | %22s | Non-Applicable" % (l[0], l[1]))
    print("{} rows returned.".format(len(results)))


help_str = """Commands:
add_customer|<Name>|<Phone>
    Adds a customer to the database with auto-incremented CustID.
add_vehicle|<VIN>|<Description>|<Year>|<Type>|<Category>
    Adds a vehicle to the database with all above info.
add_rental|<CustID>|<VehicleType>|<VehicleCategory>|<StartDate>|<OrderDate>|<RentalType>|<Qty>|<ReturnDate>|[PaymentDate]
    Adds a rental to the database with all above info.
    PaymentDate is optional for the case when it is paid on the same date as ordered.
return_rental|<ReturnDate>|<CustomerName>|<VehicleDescription>
    Handles a return.
    The relevant row in the Rental table is updated with a payment date and Returned is set to 1.
view_customer|[ID=CustID]|[Name=CustomerName]
    Views a list of customers by CustID, Name, and Remaining Balance.
    With no filter, lists all customers.
    With ID=<CustID>, lists only customer with that ID.
    With Name=<CustomerName>, lists customers with names like CustomerName.
view_vehicle|[VIN=VIN]|[desc=description]
    Views a list of vehicles by VIN, Description, and Average DAILY Price.
    With no filter, lists all vehicles.
    With VIN=<VIN>, lists only the vehicle with that VIN.
    With desc=<description>, lists vehicles with descriptions like description.
help
    Prints this string.
quit
    Quits the program."""
print(help_str)
while True:
    command = input("Command: ")
    args = command.split("|")
    if args[0] == "quit":
        break
    elif args[0] == "help":
        print(help_str)
    elif args[0] == "add_customer":
        add_customer(args[1], args[2])
    elif args[0] == "add_vehicle":
        add_vehicle(args[1], args[2], int(args[3]), int(args[4]), int(args[5]))
    elif args[0] == "add_rental":
        if len(args) >= 10:
            add_rental(args[1], args[2], args[3], args[4], args[5], args[6], args[7], args[8], payment_date=args[9])
        else:
            add_rental(args[1], args[2], args[3], args[4], args[5], args[6], args[7], args[8])
    elif args[0] == "return_rental":
        return_rental(args[1], args[2], args[3])
    elif args[0] == "view_customer":
        if "ID=" in command:
            if "Name=" in command:
                view_customer(int(args[1].split('=')[1]), args[2].split('=')[1])
            else:
                view_customer(int(args[1].split('=')[1]))
        else:
            if "Name=" in command:
                view_customer(None, args[1].split('=')[1])
            else:
                view_customer()
    elif args[0] == "view_vehicle":
        if "VIN=" in command:
            if "desc=" in command:
                view_vehicle(args[1].split('=')[1], args[2].split('=')[1])
            else:
                view_vehicle(args[1].split('=')[1])
        else:
            if "desc=" in command:
                view_vehicle(None, args[1].split('=')[1])
            else:
                view_vehicle()
