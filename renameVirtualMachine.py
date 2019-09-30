#!/usr/bin/python

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

# Script to rename a virtual machine from old display name to new display name

import sys
import getopt
from cloudstackops import cloudstackops
import os.path
from prettytable import PrettyTable


# Function to handle our arguments
def handleArguments(argv):
    global DEBUG
    DEBUG = 1
    global DRYRUN
    DRYRUN = 0
    global vmID
    vmID = ''
    global oldName
    oldName = ''
    global newName
    newName = ''
    global configProfileName
    configProfileName = ''
    global c
    c = ''

    # Usage message
    help = "Usage: ./" + os.path.basename(__file__) + ' [options]' + \
        '\n  --config-profile -c <name>\t\tSpecify CloudMonkey profile ' + \
        'name to get the credentials from (or specify in ./config file)' + \
        '\n  --oldname <displayname>\t\t\tZone id where the machine has to be deployed' + \
        '\n  --newname <displayname>\t\t\tDomain id where the machine has to be deployed'

    try:
        opts, args = getopt.getopt(
            argv, "hc:f:o:n:",
            [
                "config-profile=", "oldname=", "newname="
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
        elif opt in ("--oldname", "-o"):
            oldName = arg
        elif opt in ("--newname", "-n"):
            newName = arg


    # Default to cloudmonkey default config file
    if len(configProfileName) == 0:
        configProfileName = "config"

    if oldName == '' or newName == '':
        print "Please enter the old name and new name for the virtual machine"
        sys.exit(1)
# Function to handle stdout vm data
def printVirtualmachine(args):
    args = c.remove_empty_values(args)

    vmdata = (args['vmdata']) if 'vmdata' in args else None
    counter = (args['counter']) if 'counter' in args else 0
    hostCounter = (args['hostCounter']) if 'hostCounter' in args else 0
    memoryTotal = (args['memoryTotal']) if 'memoryTotal' in args else 0
    coresTotal = (args['coresTotal']) if 'coresTotal' in args else 0
    storageSizeTotal = (args['storageSizeTotal']) \
        if 'storageSizeTotal' in args else 0
    hostMemoryTotal = (args['hostMemoryTotal']) \
        if 'hostMemoryTotal' in args else 0
    ignoreDomains = (args['ignoreDomains']) if 'ignoreDomains' in args else []
    clustername = (args['clustername']) if 'clustername' in args else None

    if vmdata is not None:
        for vm in vmdata:
            if vm.domain in ignoreDomains:
                continue
            # Calculate storage usage
            storageSize = c.calculateVirtualMachineStorageUsage(
                vm.id,
                projectParam
            )
            storageSizeTotal = storageSizeTotal + storageSize

            # Memory
            memory = vm.memory / 1024
            memoryTotal = memoryTotal + memory

            # Cores
            coresTotal = coresTotal + vm.cpunumber

            # Counter
            counter = counter + 1

            # Display names
            vmname = (vm.name[:20] + '..') if len(vm.name) >= 22 else vm.name
            vmtemplatedisplaytext = (vm.templatedisplaytext[:40] + '..') if len(vm.templatedisplaytext) >= 42 else vm.templatedisplaytext
            vmmemory = str(memory) + " GB"
            vmstoragesize = str(storageSize) + " GB"

            # Display project and non-project different
            if display != "onlySummary":
                if projectParam == "true":
                    t.add_row([
                        vmname,
                        vmstoragesize,
                        vmtemplatedisplaytext,
                        '-',
                        vmmemory,
                        vm.cpunumber,
                        vm.instancename,
                        vm.hostname,
                        vm.domain,
                        "Proj: " + " " + str(vm.project),
                        vm.created
                    ])
                else:
                    t.add_row([
                        vmname,
                        vmstoragesize,
                        vmtemplatedisplaytext,
                        '-',
                        vmmemory,
                        vm.cpunumber,
                        vm.instancename,
                        vm.hostname,
                        vm.domain,
                        vm.account,
                        vm.created
                    ])
                sys.stdout.write(".")
                sys.stdout.flush()
    return storageSizeTotal, memoryTotal, coresTotal, counter


def renameVirtualMachine():
    if vmID is None or vmID == '':
        print "Unable to find the virtual machine with name " + oldName
        sys.exit(1)

    #vmdata = c.updateVirtualMachine({'displayname': newName,
    #                                 'id': vmID})

    return True
    #print vmdata.virtualmachine.displayname

def renameSecurityGroupsForVirtualMachine():
    if vmID is None or vmID == '':
        print "Unable to find the virtual machine with name " + oldName
        sys.exit(1)

    securitygroupdata = c.listSecurityGroups({'listall': True,
                                              'virtualmachineid': vmID})

    for entry in securitygroupdata:
        print entry.id
        print entry.name

        data = c.updateSecurityGroup({'id': entry.id,
                                      'name': entry.name})
        print data
        print

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


if oldName is not None and oldName is not '':
    vmdata = c.listVirtualmachines({'instancename': oldName})

    print vmdata
    if vmdata == None or vmdata == '':
        print "Unable to find the virtual machine with name " + oldName
        sys.exit(1)

    #if len(vmdata) > 1:
    #    print "Found more than 1 vm with the name " + oldName
    #    print "Unable to rename the virtual machine with name " + oldName
    #    sys.exit(1)

    #print vmdata[0].id
    vmID = vmdata[0].id

    # Rename the virtual machine
    status = renameVirtualMachine()

    # If renaming virtual machine is successful then rename the
    # security group names associated with it
    if status == True:
        renameSecurityGroupsForVirtualMachine()


else:
    print "Please enter vm name"
    exit(1)


sys.exit(1)

clusters = {}
# ClusterID available
if 'fromClusterID' in locals():
    clusters[fromClusterID] = fromCluster
else:
    if len(podname) > 0:
        result = c.listClusters({'podid': podID})
        for cluster in result:
            clusters[cluster.id] = cluster.name
    else:
        result = c.listClusters({'zoneid': zoneID})
        for cluster in result:
            clusters[cluster.id] = cluster.name

if DEBUG == 1:
    print clusters
    print "Debug: display mode = " + display

# Empty line
print

# Look at each cluster
grandCounter = 0
grandHostCounter = 0
grandStorageSizeTotal = 0
grandMemoryTotal = 0
grandCoresTotal = 0
grandHostMemoryTotal = 0

for clusterid, clustername in clusters.items():

    # Get hosts that belong to fromCluster
    fromClusterHostsData = c.getHostsFromCluster(clusterid)

    if fromClusterHostsData == 1 or fromClusterHostsData is None:
        print
        sys.stdout.write("\033[F")
        print "No (enabled) hosts found on cluster " + clustername
        continue

    # Look for VMs on each of the cluster hosts
    counter = 0
    hostCounter = 0
    memoryTotal = 0
    coresTotal = 0
    storageSizeTotal = 0
    hostMemoryTotal = 0
    hostCoresTotal = 0

    # Result table
    t = PrettyTable([
        "VM",
        "Storage",
        "Template",
        "Router nic count",
        "Memory",
        "Cores",
        "Instance",
        "Host",
        "Domain",
        "Account",
        "Created"
    ])
    t.align["VM"] = "l"

    for fromHostData in fromClusterHostsData:
        hostCounter = hostCounter + 1
        grandHostCounter = grandHostCounter + 1

        if DEBUG == 1:
            print "# Looking for VMS on node " + fromHostData.name
            print "# Memory of this host: " + str(fromHostData.memorytotal)

        # Reset progress indication
        print
        sys.stdout.write("\033[F")
        sys.stdout.write("\033[2K")
        sys.stdout.write(fromHostData.name + ":")

        # Count memory on the nodes
        memory = fromHostData.memorytotal / 1024 / 1024 / 1024
        hostMemoryTotal = hostMemoryTotal + memory
        grandHostMemoryTotal = grandHostMemoryTotal + memory

        # Cores
        coresTotal = 0

        # Get all vms of the domainid running on this host
        if onlyDisplayRouters < 1:

            vmdata = c.listVirtualmachines({
                'hostid': fromHostData.id,
                'domainid': domainnameID,
                'isProjectVm': projectParam,
                'projectid': projectnameID,
                'filterKeyword': filterKeyword
            })

            storageSizeTotal, memoryTotal, coresTotal, \
                counter = printVirtualmachine({
                    'vmdata': vmdata,
                    'counter': counter,
                    'hostCounter': hostCounter,
                    'memoryTotal': memoryTotal,
                    'coresTotal': coresTotal,
                    'storageSizeTotal': storageSizeTotal,
                    'hostMemoryTotal': hostMemoryTotal,
                    'ignoreDomains': ignoreDomains,
                    'clustername': clustername
                })

        # Cores
        hostCoresTotal += coresTotal

        # Routers
        if displayRouters < 1:
            continue

        vmdata = c.getRouterData({
            'hostid': fromHostData.id,
            'domainid': domainnameID,
            'isProjectVm': projectParam
        })

        if vmdata is None:
            continue

        for vm in vmdata:
            if vm.domain in ignoreDomains:
                continue

            # Nic
            niccount = len(vm.nic)

            if routerNicCountIsMinimum == 1:
                # Minimum this number of nics
                if len(routerNicCount) > 0 and niccount < int(routerNicCount):
                    continue

            elif routerNicCountIsMaximum == 1:
                # Maximum this number of nics
                if len(routerNicCount) > 0 and niccount > int(routerNicCount):
                    continue

            else:
                # Exactly this number of nics
                if len(routerNicCount) > 0 and niccount != int(routerNicCount):
                    continue

            if onlyDisplayRoutersThatRequireUpdate == 1 and \
                    vm.requiresupgrade is False:
                continue

            # Service Offering (to find allocated RAM)
            serviceOfferingData = c.listServiceOfferings({
                'serviceofferingid': vm.serviceofferingid,
                'issystem': 'true'
            })

            if serviceOfferingData is not None:
                # Memory
                memory = round(float(serviceOfferingData[0].memory) / 1024, 3)
                memoryTotal = memoryTotal + memory
                if serviceOfferingData[0].memory >= 1024:
                    memoryDisplay = str(serviceOfferingData[0].memory / 1024) \
                        + " GB"
                else:
                    memoryDisplay = str(serviceOfferingData[0].memory) + " MB"

                # Cores
                hostCoresTotal += serviceOfferingData[0].cpunumber

            else:
                memoryDisplay = "Unknown"

            # Tabs
            counter = counter + 1

            if vm.isredundantrouter is True:
                redundantstate = vm.redundantstate
            elif vm.vpcid is not None:
                redundantstate = "VPC"
            else:
                redundantstate = "SINGLE"

            # Name of the network / VPC
            if vm.vpcid is not None:
                networkResult = c.listVPCs({'id': vm.vpcid})
            else:
                networkResult = c.listNetworks({'id': vm.guestnetworkid})

            if networkResult is not None:
                displayname = networkResult[0].name
                displayname = (networkResult[0].name[:18] + '..') \
                    if len(networkResult[0].name) >= 21 \
                    else networkResult[0].name
            else:
                displayname = (vm.name[:18] + '..') \
                    if len(vm.name) >= 21 else vm.name

            displayname = displayname + " (" + redundantstate.lower() + ")"

            if vm.requiresupgrade is True:
                displayname = displayname + " [ReqUpdate!]"

            vmniccount = str(niccount) + " nics "

            # Display project and non-project different
            if display != "onlySummary":
                if vm.project:
                    try:
                        t.add_row([
                            displayname,
                            '-',
                            '-',
                            vmniccount,
                            memoryDisplay,
                            serviceOfferingData[0].cpunumber,
                            vm.name,
                            vm.hostname,
                            vm.domain,
                            "Proj: " + " " + vm.project,
                            vm.created
                        ])
                    except:
                        t.add_row([
                            displayname,
                            '-',
                            '-',
                            vmniccount,
                            memoryDisplay,
                            'Unknown',
                            vm.name,
                            vm.hostname,
                            vm.domain,
                            "Proj: " + " " + vm.project,
                            vm.created
                        ])
                else:
                    try:
                        t.add_row([
                            displayname,
                            '-',
                            '-',
                            vmniccount,
                            memoryDisplay,
                            serviceOfferingData[0].cpunumber,
                            vm.name,
                            vm.hostname,
                            vm.domain,
                            vm.account,
                            vm.created
                        ])
                    except:
                        t.add_row([
                            displayname,
                            '-',
                            '-',
                            vmniccount,
                            memoryDisplay,
                            'Unknown',
                            vm.name,
                            vm.hostname,
                            vm.domain,
                            vm.account,
                            vm.created
                        ])

                sys.stdout.write(".")
                sys.stdout.flush()

    if counter > 0 and display != "onlySummary":
        # Remove progress indication
        sys.stdout.write("\033[F")

        # Print result table
        print
        print t

    if counter > 0 and display != "plain":
        memoryUtilisation = round((memoryTotal / float(
            hostMemoryTotal)) * 100, 2)
        print ""
        print "Summary '" + clustername + "':"
        print " Total number of VMs: " + str(counter)

        if not len(domainname) > 0 \
            and not len(filterKeyword) > 0 \
            and not len(projectname) > 0 \
            and projectParam == 'false' \
            and not (len(routerNicCount) > 0 or
                     displayRouters < 1 or
                     onlyDisplayRouters == 1
                     ):
            print " Total number hypervisors: " + str(hostCounter)
            print " Total allocated RAM: " + str(memoryTotal) + " / " + \
                str(hostMemoryTotal) + " GB (" + str(memoryUtilisation) + " %)"
            print " Total allocated cores: " + str(hostCoresTotal)
            print " Total allocated storage: " + str(storageSizeTotal) + " GB"
        else:
            print " Total allocated RAM: " + str(memoryTotal) + " GB"
            print " Total allocated cores: " + str(hostCoresTotal)

        print ""
        grandCounter = grandCounter + counter
        grandStorageSizeTotal = grandStorageSizeTotal + storageSizeTotal
        grandMemoryTotal = grandMemoryTotal + memoryTotal
        grandCoresTotal = grandCoresTotal + hostCoresTotal


if len(clusters) > 1 and display == "onlySummary":
    grandMemoryUtilisation = round((grandMemoryTotal / float(
        grandHostMemoryTotal)) * 100, 2)
    print ""
    print "==================  Grand Totals ==============="
    print " Total number of VMs: " + str(grandCounter)

    if not len(domainname) > 0 \
            and not len(filterKeyword) > 0 \
            and not len(projectname) > 0 \
            and projectParam == 'false':
        print " Total number hypervisors: " + str(grandHostCounter)
        print " Total allocated RAM: " + str(grandMemoryTotal) + " / " + \
            str(grandHostMemoryTotal) + " GB (" + \
            str(grandMemoryUtilisation) + " %)"
        print " Total allocated storage: " + str(grandStorageSizeTotal) + " GB"
    else:
        print " Total allocated RAM: " + str(grandMemoryTotal) + " GB"
        print " Total allocated cores: " + str(grandCoresTotal)

    print "================================================"
    print ""

if DEBUG == 1:
    print "Note: We're done!"

# Remove progress indication
sys.stdout.write("\033[F")
print
