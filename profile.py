"""Create single/multiple inter-connected nodes with 10.10.1.x IP addresses. An NFS server is attached to all nodes, mounted at `/nfs` path.

Instructions:
General: Wait for the experiment to start, and then log into one or more of the nodes
by clicking on them in the topology, and choosing the `shell` menu option.
Use `sudo` to run root commands.

You won't need to access the NFS server. Instead, you should majorly working with created instances marked as "node-*".
"""

# Import the Portal object.
import geni.portal as portal
# Import the ProtoGENI library.
import geni.rspec.pg as pg
# Emulab specific extensions.
import geni.rspec.emulab as emulab

import math

# Create a portal context, needed to defined parameters
pc = portal.Context()

# Create a Request object to start building the RSpec.
request = pc.makeRequestRSpec()

# Variable number of nodes.
pc.defineParameter("nodeCount", "Number of Nodes", portal.ParameterType.INTEGER, 1,
                   longDescription="If you specify more then one node, " +
                   "we will create a lan for you.")

# Pick your OS.
imageList = [
    ('urn:publicid:IDN+emulab.net+image+flashburst:ddb.ready', 'UBUNTU 22.04')
]
# ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-STD', 'UBUNTU 22.04')

pc.defineParameter("osImage", "Select OS image",
                   portal.ParameterType.IMAGE,
                   imageList[0], imageList,
                   longDescription="Pick a image...")

# Optional physical type for all nodes.
pc.defineParameter("phystype",  "Optional physical node type",
                   portal.ParameterType.STRING, "d710",
                   longDescription="Specify a single physical node type (pc3000,d710,etc) " +
                   "instead of letting the resource mapper choose for you.")

# Sometimes you want all of nodes on the same switch, Note that this option can make it impossible
# for your experiment to map.
pc.defineParameter("sameSwitch",  "No Interswitch Links", portal.ParameterType.BOOLEAN, False,
                    advanced=True,
                    longDescription="Sometimes you want all the nodes connected to the same switch. " +
                    "This option will ask the resource mapper to do that, although it might make " +
                    "it impossible to find a solution. Do not use this unless you are sure you need it!")

# Retrieve the values the user specifies during instantiation.
params = pc.bindParameters()

# Check parameter validity.
if params.nodeCount < 1:
    pc.reportError(portal.ParameterError("You must choose at least 1 node.", ["nodeCount"]))

if params.phystype != "":
    tokens = params.phystype.split(",")
    if len(tokens) != 1:
        pc.reportError(portal.ParameterError("Only a single type is allowed", ["phystype"]))

pc.verifyParameters()

# # Do not change these unless you change the setup scripts too.
nfsServerName = "nfs"
nfsLanName    = "nfsLan"
nfsDirectory  = "/nfs"

# The NFS network. All these options are required.
nfsLan = request.LAN(nfsLanName)
nfsLan.best_effort       = True
nfsLan.vlan_tagging      = True
nfsLan.link_multiplexing = True

# The NFS server.
nfsServer = request.RawPC(nfsServerName)
nfsServer.disk_image = params.osImage
# Attach server to lan.
nfsLan.addInterface(nfsServer.addInterface("eth1", pg.IPv4Address('10.10.1.100', '255.255.255.0')))
# Storage file system goes into a local (ephemeral) blockstore.
nfsBS = nfsServer.Blockstore("nfsBS", nfsDirectory)
nfsBS.size = "200GB"
# Initialization script for the server
nfsServer.addService(pg.Execute(shell="sh", command="sudo /bin/bash /local/repository/nfs-server.sh"))

# Process nodes, adding to link.
for i in range(params.nodeCount):
    # Create a node and add it to the request
    name = "node" + str(i)
    node = request.RawPC(name)
    node.routable_control_ip = False

    if params.osImage and params.osImage != "default":
        node.disk_image = params.osImage
    
    # Optional hardware type.
    if params.phystype != "":
        node.hardware_type = params.phystype

    # Prepare interface
    iface = node.addInterface("eth1", pg.IPv4Address('10.10.1.%d' % (i + 1),'255.255.255.0'))

    # setup dataset
    nfsLan.addInterface(iface)

    ### run setup scripts
    # Initialization script for the clients
    node.addService(pg.Execute(shell="sh", command="sudo /bin/bash /local/repository/nfs-client.sh"))
    #
    # install mount point && generate ssh keys
    node.addService(pg.Execute(shell="sh", command="sudo /bin/bash /local/repository/ssh.sh > /tmp/ssh.log 2>&1"))
    #
    # node.addService(pg.Execute(shell="bash",
    #     command="/local/repository/mount.sh > /tmp/mount.log 2>&1"))

    # dependencies installation
    # node.addService(pg.Execute(shell="sh", command="sudo /bin/bash /local/repository/install-dependencies.sh > /tmp/dependencies.log 2>&1"))


    # increase number of open file descriptors
    node.addService(pg.Execute(shell="sh", command="sudo /bin/bash /local/repository/ulimit.sh > /tmp/ulimit.log 2>&1"))
    
# Print the RSpec to the enclosing page.
pc.printRequestRSpec(request)
