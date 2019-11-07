#!/usr/bin/python

import MySQLdb
import ConfigParser
import subprocess
import argparse
import os.path
import getopt
import sys
from prettytable import PrettyTable

Config = ConfigParser.ConfigParser()
Config.read("/root/.my.cnf")
dbHost = Config.get('mysql', 'host')
dbUser = Config.get('mysql', 'user')
dbPassword = Config.get('mysql', 'password')

# get a connection to DB
db = MySQLdb.connect(dbHost, dbUser, dbPassword, "cloud")
cursor = db.cursor()

# table name to fetch the data from
TABLE = "vm_migration"

def build_sql_query():
    sql = "select * from %s" % TABLE

    if instanceName != '' and migrationState != '':
        sql = sql + " where instance_name=\"%s\" and state=\"%s\"" % (instanceName, migrationState)
        return sql

    if instanceName != '':
        sql = sql + " where instance_name=\"%s\"" % instanceName

    if migrationState != '':
        sql = sql + " where state=\"%s\"" % migrationState

    return sql

def get_migration_data():
    sql = build_sql_query()

    try:
        cursor.execute(sql)
        result = cursor.fetchall()
    except:
        print "Unable to fetch data. Check if table \"vm_migration\" exists in db or not."
        sys.exit(2)

    db.close()
    if len(result) == 0:
        print "No result"
        return

    # We can add more fields in the future if needed
    table = PrettyTable([
                "Instance Name",
                "State",
                "Source Host",
                "Destination Host",
                "Time",
                "User"
            ])

    for entry in result:
        table.add_row([
            entry[3],
            entry[1],
            entry[6],
            entry[7],
            entry[8],
            entry[9]
        ])

    print table

def handleArguments(argv):
    global instanceName
    instanceName = ''
    global migrationState
    migrationState = ''

    help = "Usage: ./" + os.path.basename(__file__) + ' [options]' + \
        '\n  --instance-name <name>\t\tInstance name' + \
        '\n  --state\t\t\t\tGet migration data of particular state. Valid states are Started|Completed|Failed'
    try:
        opts, args = getopt.getopt(
                argv, "h:i:s:",
            [
                "instance-name=", "state="
            ]
        )
    except getopt.GetoptError as e:
        print "Error: " + str(e)
        print help
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print help
            sys.exit()
        elif opt in ("-i", "--instance-name"):
            instanceName = arg
        elif opt in ("-s", "--state"):
            if arg not in ("Failed", "Started", "Completed"):
                print "Invalid state. Please enter one of \"Started, Completed, Failed\""
                sys.exit(2)
            migrationState = arg

def main():
    # Get the migration data
    get_migration_data()

if __name__ == '__main__':
    handleArguments(sys.argv[1:])
    main()
