#!/usr/bin/python
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
#
# Algorithm:
#   1. Check if the VM exists.
#   2. If the vm exists then stop it if its in running state
#   3. Create a template from the root disk of the VM
#   4. Use the newly created template to deploy new virtual machine
#   5. If deploy is successful then start the original vm if it was running previously
#
# Script to clone an existing virtual machine
# Usage:
#   Clone an existing VM by passing its UUID
#
#   ./cloneVirtualMachine.py --machineid <uuid of existing vm> -c <server profile>
#
#   Clone an existing VM by passing its UUID and optional displayname
#   for the newly cloned vm
#
#   ./cloneVirtualMachine.py --machineid <uuid of existing vm> --displayname "new name" -c <server profile>
#
#   To stop the VM forcefully use "--forcestop|-f" option

import sys
import getopt
from cloudstackops import cloudstackops
import os.path
from prettytable import PrettyTable


# Function to handle our arguments
def handleArguments(argv):
    global DEBUG
    DEBUG = 0
    global uuid
    uuid = ''
    global zoneId
    zoneId = ''
    global serviceOfferingId
    serviceOfferingId = ''
    global networkId
    networkId = ''
    global accountNumber
    accountNumber = ''
    global securityGroupIds
    securityGroupIds = ''
    global affinityGroupIds
    affinityGroupIds = ''
    global displayName
    displayName = ''
    global configProfileName
    configProfileName = ''
    global vmState
    vmState = 0
    global vmPassword
    vmPassword = ''
    global forceStop
    forceStop = False

    # Usage message
    help = "Usage: ./" + os.path.basename(__file__) + ' [options]' + \
        '\n  --config-profile -c <name>\t\tSpecify CloudMonkey profile ' + \
        'name to get the credentials from (or specify in ./config file)' + \
        '\n  --displayname <vm display name>\tDisplay name for the cloned vm' + \
        '\n  --machineid -i <uuid>\t\t\tUUID of the vm to be cloned' + \
        '\n  --forcestop -f \t\t\tStop the VM forcefully' + \
        '\n  --debug\t\t\t\tEnable debug mode'

    try:
        opts, args = getopt.getopt(
            argv, "hfc:d:i:",
            [
                "config-profile=", "displayname=", "machineid=","debug", "forcestop"
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
        elif opt in ("--displayname", "-d"):
            displayName = arg
        elif opt in ("-i", "--machineid"):
            uuid = arg
        elif opt in ("--debug"):
            DEBUG = 1
        elif opt in ("--forcestop", "-f"):
            forceStop = True

    # Default to cloudmonkey default config file
    if len(configProfileName) == 0:
        configProfileName = "config"


def getVirtualMachineVolumes():
    return c.getVirtualmachineVolumes(uuid)


def deployVirtualMachine(args):
    vmdata = args['vmdata']

    # Mandatory parameters
    zoneId = vmdata[0].zoneid
    serviceOfferingId = vmdata[0].serviceofferingid
    templateId = args['templateId']

    # Optional parameters
    accountNumber = vmdata[0].account

    # get affinity group id's
    affinityGroupIds = ''
    affinityGroups = vmdata[0].affinitygroup
    for ag in affinityGroups:
        affinityGroupIds = affinityGroupIds + ag.id + ","

    affinityGroupIds = affinityGroupIds[:-1]

    # get data disks
    diskOfferingIds = ''
    volumeData = getVirtualMachineVolumes()
    for volumes in volumeData:
        if volumes.type == "DATADISK":
            diskOfferingIds = diskOfferingIds + volumes.diskofferingid + ","

    diskOfferingIds = diskOfferingIds[:-1]

    # Get displayvm
    displayvm = vmdata[0].displayvm

    # Get domainid
    domainId = vmdata[0].domainid

    # Get ssh key pair
    sshKeyPair = vmdata[0].keypair

    # get network id's
    nics = vmdata[0].nic
    networkId = ''
    for nic in nics:
        networkId = networkId + nic.networkid + ","

    networkId = networkId[:-1]

    # Get security group id's
    securitygroup = vmdata[0].securitygroup
    securityGroupIds = ''
    for sg in securitygroup:
        securityGroupIds = securityGroupIds + sg.id + ","

    securityGroupIds = securityGroupIds[:-1]

    print "Deploying the new virtual machine with template id " + templateId
    vmcreationdata = c.deployVirtualMachine({
        'zoneid': zoneId,
        'domainid': domainId,
        'networkids': networkId,
        'templateid': templateId,
        'serviceofferingid': serviceOfferingId,
        'account': accountNumber,
        'affinitygroupids': affinityGroupIds,
        'diskofferingid': diskOfferingIds,
        'displayvm': displayvm,
        'keypair': sshKeyPair,
        'securitygroupids': securityGroupIds,
        'displayname': displayName,
        'name': displayName,
        'startvm': True
    })

    return vmcreationdata


def printNewVirtualMachineDetails(args):
    table = PrettyTable([
        "VM Name",
        "Instance Name",
        "State",
        "Ip address",
        "Network Name",
        "UUID",
        "Template id"
    ])

    virtualmachine = args['vmdata'].virtualmachine

    nics = virtualmachine.nic
    ipAddress = ''
    networkName = ''
    for nic in nics:
        ipAddress = ipAddress + nic.ipaddress + ","
        networkName = networkName + nic.networkname + ","

    ipAddress = ipAddress[:-1]
    networkName = networkName[:-1]

    table.add_row([
        virtualmachine.name,
        virtualmachine.instancename,
        virtualmachine.state,
        ipAddress,
        networkName,
        virtualmachine.id,
        args['templateId']
    ])

    print table


def cmdStartVirtualMachine():
    vmdata = c.getVirtualmachineData(uuid)
    if vmdata[0].state == "Running":
        print "Virtual machine is already running"
        sys.exit(1)

    status = c.startVirtualMachine(uuid)
    if status.virtualmachine.state == "Running":
        print "Original Machine succesfully started"


def cmdStopVirtualMachine():
    vmdata = c.getVirtualmachineData(uuid)
    if vmdata[0].state == "Stopped":
        print "Virtual machine is already stopped. Creating the template of this VM now"
        return

    print "Stopping the virtual machine. Please wait"
    status = c.stopVirtualMachine(uuid, forceStop)
    if status.virtualmachine.state == "Stopped":
        print "Machine successfully stopped. Creating the template of this VM now."
        vmState = 1
    else:
        print "Unable to stop the virtual machine. Please stop the machine and try again"
        return 0


def cmdCreateTemplate(args):
    data = args[0]
    templateName = data.instancename

    # Template name and display text can have max 32 characters
    if len(templateName) > 26:
        templateName = templateName[:-6]

    templateName = templateName + "-CLONE"

    templateDisplayText = data.templatename

    osTypeId = data.ostypeid

    volumeData = getVirtualMachineVolumes()

    # Get the volume ID of the ROOT disk
    volumeId = ''
    for volumes in volumeData:
        if volumes.type == "ROOT":
            volumeId = volumes.id
            break

    # Create the template from the ROOT disk of the VM
    templateCreationData = c.createTemplate({
        'displaytext': templateDisplayText,
        'name': templateName,
        'ostypeid': osTypeId,
        'volumeid': volumeId
    })

    return templateCreationData


def cmdDeleteTemplate(args):
    templateId = args['templateid']

    # delete the template
    data = c.deleteTemplate({'id': templateId})
    print data.success


def rollBack(args):
    #Delete the old template
    cmdDeleteTemplate(args)

    # Start the virtual machine if it was running initially
    if vmState == 1:
        cmdStartVirtualMachine()


# Parse arguments
if __name__ == "__main__":
    handleArguments(sys.argv[1:])

# Init our class
c = cloudstackops.CloudStackOps(DEBUG, 0)

if DEBUG == 1:
    print "Warning: Debug mode is enabled!"

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

vmdata = c.listVirtualmachines({'id': uuid})
if vmdata == 1:
    print "Unable to find the machine with id " + uuid
    sys.exit(2)

# Get the state of the VM
if vmdata[0].state == "Running":
    vmState = 1

# Stop the virtual machine if its running
status = cmdStopVirtualMachine()
if status == 0:
    print "Unable to stop the virtual machine. Please stop it manually and try again"
    sys.exit(2)

# Create the template from the original virtual machine
templateData = cmdCreateTemplate(vmdata)
if templateData == 1:
    # If unable to create the template then start the VM if it was running previously
    if vmState == 1:
        cmdStartVirtualMachine()

    print "Unable to create the template from original virtual machine"
    sys.exit(2)

# Store the template id of the newly created template
templateId = templateData.template.id

if templateId is not None or templateId != '':
    print "Created new template with id " + templateData.template.id + \
            " and name " + templateData.template.name

# Deploy the virtual machine with the newly created template
vmdata = deployVirtualMachine({'vmdata': vmdata,
                               'templateId': templateId})
if vmdata == 1:
    # If we are unable to clone the VM then delete the newly created template
    # and start the original vm if it was running
    rollBack({'templateid': templateId})
    print "Error happened. Unable to deploy the new Virtual Machine"
    sys.exit(2)

# We are able to successfully clone the VM.
# Start the original virtual machine
if vmState == 1:
    print "Starting the original virtual machine"
    cmdStartVirtualMachine()
else:
    print "The original virtual machine was not running. So not starting it"

print "Successfully cloned the virtual machine"

# Print the details of the newly created VM
printNewVirtualMachineDetails({'vmdata': vmdata,
                              'templateId': templateId})
exit(0)