#!/usr/bin/python

#      Copyright 2015, Schuberg Philis BV
#
#      Licensed to the Apache Software Foundation (ASF) under one
#      or more contributor license agreements.  See the NOTICE file
#      distributed with this work for additional information
#      regarding copyright ownership.  The ASF licenses this file
#      to you under the Apache License, Version 2.0 (the
#      "License"); you may not use this file except in compliance
#      with the License.  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#      Unless required by applicable law or agreed to in writing,
#      software distributed under the License is distributed on an
#      "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#      KIND, either express or implied.  See the License for the
#      specific language governing permissions and limitations
#      under the License.

import sys
import getopt
from cloudstackops import cloudstackops
import os.path
from prettytable import PrettyTable


# Function to handle our arguments
def handleArguments(argv):
    global DEBUG
    DEBUG = 0
    global DRYRUN
    DRYRUN = 0
    global domainID
    domainID = ''
    global domainName
    domainName = ''
    global configProfileName
    configProfileName = ''
    global command
    command = ''
    global force
    force = "false"
    global c
    c = ''

    global resourceValue
    resourceValue = ''
    global VOLUME
    VOLUME = 2
    global SNAPSHOT
    SNAPSHOT = 3
    global TEMPLATE
    TEMPLATE = 4
    global NETWORK
    NETWORK = 6
    global VPC
    VPC = 7
    global CPU
    CPU = 8
    global MEMORY
    MEMORY = 9
    global PRIMARY_STORAGE
    PRIMARY_STORAGE = 10
    global SECONDARY_STORAGE
    SECONDARY_STORAGE = 11
    global resources
    resources = {}
    global resourceType
    resourceType = {'VOLUME'             : 2,
                    'SNAPSHOT'           : 3,
                    'TEMPLATE'           : 4,
                    'NETWORK'            : 6,
                    'VPC'                : 7,
                    'CPU'                : 8,
                    'MEMORY'             : 9,
                    'PRIMARY_STORAGE'    : 10,
                    'SECONDARY_STORAGE'  : 11 }

    # Usage message
    help = "Usage: ./" + os.path.basename(__file__) + ' [options]' + \
        '\n  --config-profile -c <name>\t\tSpecify CloudMonkey profile ' + \
        'name to get the credentials from (or specify in ./config file)' + \
        '\n  --name <name>\t\t\t\tDomain name' + \
        '\n  --cpu <number>\t\t\tNew cpu count the customer can use' + \
        '\n  --memory <number>\t\t\tRAM in MB which the customer can use' + \
        '\n  --storage <number>\t\t\tPrimary Storage in GB which the customer can use' + \
        '\n  --secondary <number>\t\t\tSecondary Storage in GB which the customer can use' + \
        '\n  --debug\t\t\t\tEnable debug mode' + \
        '\n  --exec\t\t\t\tExecute for real (not needed for list* scripts)'

    try:
        opts, args = getopt.getopt(
                argv, "hc:n",
            [
                "config-profile=", "name=", "cpu=", "memory=","debug",
                "storage=", "secondary=", "volumes=", "snapshots="
            ]
        )
    except getopt.GetoptError as e:
        print "Error: " + str(e)
        print help
        sys.exit(2)
    if len(opts) == 0:
        print help
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print help
            sys.exit()
        elif opt in ("-c", "--config-profile"):
            configProfileName = arg
        elif opt in ("--name"):
            domainName  = arg
        elif opt in ("--cpu", "-c"):
            resourceValue = arg
            resources[resourceType['CPU']] = resourceValue
        elif opt in ("--memory", "-m"):
            resourceValue = arg
            resources[resourceType['MEMORY']] = resourceValue
        elif opt in ("--storage", "-p"):
            resourceValue = arg
            resources[resourceType['PRIMARY_STORAGE']] = resourceValue
        elif opt in ("--secondary", "-s"):
            resourceValue = arg
            resources[resourceType['SECONDARY_STORAGE']] = resourceValue
        elif opt in ("--volume", "-v"):
            resourceValue = arg
            resources[resourceType['VOLUME']] = resourceValue
        elif opt in ("--snapshot"):
            resourceValue = arg
            resources[resourceType['SNAPSHOT']] = resourceValue
        elif opt in ("--debug"):
            DEBUG = 1
        elif opt in ("--exec"):
            DRYRUN = 0

    if domainName is '':
        print help
        sys.exit(2)

    if not resources:
        print "Please enter the resource type to be upgraded"
        sys.exit(2)

    # Default to cloudmonkey default config file
    if len(configProfileName) == 0:
        configProfileName = "config"

# Parse arguments
if __name__ == "__main__":
    handleArguments(sys.argv[1:])

# Init our class
c = cloudstackops.CloudStackOps(DEBUG, DRYRUN)

if DEBUG == 1:
    print "Warning: Debug mode is enabled!"

if DRYRUN == 1:
    print "Warning: dry-run mode is enabled, not running any commands!"

# make credentials file known to our class
c.configProfileName = configProfileName

# Init the CloudStack API
c.initCloudStackAPI()

if DEBUG == 1:
    print "API address: " + c.apiurl
    print "ApiKey: " + c.apikey
    print "SecretKey: " + c.secretkey

# Check cloudstack IDs
if DEBUG == 1:
    print "Checking CloudStack IDs of provided input.."

if len(domainName) > 0:
    domainID = c.checkCloudStackName({
        'csname': domainName,
        'csApiCall': 'listDomains'
    })
    if domainID == 1:
        print "Error: domain " + domainName + " does not exist."
        sys.exit(1)

def updateResource():
    args = {}
    args['domainid'] = domainID
    for key in resources:
        args['resourcetype'] = key
        args['resourcevalue'] = resources[key]
        status = c.updateResourceLimit(args)

    status = c.updateResourceCount(args)
    print "Resource count upgraded successfully"

updateResource()

exit(1)
