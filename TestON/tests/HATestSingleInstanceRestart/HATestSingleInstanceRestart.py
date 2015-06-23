"""
Description: This test is to determine if a single
    instance ONOS 'cluster' can handle a restart

List of test cases:
CASE1: Compile ONOS and push it to the test machines
CASE2: Assign devices to controllers
CASE21: Assign mastership to controllers
CASE3: Assign intents
CASE4: Ping across added host intents
CASE5: Reading state of ONOS
CASE6: The Failure case.
CASE7: Check state after control plane failure
CASE8: Compare topo
CASE9: Link s3-s28 down
CASE10: Link s3-s28 up
CASE11: Switch down
CASE12: Switch up
CASE13: Clean up
CASE14: start election app on all onos nodes
CASE15: Check that Leadership Election is still functional
CASE16: Install Distributed Primitives app
CASE17: Check for basic functionality with distributed primitives
"""


class HATestSingleInstanceRestart:

    def __init__( self ):
        self.default = ''

    def CASE1( self, main ):
        """
        CASE1 is to compile ONOS and push it to the test machines

        Startup sequence:
        cell <name>
        onos-verify-cell
        NOTE: temporary - onos-remove-raft-logs
        onos-uninstall
        start mininet
        git pull
        mvn clean install
        onos-package
        onos-install -f
        onos-wait-for-start
        start cli sessions
        start tcpdump
        """
        main.log.info( "ONOS Single node cluster restart " +
                         "HA test - initialization" )
        main.case( "Setting up test environment" )
        main.caseExplaination = "Setup the test environment including " +\
                                "installing ONOS, starting Mininet and ONOS" +\
                                "cli sessions."
        # TODO: save all the timers and output them for plotting

        # load some variables from the params file
        PULLCODE = False
        if main.params[ 'Git' ] == 'True':
            PULLCODE = True
        gitBranch = main.params[ 'branch' ]
        cellName = main.params[ 'ENV' ][ 'cellName' ]

        # set global variables
        global ONOS1Ip
        global ONOS1Port
        global ONOS2Port
        global ONOS3Port
        global ONOS4Port
        global ONOS5Port
        global ONOS6Port
        global ONOS7Port
        global numControllers
        numControllers = int( main.params[ 'num_controllers' ] )

        ONOS1Ip = main.params[ 'CTRL' ][ 'ip1' ]
        ONOS1Port = main.params[ 'CTRL' ][ 'port1' ]
        ONOS2Port = main.params[ 'CTRL' ][ 'port2' ]
        ONOS3Port = main.params[ 'CTRL' ][ 'port3' ]
        ONOS4Port = main.params[ 'CTRL' ][ 'port4' ]
        ONOS5Port = main.params[ 'CTRL' ][ 'port5' ]
        ONOS6Port = main.params[ 'CTRL' ][ 'port6' ]
        ONOS7Port = main.params[ 'CTRL' ][ 'port7' ]

        global CLIs
        CLIs = []
        global nodes
        nodes = []
        for i in range( 1, numControllers + 1 ):
            CLIs.append( getattr( main, 'ONOScli' + str( i ) ) )
            nodes.append( getattr( main, 'ONOS' + str( i ) ) )

        main.step( "Applying cell variable to environment" )
        cellResult = main.ONOSbench.setCell( cellName )
        verifyResult = main.ONOSbench.verifyCell()

        # FIXME:this is short term fix
        main.log.info( "Removing raft logs" )
        main.ONOSbench.onosRemoveRaftLogs()

        main.log.info( "Uninstalling ONOS" )
        for node in nodes:
            main.ONOSbench.onosUninstall( node.ip_address )

        # Make sure ONOS is DEAD
        main.log.info( "Killing any ONOS processes" )
        killResults = main.TRUE
        for node in nodes:
            killed = main.ONOSbench.onosKill( node.ip_address )
            killResults = killResults and killed

        cleanInstallResult = main.TRUE
        gitPullResult = main.TRUE

        main.step( "Starting Mininet" )
        mnResult = main.Mininet1.startNet( )
        utilities.assert_equals( expect=main.TRUE, actual=mnResult,
                                 onpass="Mininet Started",
                                 onfail="Error starting Mininet" )

        main.step( "Git checkout and pull " + gitBranch )
        if PULLCODE:
            main.ONOSbench.gitCheckout( gitBranch )
            gitPullResult = main.ONOSbench.gitPull()
            # values of 1 or 3 are good
            utilities.assert_lesser( expect=0, actual=gitPullResult,
                                      onpass="Git pull successful",
                                      onfail="Git pull failed" )
        main.ONOSbench.getVersion( report=True )

        main.step( "Using mvn clean install" )
        cleanInstallResult = main.TRUE
        if PULLCODE and gitPullResult == main.TRUE:
            cleanInstallResult = main.ONOSbench.cleanInstall()
        else:
            main.log.warn( "Did not pull new code so skipping mvn " +
                           "clean install" )
        utilities.assert_equals( expect=main.TRUE,
                                 actual=cleanInstallResult,
                                 onpass="MCI successful",
                                 onfail="MCI failed" )
        # GRAPHS
        # NOTE: important params here:
        #       job = name of Jenkins job
        #       Plot Name = Plot-HA, only can be used if multiple plots
        #       index = The number of the graph under plot name
        job = "HASingleInstanceRestart"
        plotName = "Plot-HA"
        graphs = '<ac:structured-macro ac:name="html">\n'
        graphs += '<ac:plain-text-body><![CDATA[\n'
        graphs += '<iframe src="https://onos-jenkins.onlab.us/job/' + job +\
                  '/plot/' + plotName + '/getPlot?index=0' +\
                  '&width=500&height=300"' +\
                  'noborder="0" width="500" height="300" scrolling="yes" ' +\
                  'seamless="seamless"></iframe>\n'
        graphs += ']]></ac:plain-text-body>\n'
        graphs += '</ac:structured-macro>\n'
        main.log.wiki(graphs)

        cellResult = main.ONOSbench.setCell( "SingleHA" )
        verifyResult = main.ONOSbench.verifyCell()
        main.step( "Creating ONOS package" )
        packageResult = main.ONOSbench.onosPackage()
        utilities.assert_equals( expect=main.TRUE, actual=packageResult,
                                 onpass="ONOS package successful",
                                 onfail="ONOS package failed" )

        main.step( "Installing ONOS package" )
        onosInstallResult = main.ONOSbench.onosInstall( options="-f",
                                                           node=ONOS1Ip )
        utilities.assert_equals( expect=main.TRUE, actual=onosInstallResult,
                                 onpass="ONOS install successful",
                                 onfail="ONOS install failed" )

        main.step( "Checking if ONOS is up yet" )
        for i in range( 2 ):
            onos1Isup = main.ONOSbench.isup( ONOS1Ip )
            if onos1Isup:
                break
        utilities.assert_equals( expect=main.TRUE, actual=onos1Isup,
                                 onpass="ONOS startup successful",
                                 onfail="ONOS startup failed" )

        main.log.step( "Starting ONOS CLI sessions" )
        cliResults = main.ONOScli1.startOnosCli( ONOS1Ip )
        utilities.assert_equals( expect=main.TRUE, actual=cliResults,
                                 onpass="ONOS cli startup successful",
                                 onfail="ONOS cli startup failed" )

        if main.params[ 'tcpdump' ].lower() == "true":
            main.step( "Start Packet Capture MN" )
            main.Mininet2.startTcpdump(
                str( main.params[ 'MNtcpdump' ][ 'folder' ] ) + str( main.TEST )
                + "-MN.pcap",
                intf=main.params[ 'MNtcpdump' ][ 'intf' ],
                port=main.params[ 'MNtcpdump' ][ 'port' ] )

        main.step( "App Ids check" )
        appCheck = main.ONOScli1.appToIDCheck()
        if appCheck != main.TRUE:
            main.log.warn( CLIs[0].apps() )
            main.log.warn( CLIs[0].appIDs() )
        utilities.assert_equals( expect=main.TRUE, actual=appCheck,
                                 onpass="App Ids seem to be correct",
                                 onfail="Something is wrong with app Ids" )

        if cliResults == main.FALSE:
            main.log.error( "Failed to start ONOS, stopping test" )
            main.cleanup()
            main.exit()

    def CASE2( self, main ):
        """
        Assign devices to controllers
        """
        import re
        import time
        assert numControllers, "numControllers not defined"
        assert main, "main not defined"
        assert utilities.assert_equals, "utilities.assert_equals not defined"
        assert ONOS1Port, "ONOS1Port not defined"
        assert ONOS2Port, "ONOS2Port not defined"
        assert ONOS3Port, "ONOS3Port not defined"
        assert ONOS4Port, "ONOS4Port not defined"
        assert ONOS5Port, "ONOS5Port not defined"
        assert ONOS6Port, "ONOS6Port not defined"
        assert ONOS7Port, "ONOS7Port not defined"

        main.case( "Assigning devices to controllers" )
        main.caseExplaination = "Assign switches to ONOS using 'ovs-vsctl' " +\
                                "and check that an ONOS node becomes the " +\
                                "master of the device."
        main.step( "Assign switches to controllers" )

        for i in range( 1, 29 ):
            main.Mininet1.assignSwController(
                sw=str( i ),
                ip1=ONOS1Ip, port1=ONOS1Port )

        mastershipCheck = main.TRUE
        for i in range( 1, 29 ):
            response = main.Mininet1.getSwController( "s" + str( i ) )
            try:
                main.log.info( str( response ) )
            except Exception:
                main.log.info( repr( response ) )
            if re.search( "tcp:" + ONOS1Ip, response ):
                mastershipCheck = mastershipCheck and main.TRUE
            else:
                mastershipCheck = main.FALSE
        if mastershipCheck == main.TRUE:
            main.log.info( "Switch mastership assigned correctly" )
        utilities.assert_equals(
            expect=main.TRUE,
            actual=mastershipCheck,
            onpass="Switch mastership assigned correctly",
            onfail="Switches not assigned correctly to controllers" )

    def CASE21( self, main ):
        """
        Assign mastership to controllers
        """
        import re
        import time
        assert numControllers, "numControllers not defined"
        assert main, "main not defined"
        assert utilities.assert_equals, "utilities.assert_equals not defined"
        assert CLIs, "CLIs not defined"
        assert nodes, "nodes not defined"
        assert ONOS1Port, "ONOS1Port not defined"
        assert ONOS2Port, "ONOS2Port not defined"
        assert ONOS3Port, "ONOS3Port not defined"
        assert ONOS4Port, "ONOS4Port not defined"
        assert ONOS5Port, "ONOS5Port not defined"
        assert ONOS6Port, "ONOS6Port not defined"
        assert ONOS7Port, "ONOS7Port not defined"

        main.case( "Assigning Controller roles for switches" )
        main.caseExplaination = "Check that ONOS is connected to each " +\
                                "device. Then manually assign" +\
                                " mastership to specific ONOS nodes using" +\
                                " 'device-role'"
        main.step( "Assign mastership of switches to specific controllers" )
        roleCall = main.TRUE
        roleCheck = main.TRUE
        try:
            for i in range( 1, 29 ):  # switches 1 through 28
                ip = nodes[ 0 ].ip_address  # ONOS1
                # set up correct variables:
                if i == 1:
                    deviceId = main.ONOScli1.getDevice( "1000" ).get( 'id' )
                elif i == 2:
                    deviceId = main.ONOScli1.getDevice( "2000" ).get( 'id' )
                elif i == 3:
                    deviceId = main.ONOScli1.getDevice( "3000" ).get( 'id' )
                elif i == 4:
                    deviceId = main.ONOScli1.getDevice( "3004" ).get( 'id' )
                elif i == 5:
                    deviceId = main.ONOScli1.getDevice( "5000" ).get( 'id' )
                elif i == 6:
                    deviceId = main.ONOScli1.getDevice( "6000" ).get( 'id' )
                elif i == 7:
                    deviceId = main.ONOScli1.getDevice( "6007" ).get( 'id' )
                elif i >= 8 and i <= 17:
                    dpid = '3' + str( i ).zfill( 3 )
                    deviceId = main.ONOScli1.getDevice( dpid ).get( 'id' )
                elif i >= 18 and i <= 27:
                    dpid = '6' + str( i ).zfill( 3 )
                    deviceId = main.ONOScli1.getDevice( dpid ).get( 'id' )
                elif i == 28:
                    deviceId = main.ONOScli1.getDevice( "2800" ).get( 'id' )
                else:
                    main.log.error( "You didn't write an else statement for " +
                                    "switch s" + str( i ) )
                # Assign switch
                assert deviceId, "No device id for s" + str( i ) + " in ONOS"
                # TODO: make this controller dynamic
                roleCall = roleCall and main.ONOScli1.deviceRole( deviceId,
                                                                  ip )
                # Check assignment
                master = main.ONOScli1.getRole( deviceId ).get( 'master' )
                if ip in master:
                    roleCheck = roleCheck and main.TRUE
                else:
                    roleCheck = roleCheck and main.FALSE
                    main.log.error( "Error, controller " + ip + " is not" +
                                    " master " + "of device " +
                                    str( deviceId ) + ". Master is " +
                                    repr( master ) + "." )
        except ( AttributeError, AssertionError ):
            main.log.exception( "Something is wrong with ONOS device view" )
            main.log.info( main.ONOScli1.devices() )
        utilities.assert_equals(
            expect=main.TRUE,
            actual=roleCall,
            onpass="Re-assigned switch mastership to designated controller",
            onfail="Something wrong with deviceRole calls" )

        main.step( "Check mastership was correctly assigned" )
        utilities.assert_equals(
            expect=main.TRUE,
            actual=roleCheck,
            onpass="Switches were successfully reassigned to designated " +
                   "controller",
            onfail="Switches were not successfully reassigned" )

    def CASE3( self, main ):
        """
        Assign intents
        """
        import time
        import json
        assert numControllers, "numControllers not defined"
        assert main, "main not defined"
        assert utilities.assert_equals, "utilities.assert_equals not defined"
        # NOTE: we must reinstall intents until we have a persistant intent
        #        datastore!
        main.case( "Adding host Intents" )
        main.caseExplaination = "Discover hosts by using pingall then " +\
                                "assign predetermined host-to-host intents." +\
                                " After installation, check that the intent" +\
                                " is distributed to all nodes and the state" +\
                                " is INSTALLED"

        # install onos-app-fwd
        main.step( "Install reactive forwarding app" )
        installResults = CLIs[0].activateApp( "org.onosproject.fwd" )
        utilities.assert_equals( expect=main.TRUE, actual=installResults,
                                 onpass="Install fwd successful",
                                 onfail="Install fwd failed" )

        main.step( "Check app ids" )
        appCheck = main.ONOScli1.appToIDCheck()
        if appCheck != main.TRUE:
            main.log.warn( CLIs[0].apps() )
            main.log.warn( CLIs[0].appIDs() )
        utilities.assert_equals( expect=main.TRUE, actual=appCheck,
                                 onpass="App Ids seem to be correct",
                                 onfail="Something is wrong with app Ids" )

        main.step( "Discovering Hosts( Via pingall for now )" )
        # FIXME: Once we have a host discovery mechanism, use that instead
        # REACTIVE FWD test
        pingResult = main.FALSE
        for i in range(2):  # Retry if pingall fails first time
            time1 = time.time()
            pingResult = main.Mininet1.pingall()
            utilities.assert_equals(
                expect=main.TRUE,
                actual=pingResult,
                onpass="Reactive Pingall test passed",
                onfail="Reactive Pingall failed, " +
                       "one or more ping pairs failed" )
            time2 = time.time()
            main.log.info( "Time for pingall: %2f seconds" %
                           ( time2 - time1 ) )
        # timeout for fwd flows
        time.sleep( 11 )
        # uninstall onos-app-fwd
        main.step( "Uninstall reactive forwarding app" )
        uninstallResult = CLIs[0].deactivateApp( "org.onosproject.fwd" )
        utilities.assert_equals( expect=main.TRUE, actual=uninstallResult,
                                 onpass="Uninstall fwd successful",
                                 onfail="Uninstall fwd failed" )

        main.step( "Check app ids" )
        appCheck2 = main.ONOScli1.appToIDCheck()
        if appCheck2 != main.TRUE:
            main.log.warn( CLIs[0].apps() )
            main.log.warn( CLIs[0].appIDs() )
        utilities.assert_equals( expect=main.TRUE, actual=appCheck2,
                                 onpass="App Ids seem to be correct",
                                 onfail="Something is wrong with app Ids" )

        main.step( "Add host intents via cli" )
        intentIds = []
        # TODO:  move the host numbers to params
        #        Maybe look at all the paths we ping?
        intentAddResult = True
        hostResult = main.TRUE
        for i in range( 8, 18 ):
            main.log.info( "Adding host intent between h" + str( i ) +
                           " and h" + str( i + 10 ) )
            host1 = "00:00:00:00:00:" + \
                str( hex( i )[ 2: ] ).zfill( 2 ).upper()
            host2 = "00:00:00:00:00:" + \
                str( hex( i + 10 )[ 2: ] ).zfill( 2 ).upper()
            # NOTE: getHost can return None
            host1Dict = main.ONOScli1.getHost( host1 )
            host2Dict = main.ONOScli1.getHost( host2 )
            host1Id = None
            host2Id = None
            if host1Dict and host2Dict:
                host1Id = host1Dict.get( 'id', None )
                host2Id = host2Dict.get( 'id', None )
            if host1Id and host2Id:
                tmpId = main.ONOScli1.addHostIntent( host1Id, host2Id )
                if tmpId:
                    main.log.info( "Added intent with id: " + tmpId )
                    intentIds.append( tmpId )
                else:
                    main.log.error( "addHostIntent returned: " +
                                     repr( tmpId ) )
            else:
                main.log.error( "Error, getHost() failed for h" + str( i ) +
                                " and/or h" + str( i + 10 ) )
                hosts = main.ONOScli1.hosts()
                main.log.warn( "Hosts output: " )
                try:
                    main.log.warn( json.dumps( json.loads( hosts ),
                                               sort_keys=True,
                                               indent=4,
                                               separators=( ',', ': ' ) ) )
                except ( ValueError, TypeError ):
                    main.log.warn( repr( hosts ) )
                hostResult = main.FALSE
        utilities.assert_equals( expect=main.TRUE, actual=hostResult,
                                 onpass="Found a host id for each host",
                                 onfail="Error looking up host ids" )

        intentStart = time.time()
        onosIds = main.ONOScli1.getAllIntentsId()
        main.log.info( "Submitted intents: " + str( intentIds ) )
        main.log.info( "Intents in ONOS: " + str( onosIds ) )
        for intent in intentIds:
            if intent in onosIds:
                pass  # intent submitted is in onos
            else:
                intentAddResult = False
        # FIXME: DEBUG
        if intentAddResult:
            intentStop = time.time()
        else:
            intentStop = None
        # Print the intent states
        intents = main.ONOScli1.intents()
        intentStates = []
        installedCheck = True
        main.log.info( "%-6s%-15s%-15s" % ( 'Count', 'ID', 'State' ) )
        count = 0
        try:
            for intent in json.loads( intents ):
                state = intent.get( 'state', None )
                if "INSTALLED" not in state:
                    installedCheck = False
                intentId = intent.get( 'id', None )
                intentStates.append( ( intentId, state ) )
        except ( ValueError, TypeError ):
            main.log.exception( "Error parsing intents" )
        # add submitted intents not in the store
        tmplist = [ i for i, s in intentStates ]
        missingIntents = False
        for i in intentIds:
            if i not in tmplist:
                intentStates.append( ( i, " - " ) )
                missingIntents = True
        intentStates.sort()
        for i, s in intentStates:
            count += 1
            main.log.info( "%-6s%-15s%-15s" %
                           ( str( count ), str( i ), str( s ) ) )
        leaders = main.ONOScli1.leaders()
        try:
            if leaders:
                parsedLeaders = json.loads( leaders )
                main.log.warn( json.dumps( parsedLeaders,
                                           sort_keys=True,
                                           indent=4,
                                           separators=( ',', ': ' ) ) )
                # check for all intent partitions
                topics = []
                for i in range( 14 ):
                    topics.append( "intent-partition-" + str( i ) )
                main.log.debug( topics )
                ONOStopics = [ j['topic'] for j in parsedLeaders ]
                for topic in topics:
                    if topic not in ONOStopics:
                        main.log.error( "Error: " + topic +
                                        " not in leaders" )
            else:
                main.log.error( "leaders() returned None" )
        except ( ValueError, TypeError ):
            main.log.exception( "Error parsing leaders" )
            main.log.error( repr( leaders ) )
        partitions = main.ONOScli1.partitions()
        try:
            if partitions :
                parsedPartitions = json.loads( partitions )
                main.log.warn( json.dumps( parsedPartitions,
                                           sort_keys=True,
                                           indent=4,
                                           separators=( ',', ': ' ) ) )
                # TODO check for a leader in all paritions
                # TODO check for consistency among nodes
            else:
                main.log.error( "partitions() returned None" )
        except ( ValueError, TypeError ):
            main.log.exception( "Error parsing partitions" )
            main.log.error( repr( partitions ) )
        pendingMap = main.ONOScli1.pendingMap()
        try:
            if pendingMap :
                parsedPending = json.loads( pendingMap )
                main.log.warn( json.dumps( parsedPending,
                                           sort_keys=True,
                                           indent=4,
                                           separators=( ',', ': ' ) ) )
                # TODO check something here?
            else:
                main.log.error( "pendingMap() returned None" )
        except ( ValueError, TypeError ):
            main.log.exception( "Error parsing pending map" )
            main.log.error( repr( pendingMap ) )

        intentAddResult = bool( intentAddResult and not missingIntents and
                                installedCheck )
        if not intentAddResult:
            main.log.error( "Error in pushing host intents to ONOS" )

        main.step( "Intent Anti-Entropy dispersion" )
        for i in range(100):
            correct = True
            main.log.info( "Submitted intents: " + str( sorted( intentIds ) ) )
            for cli in CLIs:
                onosIds = []
                ids = cli.getAllIntentsId()
                onosIds.append( ids )
                main.log.debug( "Intents in " + cli.name + ": " +
                                str( sorted( onosIds ) ) )
                if sorted( ids ) != sorted( intentIds ):
                    correct = False
            if correct:
                break
            else:
                time.sleep(1)
        if not intentStop:
            intentStop = time.time()
        global gossipTime
        gossipTime = intentStop - intentStart
        main.log.info( "It took about " + str( gossipTime ) +
                        " seconds for all intents to appear in each node" )
        # FIXME: make this time configurable/calculate based off of number of
        #        nodes and gossip rounds
        utilities.assert_greater_equals(
                expect=40, actual=gossipTime,
                onpass="ECM anti-entropy for intents worked within " +
                       "expected time",
                onfail="Intent ECM anti-entropy took too long" )
        if gossipTime <= 40:
            intentAddResult = True

        if not intentAddResult or "key" in pendingMap:
            import time
            installedCheck = True
            main.log.info( "Sleeping 60 seconds to see if intents are found" )
            time.sleep( 60 )
            onosIds = main.ONOScli1.getAllIntentsId()
            main.log.info( "Submitted intents: " + str( intentIds ) )
            main.log.info( "Intents in ONOS: " + str( onosIds ) )
            # Print the intent states
            intents = main.ONOScli1.intents()
            intentStates = []
            main.log.info( "%-6s%-15s%-15s" % ( 'Count', 'ID', 'State' ) )
            count = 0
            try:
                for intent in json.loads( intents ):
                    # Iter through intents of a node
                    state = intent.get( 'state', None )
                    if "INSTALLED" not in state:
                        installedCheck = False
                    intentId = intent.get( 'id', None )
                    intentStates.append( ( intentId, state ) )
            except ( ValueError, TypeError ):
                main.log.exception( "Error parsing intents" )
            # add submitted intents not in the store
            tmplist = [ i for i, s in intentStates ]
            for i in intentIds:
                if i not in tmplist:
                    intentStates.append( ( i, " - " ) )
            intentStates.sort()
            for i, s in intentStates:
                count += 1
                main.log.info( "%-6s%-15s%-15s" %
                               ( str( count ), str( i ), str( s ) ) )
            leaders = main.ONOScli1.leaders()
            try:
                if leaders:
                    parsedLeaders = json.loads( leaders )
                    main.log.warn( json.dumps( parsedLeaders,
                                               sort_keys=True,
                                               indent=4,
                                               separators=( ',', ': ' ) ) )
                    # check for all intent partitions
                    # check for election
                    topics = []
                    for i in range( 14 ):
                        topics.append( "intent-partition-" + str( i ) )
                    # FIXME: this should only be after we start the app
                    topics.append( "org.onosproject.election" )
                    main.log.debug( topics )
                    ONOStopics = [ j['topic'] for j in parsedLeaders ]
                    for topic in topics:
                        if topic not in ONOStopics:
                            main.log.error( "Error: " + topic +
                                            " not in leaders" )
                else:
                    main.log.error( "leaders() returned None" )
            except ( ValueError, TypeError ):
                main.log.exception( "Error parsing leaders" )
                main.log.error( repr( leaders ) )
            partitions = main.ONOScli1.partitions()
            try:
                if partitions :
                    parsedPartitions = json.loads( partitions )
                    main.log.warn( json.dumps( parsedPartitions,
                                               sort_keys=True,
                                               indent=4,
                                               separators=( ',', ': ' ) ) )
                    # TODO check for a leader in all paritions
                    # TODO check for consistency among nodes
                else:
                    main.log.error( "partitions() returned None" )
            except ( ValueError, TypeError ):
                main.log.exception( "Error parsing partitions" )
                main.log.error( repr( partitions ) )
            pendingMap = main.ONOScli1.pendingMap()
            try:
                if pendingMap :
                    parsedPending = json.loads( pendingMap )
                    main.log.warn( json.dumps( parsedPending,
                                               sort_keys=True,
                                               indent=4,
                                               separators=( ',', ': ' ) ) )
                    # TODO check something here?
                else:
                    main.log.error( "pendingMap() returned None" )
            except ( ValueError, TypeError ):
                main.log.exception( "Error parsing pending map" )
                main.log.error( repr( pendingMap ) )

    def CASE4( self, main ):
        """
        Ping across added host intents
        """
        import json
        import time
        assert numControllers, "numControllers not defined"
        assert main, "main not defined"
        assert utilities.assert_equals, "utilities.assert_equals not defined"
        main.case( "Verify connectivity by sendind traffic across Intents" )
        main.caseExplaination = "Ping across added host intents to check " +\
                                "functionality and check the state of " +\
                                "the intent"
        main.step( "Ping across added host intents" )
        PingResult = main.TRUE
        for i in range( 8, 18 ):
            ping = main.Mininet1.pingHost( src="h" + str( i ),
                                           target="h" + str( i + 10 ) )
            PingResult = PingResult and ping
            if ping == main.FALSE:
                main.log.warn( "Ping failed between h" + str( i ) +
                               " and h" + str( i + 10 ) )
            elif ping == main.TRUE:
                main.log.info( "Ping test passed!" )
                # Don't set PingResult or you'd override failures
        if PingResult == main.FALSE:
            main.log.error(
                "Intents have not been installed correctly, pings failed." )
            # TODO: pretty print
            main.log.warn( "ONOS1 intents: " )
            try:
                tmpIntents = main.ONOScli1.intents()
                main.log.warn( json.dumps( json.loads( tmpIntents ),
                                           sort_keys=True,
                                           indent=4,
                                           separators=( ',', ': ' ) ) )
            except ( ValueError, TypeError ):
                main.log.warn( repr( tmpIntents ) )
        utilities.assert_equals(
            expect=main.TRUE,
            actual=PingResult,
            onpass="Intents have been installed correctly and pings work",
            onfail="Intents have not been installed correctly, pings failed." )

        main.step( "Check Intent state" )
        installedCheck = True
        # Print the intent states
        intents = main.ONOScli1.intents()
        intentStates = []
        main.log.info( "%-6s%-15s%-15s" % ( 'Count', 'ID', 'State' ) )
        count = 0
        # Iter through intents of a node
        try:
            for intent in json.loads( intents ):
                state = intent.get( 'state', None )
                if "INSTALLED" not in state:
                    installedCheck = False
                intentId = intent.get( 'id', None )
                intentStates.append( ( intentId, state ) )
        except ( ValueError, TypeError ):
            main.log.exception( "Error parsing intents." )
        # Print states
        intentStates.sort()
        for i, s in intentStates:
            count += 1
            main.log.info( "%-6s%-15s%-15s" %
                           ( str( count ), str( i ), str( s ) ) )
        utilities.assert_equals( expect=True, actual=installedCheck,
                                 onpass="Intents are all INSTALLED",
                                 onfail="Intents are not all in " +
                                        "INSTALLED state" )

        main.step( "Check leadership of topics" )
        leaders = main.ONOScli1.leaders()
        topicCheck = main.TRUE
        try:
            if leaders:
                parsedLeaders = json.loads( leaders )
                main.log.warn( json.dumps( parsedLeaders,
                                           sort_keys=True,
                                           indent=4,
                                           separators=( ',', ': ' ) ) )
                # check for all intent partitions
                # check for election
                # TODO: Look at Devices as topics now that it uses this system
                topics = []
                for i in range( 14 ):
                    topics.append( "intent-partition-" + str( i ) )
                # FIXME: this should only be after we start the app
                # FIXME: topics.append( "org.onosproject.election" )
                # Print leaders output
                main.log.debug( topics )
                ONOStopics = [ j['topic'] for j in parsedLeaders ]
                for topic in topics:
                    if topic not in ONOStopics:
                        main.log.error( "Error: " + topic +
                                        " not in leaders" )
                        topicCheck = main.FALSE
            else:
                main.log.error( "leaders() returned None" )
                topicCheck = main.FALSE
        except ( ValueError, TypeError ):
            topicCheck = main.FALSE
            main.log.exception( "Error parsing leaders" )
            main.log.error( repr( leaders ) )
            # TODO: Check for a leader of these topics
        utilities.assert_equals( expect=main.TRUE, actual=topicCheck,
                                 onpass="intent Partitions is in leaders",
                                 onfail="Some topics were lost " )
        # Print partitions
        partitions = main.ONOScli1.partitions()
        try:
            if partitions :
                parsedPartitions = json.loads( partitions )
                main.log.warn( json.dumps( parsedPartitions,
                                           sort_keys=True,
                                           indent=4,
                                           separators=( ',', ': ' ) ) )
                # TODO check for a leader in all paritions
                # TODO check for consistency among nodes
            else:
                main.log.error( "partitions() returned None" )
        except ( ValueError, TypeError ):
            main.log.exception( "Error parsing partitions" )
            main.log.error( repr( partitions ) )
        # Print Pending Map
        pendingMap = main.ONOScli1.pendingMap()
        try:
            if pendingMap :
                parsedPending = json.loads( pendingMap )
                main.log.warn( json.dumps( parsedPending,
                                           sort_keys=True,
                                           indent=4,
                                           separators=( ',', ': ' ) ) )
                # TODO check something here?
            else:
                main.log.error( "pendingMap() returned None" )
        except ( ValueError, TypeError ):
            main.log.exception( "Error parsing pending map" )
            main.log.error( repr( pendingMap ) )

        if not installedCheck:
            main.log.info( "Waiting 60 seconds to see if the state of " +
                           "intents change" )
            time.sleep( 60 )
            # Print the intent states
            intents = main.ONOScli1.intents()
            intentStates = []
            main.log.info( "%-6s%-15s%-15s" % ( 'Count', 'ID', 'State' ) )
            count = 0
            # Iter through intents of a node
            try:
                for intent in json.loads( intents ):
                    state = intent.get( 'state', None )
                    if "INSTALLED" not in state:
                        installedCheck = False
                    intentId = intent.get( 'id', None )
                    intentStates.append( ( intentId, state ) )
            except ( ValueError, TypeError ):
                main.log.exception( "Error parsing intents." )
            intentStates.sort()
            for i, s in intentStates:
                count += 1
                main.log.info( "%-6s%-15s%-15s" %
                               ( str( count ), str( i ), str( s ) ) )
            leaders = main.ONOScli1.leaders()
            try:
                if leaders:
                    parsedLeaders = json.loads( leaders )
                    main.log.warn( json.dumps( parsedLeaders,
                                               sort_keys=True,
                                               indent=4,
                                               separators=( ',', ': ' ) ) )
                    # check for all intent partitions
                    # check for election
                    topics = []
                    for i in range( 14 ):
                        topics.append( "intent-partition-" + str( i ) )
                    # FIXME: this should only be after we start the app
                    topics.append( "org.onosproject.election" )
                    main.log.debug( topics )
                    ONOStopics = [ j['topic'] for j in parsedLeaders ]
                    for topic in topics:
                        if topic not in ONOStopics:
                            main.log.error( "Error: " + topic +
                                            " not in leaders" )
                else:
                    main.log.error( "leaders() returned None" )
            except ( ValueError, TypeError ):
                main.log.exception( "Error parsing leaders" )
                main.log.error( repr( leaders ) )
            partitions = main.ONOScli1.partitions()
            try:
                if partitions :
                    parsedPartitions = json.loads( partitions )
                    main.log.warn( json.dumps( parsedPartitions,
                                               sort_keys=True,
                                               indent=4,
                                               separators=( ',', ': ' ) ) )
                    # TODO check for a leader in all paritions
                    # TODO check for consistency among nodes
                else:
                    main.log.error( "partitions() returned None" )
            except ( ValueError, TypeError ):
                main.log.exception( "Error parsing partitions" )
                main.log.error( repr( partitions ) )
            pendingMap = main.ONOScli1.pendingMap()
            try:
                if pendingMap :
                    parsedPending = json.loads( pendingMap )
                    main.log.warn( json.dumps( parsedPending,
                                               sort_keys=True,
                                               indent=4,
                                               separators=( ',', ': ' ) ) )
                    # TODO check something here?
                else:
                    main.log.error( "pendingMap() returned None" )
            except ( ValueError, TypeError ):
                main.log.exception( "Error parsing pending map" )
                main.log.error( repr( pendingMap ) )
        # Print flowrules
        main.log.debug( CLIs[0].flows( jsonFormat=False ) )
        main.step( "Wait a minute then ping again" )
        # the wait is above
        PingResult = main.TRUE
        for i in range( 8, 18 ):
            ping = main.Mininet1.pingHost( src="h" + str( i ),
                                           target="h" + str( i + 10 ) )
            PingResult = PingResult and ping
            if ping == main.FALSE:
                main.log.warn( "Ping failed between h" + str( i ) +
                               " and h" + str( i + 10 ) )
            elif ping == main.TRUE:
                main.log.info( "Ping test passed!" )
                # Don't set PingResult or you'd override failures
        if PingResult == main.FALSE:
            main.log.error(
                "Intents have not been installed correctly, pings failed." )
            # TODO: pretty print
            main.log.warn( "ONOS1 intents: " )
            try:
                tmpIntents = main.ONOScli1.intents()
                main.log.warn( json.dumps( json.loads( tmpIntents ),
                                           sort_keys=True,
                                           indent=4,
                                           separators=( ',', ': ' ) ) )
            except ( ValueError, TypeError ):
                main.log.warn( repr( tmpIntents ) )
        utilities.assert_equals(
            expect=main.TRUE,
            actual=PingResult,
            onpass="Intents have been installed correctly and pings work",
            onfail="Intents have not been installed correctly, pings failed." )

    def CASE5( self, main ):
        """
        Reading state of ONOS
        """
        import json
        assert numControllers, "numControllers not defined"
        assert main, "main not defined"
        assert utilities.assert_equals, "utilities.assert_equals not defined"
        # assumes that sts is already in you PYTHONPATH
        from sts.topology.teston_topology import TestONTopology

        main.case( "Setting up and gathering data for current state" )
        # The general idea for this test case is to pull the state of
        # ( intents,flows, topology,... ) from each ONOS node
        # We can then compare them with each other and also with past states

        main.step( "Check that each switch has a master" )
        global mastershipState
        mastershipState = '[]'

        # Assert that each device has a master
        rolesNotNull = main.ONOScli1.rolesNotNull()
        utilities.assert_equals(
            expect=main.TRUE,
            actual=rolesNotNull,
            onpass="Each device has a master",
            onfail="Some devices don't have a master assigned" )

        main.step( "Get the Mastership of each switch" )
        ONOS1Mastership = main.ONOScli1.roles()
        # TODO: Make this a meaningful check
        if "Error" in ONOS1Mastership or not ONOS1Mastership:
            main.log.error( "Error in getting ONOS roles" )
            main.log.warn(
                "ONOS1 mastership response: " +
                repr( ONOS1Mastership ) )
            consistentMastership = main.FALSE
        else:
            mastershipState = ONOS1Mastership
            consistentMastership = main.TRUE

        main.step( "Get the intents from each controller" )
        global intentState
        intentState = []
        ONOS1Intents = main.ONOScli1.intents( jsonFormat=True )
        intentCheck = main.FALSE
        if "Error" in ONOS1Intents or not ONOS1Intents:
            main.log.error( "Error in getting ONOS intents" )
            main.log.warn( "ONOS1 intents response: " + repr( ONOS1Intents ) )
        else:
            intentCheck = main.TRUE

        main.step( "Get the flows from each controller" )
        global flowState
        flowState = []
        flowCheck = main.FALSE
        ONOS1Flows = main.ONOScli1.flows( jsonFormat=True )
        if "Error" in ONOS1Flows or not ONOS1Flows:
            main.log.error( "Error in getting ONOS flows" )
            main.log.warn( "ONOS1 flows repsponse: " + ONOS1Flows )
        else:
            # TODO: Do a better check, maybe compare flows on switches?
            flowState = ONOS1Flows
            flowCheck = main.TRUE

        main.step( "Get the OF Table entries" )
        global flows
        flows = []
        for i in range( 1, 29 ):
            flows.append( main.Mininet2.getFlowTable( 1.3, "s" + str( i ) ) )
        if flowCheck == main.FALSE:
            for table in flows:
                main.log.warn( table )
        # TODO: Compare switch flow tables with ONOS flow tables

        main.step( "Create TestONTopology object" )
        ctrls = []
        temp = ( nodes[0], nodes[0].name, nodes[0].ip_address, 6633 )
        ctrls.append( temp )
        MNTopo = TestONTopology( main.Mininet1, ctrls )

        main.step( "Collecting topology information from ONOS" )
        devices = []
        devices.append( main.ONOScli1.devices() )
        hosts = []
        hosts.append( json.loads( main.ONOScli1.hosts() ) )
        ports = []
        ports.append( main.ONOScli1.ports() )
        links = []
        links.append( main.ONOScli1.links() )
        clusters = []
        clusters.append( main.ONOScli1.clusters() )

        main.step( "Each host has an IP address" )
        ipResult = main.TRUE
        for controller in range( 0, len( hosts ) ):
            controllerStr = str( controller + 1 )
            for host in hosts[ controller ]:
                if host is None or host.get( 'ipAddresses', [] ) == []:
                    main.log.error(
                        "DEBUG:Error with host ips on controller" +
                        controllerStr + ": " + str( host ) )
                    ipResult = main.FALSE
        utilities.assert_equals(
            expect=main.TRUE,
            actual=ipResult,
            onpass="The ips of the hosts aren't empty",
            onfail="The ip of at least one host is missing" )

        # there should always only be one cluster
        main.step( "There is only one dataplane cluster" )
        try:
            numClusters = len( json.loads( clusters[ 0 ] ) )
        except ( ValueError, TypeError ):
            main.log.exception( "Error parsing clusters[0]: " +
                                repr( clusters[ 0 ] ) )
        clusterResults = main.FALSE
        if numClusters == 1:
            clusterResults = main.TRUE
        utilities.assert_equals(
            expect=1,
            actual=numClusters,
            onpass="ONOS shows 1 SCC",
            onfail="ONOS shows " + str( numClusters ) + " SCCs" )

        main.step( "Comparing ONOS topology to MN" )
        devicesResults = main.TRUE
        portsResults = main.TRUE
        linksResults = main.TRUE
        hostsResults = main.TRUE
        for controller in range( numControllers ):
            controllerStr = str( controller + 1 )
            if devices[ controller ] or "Error" not in devices[ controller ]:
                currentDevicesResult = main.Mininet1.compareSwitches(
                    MNTopo,
                    json.loads( devices[ controller ] ) )
            else:
                currentDevicesResult = main.FALSE
            utilities.assert_equals( expect=main.TRUE,
                                     actual=currentDevicesResult,
                                     onpass="ONOS" + controllerStr +
                                     " Switches view is correct",
                                     onfail="ONOS" + controllerStr +
                                     " Switches view is incorrect" )

            if ports[ controller ] or "Error" not in ports[ controller ]:
                currentPortsResult = main.Mininet1.comparePorts(
                    MNTopo,
                    json.loads( ports[ controller ] ) )
            else:
                currentPortsResult = main.FALSE
            utilities.assert_equals( expect=main.TRUE,
                                     actual=currentPortsResult,
                                     onpass="ONOS" + controllerStr +
                                     " ports view is correct",
                                     onfail="ONOS" + controllerStr +
                                     " ports view is incorrect" )

            if links[ controller ] or "Error" not in links[ controller ]:
                currentLinksResult = main.Mininet1.compareLinks(
                    MNTopo,
                    json.loads( links[ controller ] ) )
            else:
                currentLinksResult = main.FALSE
            utilities.assert_equals( expect=main.TRUE,
                                     actual=currentLinksResult,
                                     onpass="ONOS" + controllerStr +
                                     " links view is correct",
                                     onfail="ONOS" + controllerStr +
                                     " links view is incorrect" )

            if hosts[ controller ] or "Error" not in hosts[ controller ]:
                currentHostsResult = main.Mininet1.compareHosts(
                    MNTopo, hosts[ controller ] )
            else:
                currentHostsResult = main.FALSE
            utilities.assert_equals( expect=main.TRUE,
                                     actual=currentHostsResult,
                                     onpass="ONOS" + controllerStr +
                                     " hosts exist in Mininet",
                                     onfail="ONOS" + controllerStr +
                                     " hosts don't match Mininet" )

            devicesResults = devicesResults and currentDevicesResult
            portsResults = portsResults and currentPortsResult
            linksResults = linksResults and currentLinksResult
            hostsResults = hostsResults and currentHostsResult

        topoResult = devicesResults and portsResults and linksResults\
                     and clusterResults and ipResult and hostsResults
        utilities.assert_equals( expect=main.TRUE, actual=topoResult,
                                 onpass="Topology Check Test successful",
                                 onfail="Topology Check Test NOT successful" )

    def CASE6( self, main ):
        """
        The Failure case.
        """
        import time
        assert numControllers, "numControllers not defined"
        assert main, "main not defined"
        assert utilities.assert_equals, "utilities.assert_equals not defined"

        # Reset non-persistent variables
        try:
            iCounterValue = 0
        except NameError:
            main.log.error( "iCounterValue not defined, setting to 0" )
            iCounterValue = 0

        main.case( "Restart ONOS node" )
        main.caseExplaination = "Killing ONOS process and restart cli " +\
                                "sessions once onos is up."
        main.step( "Killing ONOS processes" )
        killResult = main.ONOSbench.onosKill( ONOS1Ip )
        start = time.time()
        utilities.assert_equals( expect=main.TRUE, actual=killResult,
                                 onpass="ONOS Killed",
                                 onfail="Error killing ONOS" )

        main.step( "Checking if ONOS is up yet" )
        count = 0
        while count < 10:
            onos1Isup = main.ONOSbench.isup( ONOS1Ip )
            if onos1Isup == main.TRUE:
                elapsed = time.time() - start
                break
            else:
                count = count + 1
        utilities.assert_equals( expect=main.TRUE, actual=onos1Isup,
                                 onpass="ONOS is back up",
                                 onfail="ONOS failed to start" )

        main.log.step( "Starting ONOS CLI sessions" )
        cliResults = main.ONOScli1.startOnosCli( ONOS1Ip )
        utilities.assert_equals( expect=main.TRUE, actual=cliResults,
                                 onpass="ONOS cli startup successful",
                                 onfail="ONOS cli startup failed" )

        if elapsed:
            main.log.info( "ESTIMATE: ONOS took %s seconds to restart" %
                           str( elapsed ) )
            main.restartTime = elapsed
        else:
            main.restartTime = -1
        time.sleep( 5 )
        # rerun on election apps
        main.ONOScli1.electionTestRun()

    def CASE7( self, main ):
        """
        Check state after ONOS failure
        """
        import json
        assert numControllers, "numControllers not defined"
        assert main, "main not defined"
        assert utilities.assert_equals, "utilities.assert_equals not defined"
        main.case( "Running ONOS Constant State Tests" )
        main.step( "Check that each switch has a master" )
        # Assert that each device has a master
        rolesNotNull = main.ONOScli1.rolesNotNull()
        utilities.assert_equals(
            expect=main.TRUE,
            actual=rolesNotNull,
            onpass="Each device has a master",
            onfail="Some devices don't have a master assigned" )

        main.step( "Check if switch roles are consistent across all nodes" )
        ONOS1Mastership = main.ONOScli1.roles()
        # FIXME: Refactor this whole case for single instance
        if "Error" in ONOS1Mastership or not ONOS1Mastership:
            main.log.error( "Error in getting ONOS mastership" )
            main.log.warn( "ONOS1 mastership response: " +
                           repr( ONOS1Mastership ) )
            consistentMastership = main.FALSE
        else:
            consistentMastership = main.TRUE
        utilities.assert_equals(
            expect=main.TRUE,
            actual=consistentMastership,
            onpass="Switch roles are consistent across all ONOS nodes",
            onfail="ONOS nodes have different views of switch roles" )

        description2 = "Compare switch roles from before failure"
        main.step( description2 )

        currentJson = json.loads( ONOS1Mastership )
        oldJson = json.loads( mastershipState )
        mastershipCheck = main.TRUE
        for i in range( 1, 29 ):
            switchDPID = str(
                main.Mininet1.getSwitchDPID( switch="s" + str( i ) ) )

            current = [ switch[ 'master' ] for switch in currentJson
                        if switchDPID in switch[ 'id' ] ]
            old = [ switch[ 'master' ] for switch in oldJson
                    if switchDPID in switch[ 'id' ] ]
            if current == old:
                mastershipCheck = mastershipCheck and main.TRUE
            else:
                main.log.warn( "Mastership of switch %s changed" % switchDPID )
                mastershipCheck = main.FALSE
        utilities.assert_equals(
            expect=main.TRUE,
            actual=mastershipCheck,
            onpass="Mastership of Switches was not changed",
            onfail="Mastership of some switches changed" )
        mastershipCheck = mastershipCheck and consistentMastership

        main.step( "Get the intents and compare across all nodes" )
        ONOS1Intents = main.ONOScli1.intents( jsonFormat=True )
        intentCheck = main.FALSE
        if "Error" in ONOS1Intents or not ONOS1Intents:
            main.log.error( "Error in getting ONOS intents" )
            main.log.warn( "ONOS1 intents response: " + repr( ONOS1Intents ) )
        else:
            intentCheck = main.TRUE
            main.log.error( "Intents are consistent across all ONOS nodes" )
        utilities.assert_equals(
            expect=main.TRUE,
            actual=intentCheck,
            onpass="Intents are consistent across all ONOS nodes",
            onfail="ONOS nodes have different views of intents" )
        # Print the intent states
        intents = []
        intents.append( ONOS1Intents )
        intentStates = []
        for node in intents:  # Iter through ONOS nodes
            nodeStates = []
            # Iter through intents of a node
            for intent in json.loads( node ):
                nodeStates.append( intent[ 'state' ] )
            intentStates.append( nodeStates )
            out = [ (i, nodeStates.count( i ) ) for i in set( nodeStates ) ]
            main.log.info( dict( out ) )

        # NOTE: Store has no durability, so intents are lost across system
        #       restarts
        """
        main.step( "Compare current intents with intents before the failure" )
        # NOTE: this requires case 5 to pass for intentState to be set.
        #      maybe we should stop the test if that fails?
        sameIntents = main.FALSE
        if intentState and intentState == ONOSIntents[ 0 ]:
            sameIntents = main.TRUE
            main.log.info( "Intents are consistent with before failure" )
        # TODO: possibly the states have changed? we may need to figure out
        #       what the acceptable states are
        elif len( intentState ) == len( ONOSIntents[ 0 ] ):
            sameIntents = main.TRUE
            try:
                before = json.loads( intentState )
                after = json.loads( ONOSIntents[ 0 ] )
                for intent in before:
                    if intent not in after:
                        sameIntents = main.FALSE
                        main.log.debug( "Intent is not currently in ONOS " +
                                        "(at least in the same form):" )
                        main.log.debug( json.dumps( intent ) )
            except ( ValueError, TypeError ):
                main.log.exception( "Exception printing intents" )
                main.log.debug( repr( ONOSIntents[0] ) )
                main.log.debug( repr( intentState ) )
        if sameIntents == main.FALSE:
            try:
                main.log.debug( "ONOS intents before: " )
                main.log.debug( json.dumps( json.loads( intentState ),
                                            sort_keys=True, indent=4,
                                            separators=( ',', ': ' ) ) )
                main.log.debug( "Current ONOS intents: " )
                main.log.debug( json.dumps( json.loads( ONOSIntents[ 0 ] ),
                                            sort_keys=True, indent=4,
                                            separators=( ',', ': ' ) ) )
            except ( ValueError, TypeError ):
                main.log.exception( "Exception printing intents" )
                main.log.debug( repr( ONOSIntents[0] ) )
                main.log.debug( repr( intentState ) )
        utilities.assert_equals(
            expect=main.TRUE,
            actual=sameIntents,
            onpass="Intents are consistent with before failure",
            onfail="The Intents changed during failure" )
        intentCheck = intentCheck and sameIntents
        """
        main.step( "Get the OF Table entries and compare to before " +
                   "component failure" )
        FlowTables = main.TRUE
        flows2 = []
        for i in range( 28 ):
            main.log.info( "Checking flow table on s" + str( i + 1 ) )
            tmpFlows = main.Mininet2.getFlowTable( 1.3, "s" + str( i + 1 ) )
            flows2.append( tmpFlows )
            tempResult = main.Mininet2.flowComp(
                flow1=flows[ i ],
                flow2=tmpFlows )
            FlowTables = FlowTables and tempResult
            if FlowTables == main.FALSE:
                main.log.info( "Differences in flow table for switch: s" +
                               str( i + 1 ) )
        utilities.assert_equals(
            expect=main.TRUE,
            actual=FlowTables,
            onpass="No changes were found in the flow tables",
            onfail="Changes were found in the flow tables" )

        main.step( "Leadership Election is still functional" )
        # Test of LeadershipElection

        leader = ONOS1Ip
        leaderResult = main.TRUE
        for controller in range( 1, numControllers + 1 ):
            # loop through ONOScli handlers
            node = getattr( main, ( 'ONOScli' + str( controller ) ) )
            leaderN = node.electionTestLeader()
            # verify leader is ONOS1
            # NOTE even though we restarted ONOS, it is the only one so onos 1
            # must be leader
            if leaderN == leader:
                # all is well
                pass
            elif leaderN == main.FALSE:
                # error in response
                main.log.error( "Something is wrong with " +
                                 "electionTestLeader function, check the" +
                                 " error logs" )
                leaderResult = main.FALSE
            elif leader != leaderN:
                leaderResult = main.FALSE
                main.log.error( "ONOS" + str( controller ) + " sees " +
                                 str( leaderN ) +
                                 " as the leader of the election app. " +
                                 "Leader should be " + str( leader ) )
        utilities.assert_equals(
            expect=main.TRUE,
            actual=leaderResult,
            onpass="Leadership election passed",
            onfail="Something went wrong with Leadership election" )

    def CASE8( self, main ):
        """
        Compare topo
        """
        import sys
        # FIXME add this path to params
        sys.path.append( "/home/admin/sts" )
        # assumes that sts is already in you PYTHONPATH
        from sts.topology.teston_topology import TestONTopology
        import json
        import time
        assert numControllers, "numControllers not defined"
        assert main, "main not defined"
        assert utilities.assert_equals, "utilities.assert_equals not defined"

        main.case( "Compare ONOS Topology view to Mininet topology" )
        main.caseExplaination = "Compare topology objects between Mininet" +\
                                " and ONOS"
        main.step( "Create TestONTopology object" )
        try:
            ctrls = []
            node = main.ONOS1
            temp = ( node, node.name, node.ip_address, 6633 )
            ctrls.append( temp )
            MNTopo = TestONTopology( main.Mininet1, ctrls )
        except Exception:
            objResult = main.FALSE
        else:
            objResult = main.TRUE
        utilities.assert_equals( expect=main.TRUE, actual=objResult,
                                 onpass="Created TestONTopology object",
                                 onfail="Exception while creating " +
                                        "TestONTopology object" )

        main.step( "Comparing ONOS topology to MN" )
        devicesResults = main.TRUE
        portsResults = main.TRUE
        linksResults = main.TRUE
        hostsResults = main.TRUE
        topoResult = main.FALSE
        elapsed = 0
        count = 0
        main.step( "Collecting topology information from ONOS" )
        startTime = time.time()
        # Give time for Gossip to work
        while topoResult == main.FALSE and elapsed < 60:
            count += 1
            if count > 1:
                # TODO: Deprecate STS usage
                MNTopo = TestONTopology( main.Mininet1, ctrls )
            cliStart = time.time()
            devices = []
            devices.append( main.ONOScli1.devices() )
            hosts = []
            hosts.append( json.loads( main.ONOScli1.hosts() ) )
            ipResult = main.TRUE
            for controller in range( 0, len( hosts ) ):
                controllerStr = str( controller + 1 )
                for host in hosts[ controller ]:
                    if host is None or host.get( 'ipAddresses', [] ) == []:
                        main.log.error(
                            "DEBUG:Error with host ips on controller" +
                            controllerStr + ": " + str( host ) )
                        ipResult = main.FALSE
            ports = []
            ports.append( main.ONOScli1.ports() )
            links = []
            links.append( main.ONOScli1.links() )
            clusters = []
            clusters.append( main.ONOScli1.clusters() )

            elapsed = time.time() - startTime
            cliTime = time.time() - cliStart
            print "CLI time: " + str( cliTime )

            for controller in range( numControllers ):
                controllerStr = str( controller + 1 )
                if devices[ controller ] or "Error" not in devices[
                        controller ]:
                    currentDevicesResult = main.Mininet1.compareSwitches(
                        MNTopo,
                        json.loads( devices[ controller ] ) )
                else:
                    currentDevicesResult = main.FALSE
                utilities.assert_equals( expect=main.TRUE,
                                         actual=currentDevicesResult,
                                         onpass="ONOS" + controllerStr +
                                         " Switches view is correct",
                                         onfail="ONOS" + controllerStr +
                                         " Switches view is incorrect" )

                if ports[ controller ] or "Error" not in ports[ controller ]:
                    currentPortsResult = main.Mininet1.comparePorts(
                        MNTopo,
                        json.loads( ports[ controller ] ) )
                else:
                    currentPortsResult = main.FALSE
                utilities.assert_equals( expect=main.TRUE,
                                         actual=currentPortsResult,
                                         onpass="ONOS" + controllerStr +
                                         " ports view is correct",
                                         onfail="ONOS" + controllerStr +
                                         " ports view is incorrect" )

                if links[ controller ] or "Error" not in links[ controller ]:
                    currentLinksResult = main.Mininet1.compareLinks(
                        MNTopo,
                        json.loads( links[ controller ] ) )
                else:
                    currentLinksResult = main.FALSE
                utilities.assert_equals( expect=main.TRUE,
                                         actual=currentLinksResult,
                                         onpass="ONOS" + controllerStr +
                                         " links view is correct",
                                         onfail="ONOS" + controllerStr +
                                         " links view is incorrect" )

                if hosts[ controller ] or "Error" not in hosts[ controller ]:
                    currentHostsResult = main.Mininet1.compareHosts(
                        MNTopo, hosts[ controller ] )
                else:
                    currentHostsResult = main.FALSE
                utilities.assert_equals( expect=main.TRUE,
                                         actual=currentHostsResult,
                                         onpass="ONOS" + controllerStr +
                                         " hosts exist in Mininet",
                                         onfail="ONOS" + controllerStr +
                                         " hosts don't match Mininet" )

                devicesResults = devicesResults and currentDevicesResult
                portsResults = portsResults and currentPortsResult
                linksResults = linksResults and currentLinksResult
                hostsResults = hostsResults and currentHostsResult

                # "consistent" results don't make sense for single instance
            # there should always only be one cluster
            numClusters = len( json.loads( clusters[ 0 ] ) )
            clusterResults = main.FALSE
            if numClusters == 1:
                clusterResults = main.TRUE
            utilities.assert_equals(
                expect=1,
                actual=numClusters,
                onpass="ONOS shows 1 SCC",
                onfail="ONOS shows " + str( numClusters ) + " SCCs" )

            topoResult = ( devicesResults and portsResults and linksResults
                           and hostsResults and ipResult and clusterResults )

        topoResult = topoResult and int( count <= 2 )
        note = "note it takes about " + str( int( cliTime ) ) + \
            " seconds for the test to make all the cli calls to fetch " +\
            "the topology from each ONOS instance"
        main.log.info(
            "Very crass estimate for topology discovery/convergence( " +
            str( note ) + " ): " + str( elapsed ) + " seconds, " +
            str( count ) + " tries" )
        utilities.assert_equals( expect=main.TRUE, actual=topoResult,
                                 onpass="Topology Check Test successful",
                                 onfail="Topology Check Test NOT successful" )

    def CASE9( self, main ):
        """
        Link s3-s28 down
        """
        import time
        assert numControllers, "numControllers not defined"
        assert main, "main not defined"
        assert utilities.assert_equals, "utilities.assert_equals not defined"
        # NOTE: You should probably run a topology check after this

        linkSleep = float( main.params[ 'timers' ][ 'LinkDiscovery' ] )

        description = "Turn off a link to ensure that Link Discovery " +\
                      "is working properly"
        main.case( description )

        main.step( "Kill Link between s3 and s28" )
        LinkDown = main.Mininet1.link( END1="s3", END2="s28", OPTION="down" )
        main.log.info( "Waiting " + str( linkSleep ) +
                       " seconds for link down to be discovered" )
        time.sleep( linkSleep )
        utilities.assert_equals( expect=main.TRUE, actual=LinkDown,
                                 onpass="Link down successful",
                                 onfail="Failed to bring link down" )
        # TODO do some sort of check here

    def CASE10( self, main ):
        """
        Link s3-s28 up
        """
        import time
        assert numControllers, "numControllers not defined"
        assert main, "main not defined"
        assert utilities.assert_equals, "utilities.assert_equals not defined"
        # NOTE: You should probably run a topology check after this

        linkSleep = float( main.params[ 'timers' ][ 'LinkDiscovery' ] )

        description = "Restore a link to ensure that Link Discovery is " + \
                      "working properly"
        main.case( description )

        main.step( "Bring link between s3 and s28 back up" )
        LinkUp = main.Mininet1.link( END1="s3", END2="s28", OPTION="up" )
        main.log.info( "Waiting " + str( linkSleep ) +
                       " seconds for link up to be discovered" )
        time.sleep( linkSleep )
        utilities.assert_equals( expect=main.TRUE, actual=LinkUp,
                                 onpass="Link up successful",
                                 onfail="Failed to bring link up" )
        # TODO do some sort of check here

    def CASE11( self, main ):
        """
        Switch Down
        """
        # NOTE: You should probably run a topology check after this
        import time
        assert numControllers, "numControllers not defined"
        assert main, "main not defined"
        assert utilities.assert_equals, "utilities.assert_equals not defined"

        switchSleep = float( main.params[ 'timers' ][ 'SwitchDiscovery' ] )

        description = "Killing a switch to ensure it is discovered correctly"
        main.case( description )
        switch = main.params[ 'kill' ][ 'switch' ]
        switchDPID = main.params[ 'kill' ][ 'dpid' ]

        # TODO: Make this switch parameterizable
        main.step( "Kill " + switch )
        main.log.info( "Deleting " + switch )
        main.Mininet1.delSwitch( switch )
        main.log.info( "Waiting " + str( switchSleep ) +
                       " seconds for switch down to be discovered" )
        time.sleep( switchSleep )
        device = main.ONOScli1.getDevice( dpid=switchDPID )
        # Peek at the deleted switch
        main.log.warn( str( device ) )
        result = main.FALSE
        if device and device[ 'available' ] is False:
            result = main.TRUE
        utilities.assert_equals( expect=main.TRUE, actual=result,
                                 onpass="Kill switch successful",
                                 onfail="Failed to kill switch?" )

    def CASE12( self, main ):
        """
        Switch Up
        """
        # NOTE: You should probably run a topology check after this
        import time
        assert numControllers, "numControllers not defined"
        assert main, "main not defined"
        assert utilities.assert_equals, "utilities.assert_equals not defined"
        assert ONOS1Port, "ONOS1Port not defined"
        assert ONOS2Port, "ONOS2Port not defined"
        assert ONOS3Port, "ONOS3Port not defined"
        assert ONOS4Port, "ONOS4Port not defined"
        assert ONOS5Port, "ONOS5Port not defined"
        assert ONOS6Port, "ONOS6Port not defined"
        assert ONOS7Port, "ONOS7Port not defined"

        switchSleep = float( main.params[ 'timers' ][ 'SwitchDiscovery' ] )
        switch = main.params[ 'kill' ][ 'switch' ]
        switchDPID = main.params[ 'kill' ][ 'dpid' ]
        links = main.params[ 'kill' ][ 'links' ].split()
        description = "Adding a switch to ensure it is discovered correctly"
        main.case( description )

        main.step( "Add back " + switch )
        main.Mininet1.addSwitch( switch, dpid=switchDPID )
        for peer in links:
            main.Mininet1.addLink( switch, peer )
        main.Mininet1.assignSwController( sw=switch.split( 's' )[ 1 ],
                                          ip1=ONOS1Ip,
                                          port1=ONOS1Port )
        main.log.info( "Waiting " + str( switchSleep ) +
                       " seconds for switch up to be discovered" )
        time.sleep( switchSleep )
        device = main.ONOScli1.getDevice( dpid=switchDPID )
        # Peek at the deleted switch
        main.log.warn( str( device ) )
        result = main.FALSE
        if device and device[ 'available' ]:
            result = main.TRUE
        utilities.assert_equals( expect=main.TRUE, actual=result,
                                 onpass="add switch successful",
                                 onfail="Failed to add switch?" )

    def CASE13( self, main ):
        """
        Clean up
        """
        import os
        import time
        assert numControllers, "numControllers not defined"
        assert main, "main not defined"
        assert utilities.assert_equals, "utilities.assert_equals not defined"
        # printing colors to terminal
        colors = { 'cyan': '\033[96m', 'purple': '\033[95m',
                   'blue': '\033[94m', 'green': '\033[92m',
                   'yellow': '\033[93m', 'red': '\033[91m', 'end': '\033[0m' }
        main.case( "Test Cleanup" )
        main.step( "Killing tcpdumps" )
        main.Mininet2.stopTcpdump()

        main.step( "Copying MN pcap and ONOS log files to test station" )
        testname = main.TEST
        teststationUser = main.params[ 'TESTONUSER' ]
        teststationIP = main.params[ 'TESTONIP' ]
        # NOTE: MN Pcap file is being saved to ~/packet_captures
        #       scp this file as MN and TestON aren't necessarily the same vm
        # FIXME: scp
        # mn files
        # TODO: Load these from params
        # NOTE: must end in /
        logFolder = "/opt/onos/log/"
        logFiles = [ "karaf.log", "karaf.log.1" ]
        # NOTE: must end in /
        dstDir = "~/packet_captures/"
        for f in logFiles:
            main.ONOSbench.handle.sendline( "scp sdn@" + ONOS1Ip + ":" +
                                            logFolder + f + " " +
                                            teststationUser + "@" +
                                            teststationIP + ":" + dstDir +
                                            str( testname ) + "-ONOS1-" + f )
            main.ONOSbench.handle.expect( "\$" )

        # std*.log's
        # NOTE: must end in /
        logFolder = "/opt/onos/var/"
        logFiles = [ "stderr.log", "stdout.log" ]
        # NOTE: must end in /
        dstDir = "~/packet_captures/"
        for f in logFiles:
            main.ONOSbench.handle.sendline( "scp sdn@" + ONOS1Ip + ":" +
                                            logFolder + f + " " +
                                            teststationUser + "@" +
                                            teststationIP + ":" + dstDir +
                                            str( testname ) + "-ONOS1-" + f )
            main.ONOSbench.handle.expect( "\$" )
        # sleep so scp can finish
        time.sleep( 10 )

        main.step( "Stopping Mininet" )
        mnResult = main.Mininet1.stopNet()
        utilities.assert_equals( expect=main.TRUE, actual=mnResult,
                                 onpass="Mininet stopped",
                                 onfail="MN cleanup NOT successful" )

        main.step( "Checking ONOS Logs for errors" )
        print colors[ 'purple' ] + "Checking logs for errors on ONOS1:" + \
            colors[ 'end' ]
        print main.ONOSbench.checkLogs( ONOS1Ip, restart=True )

        main.step( "Packing and rotating pcap archives" )
        os.system( "~/TestON/dependencies/rotate.sh " + str( testname ) )

        try:
            timerLog = open( main.logdir + "/Timers.csv", 'w')
            # Overwrite with empty line and close
            labels = "Gossip Intents, Restart"
            data = str( gossipTime ) + ", " + str( main.restartTime )
            timerLog.write( labels + "\n" + data )
            timerLog.close()
        except NameError, e:
            main.log.exception(e)

    def CASE14( self, main ):
        """
        start election app on all onos nodes
        """
        assert numControllers, "numControllers not defined"
        assert main, "main not defined"
        assert utilities.assert_equals, "utilities.assert_equals not defined"

        main.case("Start Leadership Election app")
        main.step( "Install leadership election app" )
        appResult = main.ONOScli1.activateApp( "org.onosproject.election" )
        utilities.assert_equals(
            expect=main.TRUE,
            actual=appResult,
            onpass="Election app installed",
            onfail="Something went wrong with installing Leadership election" )

        main.step( "Run for election on each node" )
        leaderResult = main.ONOScli1.electionTestRun()
        # check for leader
        leader = main.ONOScli1.electionTestLeader()
        # verify leader is ONOS1
        if leader == ONOS1Ip:
            # all is well
            pass
        elif leader is None:
            # No leader elected
            main.log.error( "No leader was elected" )
            leaderResult = main.FALSE
        elif leader == main.FALSE:
            # error in  response
            # TODO: add check for "Command not found:" in the driver, this
            # means the app isn't loaded
            main.log.error( "Something is wrong with electionTestLeader" +
                             " function, check the error logs" )
            leaderResult = main.FALSE
        else:
            # error in  response
            main.log.error(
                "Unexpected response from electionTestLeader function:'" +
                str( leader ) +
                "'" )
            leaderResult = main.FALSE
        utilities.assert_equals(
            expect=main.TRUE,
            actual=leaderResult,
            onpass="Successfully ran for leadership",
            onfail="Failed to run for leadership" )

    def CASE15( self, main ):
        """
        Check that Leadership Election is still functional
        """
        assert numControllers, "numControllers not defined"
        assert main, "main not defined"
        assert utilities.assert_equals, "utilities.assert_equals not defined"
        leaderResult = main.TRUE
        description = "Check that Leadership Election is still functional"
        main.case( description )
        main.step( "Find current leader and withdraw" )
        leader = main.ONOScli1.electionTestLeader()
        # do some sanity checking on leader before using it
        withdrawResult = main.FALSE
        if leader == ONOS1Ip:
            oldLeader = getattr( main, "ONOScli1" )
        elif leader is None or leader == main.FALSE:
            main.log.error(
                "Leader for the election app should be an ONOS node," +
                "instead got '" + str( leader ) + "'" )
            leaderResult = main.FALSE
            oldLeader = None
        else:
            main.log.error( "Leader election --- why am I HERE?!?")
            leaderResult = main.FALSE
            oldLeader = None
        if oldLeader:
            withdrawResult = oldLeader.electionTestWithdraw()
        utilities.assert_equals(
            expect=main.TRUE,
            actual=withdrawResult,
            onpass="Node was withdrawn from election",
            onfail="Node was not withdrawn from election" )

        main.step( "Make sure new leader is elected" )
        leaderN = main.ONOScli1.electionTestLeader()
        if leaderN == leader:
            main.log.error( "ONOS still sees " + str( leaderN ) +
                             " as leader after they withdrew" )
            leaderResult = main.FALSE
        elif leaderN == main.FALSE:
            # error in  response
            # TODO: add check for "Command not found:" in the driver, this
            # means the app isn't loaded
            main.log.error( "Something is wrong with electionTestLeader " +
                             "function, check the error logs" )
            leaderResult = main.FALSE
        elif leaderN is None:
            main.log.info(
                "There is no leader after the app withdrew from election" )
            leaderResult = main.TRUE
        utilities.assert_equals(
            expect=main.TRUE,
            actual=leaderResult,
            onpass="Leadership election passed",
            onfail="Something went wrong with Leadership election" )

        main.step( "Run for election on old leader( just so everyone " +
                   "is in the hat )" )
        if oldLeader:
            runResult = oldLeader.electionTestRun()
        else:
            runResult = main.FALSE
        utilities.assert_equals(
            expect=main.TRUE,
            actual=runResult,
            onpass="App re-ran for election",
            onfail="App failed to run for election" )

        main.step( "Node became leader when it ran for election" )
        afterRun = main.ONOScli1.electionTestLeader()
        # verify leader is ONOS1
        if afterRun == ONOS1Ip:
            afterResult = main.TRUE
        else:
            afterResult = main.FALSE

        utilities.assert_equals(
            expect=main.TRUE,
            actual=afterResult,
            onpass="Old leader successfully re-ran for election",
            onfail="Something went wrong with Leadership election after " +
                   "the old leader re-ran for election" )

    def CASE16( self, main ):
        """
        Install Distributed Primitives app
        """
        assert numControllers, "numControllers not defined"
        assert main, "main not defined"
        assert utilities.assert_equals, "utilities.assert_equals not defined"
        assert CLIs, "CLIs not defined"
        assert nodes, "nodes not defined"

        # Variables for the distributed primitives tests
        global pCounterName
        global iCounterName
        global pCounterValue
        global iCounterValue
        global onosSet
        global onosSetName
        pCounterName = "TestON-Partitions"
        iCounterName = "TestON-inMemory"
        pCounterValue = 0
        iCounterValue = 0
        onosSet = set([])
        onosSetName = "TestON-set"

        description = "Install Primitives app"
        main.case( description )
        main.step( "Install Primitives app" )
        appName = "org.onosproject.distributedprimitives"
        appResults = CLIs[0].activateApp( appName )
        utilities.assert_equals( expect=main.TRUE,
                                 actual=appResults,
                                 onpass="Primitives app activated",
                                 onfail="Primitives app not activated" )

    def CASE17( self, main ):
        """
        Check for basic functionality with distributed primitives
        """
        import json
        # Make sure variables are defined/set
        assert numControllers, "numControllers not defined"
        assert main, "main not defined"
        assert utilities.assert_equals, "utilities.assert_equals not defined"
        assert CLIs, "CLIs not defined"
        assert nodes, "nodes not defined"
        assert pCounterName, "pCounterName not defined"
        assert iCounterName, "iCounterName not defined"
        assert onosSetName, "onosSetName not defined"
        # NOTE: assert fails if value is 0/None/Empty/False
        try:
            pCounterValue
        except NameError:
            main.log.error( "pCounterValue not defined, setting to 0" )
            pCounterValue = 0
        try:
            iCounterValue
        except NameError:
            main.log.error( "iCounterValue not defined, setting to 0" )
            iCounterValue = 0
        try:
            onosSet
        except NameError:
            main.log.error( "onosSet not defined, setting to empty Set" )
            onosSet = set([])
        # Variables for the distributed primitives tests. These are local only
        addValue = "a"
        addAllValue = "a b c d e f"
        retainValue = "c d e f"

        description = "Check for basic functionality with distributed " +\
                      "primitives"
        main.case( description )
        main.caseExplaination = "Test the methods of the distributed primitives (counters and sets) throught the cli"
        # DISTRIBUTED ATOMIC COUNTERS
        main.step( "Increment and get a default counter on each node" )
        pCounters = []
        threads = []
        addedPValues = []
        for i in range( numControllers ):
            t = main.Thread( target=CLIs[i].counterTestIncrement,
                             name="counterIncrement-" + str( i ),
                             args=[ pCounterName ] )
            pCounterValue += 1
            addedPValues.append( pCounterValue )
            threads.append( t )
            t.start()

        for t in threads:
            t.join()
            pCounters.append( t.result )
        # Check that counter incremented numController times
        pCounterResults = True
        for i in addedPValues:
            tmpResult = i in pCounters
            pCounterResults = pCounterResults and tmpResult
            if not tmpResult:
                main.log.error( str( i ) + " is not in partitioned "
                                "counter incremented results" )
        utilities.assert_equals( expect=True,
                                 actual=pCounterResults,
                                 onpass="Default counter incremented",
                                 onfail="Error incrementing default" +
                                        " counter" )

        main.step( "Increment and get an in memory counter on each node" )
        iCounters = []
        addedIValues = []
        threads = []
        for i in range( numControllers ):
            t = main.Thread( target=CLIs[i].counterTestIncrement,
                             name="icounterIncrement-" + str( i ),
                             args=[ iCounterName ],
                             kwargs={ "inMemory": True } )
            iCounterValue += 1
            addedIValues.append( iCounterValue )
            threads.append( t )
            t.start()

        for t in threads:
            t.join()
            iCounters.append( t.result )
        # Check that counter incremented numController times
        iCounterResults = True
        for i in addedIValues:
            tmpResult = i in iCounters
            iCounterResults = iCounterResults and tmpResult
            if not tmpResult:
                main.log.error( str( i ) + " is not in the in-memory "
                                "counter incremented results" )
        utilities.assert_equals( expect=True,
                                 actual=iCounterResults,
                                 onpass="In memory counter incremented",
                                 onfail="Error incrementing in memory" +
                                        " counter" )

        main.step( "Check counters are consistant across nodes" )
        onosCounters = []
        threads = []
        for i in range( numControllers ):
            t = main.Thread( target=CLIs[i].counters,
                             name="counters-" + str( i ) )
            threads.append( t )
            t.start()
        for t in threads:
            t.join()
            onosCounters.append( t.result )
        tmp = [ i == onosCounters[ 0 ] for i in onosCounters ]
        if all( tmp ):
            main.log.info( "Counters are consistent across all nodes" )
            consistentCounterResults = main.TRUE
        else:
            main.log.error( "Counters are not consistent across all nodes" )
            consistentCounterResults = main.FALSE
        utilities.assert_equals( expect=main.TRUE,
                                 actual=consistentCounterResults,
                                 onpass="ONOS counters are consistent " +
                                        "across nodes",
                                 onfail="ONOS Counters are inconsistent " +
                                        "across nodes" )

        main.step( "Counters we added have the correct values" )
        correctResults = main.TRUE
        for i in range( numControllers ):
            current = json.loads( onosCounters[i] )
            pValue = None
            iValue = None
            try:
                for database in current:
                    partitioned = database.get( 'partitionedDatabaseCounters' )
                    if partitioned:
                        for value in partitioned:
                            if value.get( 'name' ) == pCounterName:
                                pValue = value.get( 'value' )
                                break
                    inMemory = database.get( 'inMemoryDatabaseCounters' )
                    if inMemory:
                        for value in inMemory:
                            if value.get( 'name' ) == iCounterName:
                                iValue = value.get( 'value' )
                                break
            except AttributeError, e:
                main.log.error( "ONOS" + str( i + 1 ) + " counters result " +
                                "is not as expected" )
                correctResults = main.FALSE
            if pValue == pCounterValue:
                main.log.info( "Partitioned counter value is correct" )
            else:
                main.log.error( "Partitioned counter value is incorrect," +
                                " expected value: " + str( pCounterValue )
                                + " current value: " + str( pValue ) )
                correctResults = main.FALSE
            if iValue == iCounterValue:
                main.log.info( "In memory counter value is correct" )
            else:
                main.log.error( "In memory counter value is incorrect, " +
                                "expected value: " + str( iCounterValue ) +
                                " current value: " + str( iValue ) )
                correctResults = main.FALSE
        utilities.assert_equals( expect=main.TRUE,
                                 actual=correctResults,
                                 onpass="Added counters are correct",
                                 onfail="Added counters are incorrect" )
        # DISTRIBUTED SETS
        main.step( "Distributed Set get" )
        size = len( onosSet )
        getResponses = []
        threads = []
        for i in range( numControllers ):
            t = main.Thread( target=CLIs[i].setTestGet,
                             name="setTestGet-" + str( i ),
                             args=[ onosSetName ] )
            threads.append( t )
            t.start()
        for t in threads:
            t.join()
            getResponses.append( t.result )

        getResults = main.TRUE
        for i in range( numControllers ):
            if isinstance( getResponses[ i ], list):
                current = set( getResponses[ i ] )
                if len( current ) == len( getResponses[ i ] ):
                    # no repeats
                    if onosSet != current:
                        main.log.error( "ONOS" + str( i + 1 ) +
                                        " has incorrect view" +
                                        " of set " + onosSetName + ":\n" +
                                        str( getResponses[ i ] ) )
                        main.log.debug( "Expected: " + str( onosSet ) )
                        main.log.debug( "Actual: " + str( current ) )
                        getResults = main.FALSE
                else:
                    # error, set is not a set
                    main.log.error( "ONOS" + str( i + 1 ) +
                                    " has repeat elements in" +
                                    " set " + onosSetName + ":\n" +
                                    str( getResponses[ i ] ) )
                    getResults = main.FALSE
            elif getResponses[ i ] == main.ERROR:
                getResults = main.FALSE
        utilities.assert_equals( expect=main.TRUE,
                                 actual=getResults,
                                 onpass="Set elements are correct",
                                 onfail="Set elements are incorrect" )

        main.step( "Distributed Set size" )
        sizeResponses = []
        threads = []
        for i in range( numControllers ):
            t = main.Thread( target=CLIs[i].setTestSize,
                             name="setTestSize-" + str( i ),
                             args=[ onosSetName ] )
            threads.append( t )
            t.start()
        for t in threads:
            t.join()
            sizeResponses.append( t.result )

        sizeResults = main.TRUE
        for i in range( numControllers ):
            if size != sizeResponses[ i ]:
                sizeResults = main.FALSE
                main.log.error( "ONOS" + str( i + 1 ) +
                                " expected a size of " + str( size ) +
                                " for set " + onosSetName +
                                " but got " + str( sizeResponses[ i ] ) )
        utilities.assert_equals( expect=main.TRUE,
                                 actual=sizeResults,
                                 onpass="Set sizes are correct",
                                 onfail="Set sizes are incorrect" )

        main.step( "Distributed Set add()" )
        onosSet.add( addValue )
        addResponses = []
        threads = []
        for i in range( numControllers ):
            t = main.Thread( target=CLIs[i].setTestAdd,
                             name="setTestAdd-" + str( i ),
                             args=[ onosSetName, addValue ] )
            threads.append( t )
            t.start()
        for t in threads:
            t.join()
            addResponses.append( t.result )

        # main.TRUE = successfully changed the set
        # main.FALSE = action resulted in no change in set
        # main.ERROR - Some error in executing the function
        addResults = main.TRUE
        for i in range( numControllers ):
            if addResponses[ i ] == main.TRUE:
                # All is well
                pass
            elif addResponses[ i ] == main.FALSE:
                # Already in set, probably fine
                pass
            elif addResponses[ i ] == main.ERROR:
                # Error in execution
                addResults = main.FALSE
            else:
                # unexpected result
                addResults = main.FALSE
        if addResults != main.TRUE:
            main.log.error( "Error executing set add" )

        # Check if set is still correct
        size = len( onosSet )
        getResponses = []
        threads = []
        for i in range( numControllers ):
            t = main.Thread( target=CLIs[i].setTestGet,
                             name="setTestGet-" + str( i ),
                             args=[ onosSetName ] )
            threads.append( t )
            t.start()
        for t in threads:
            t.join()
            getResponses.append( t.result )
        getResults = main.TRUE
        for i in range( numControllers ):
            if isinstance( getResponses[ i ], list):
                current = set( getResponses[ i ] )
                if len( current ) == len( getResponses[ i ] ):
                    # no repeats
                    if onosSet != current:
                        main.log.error( "ONOS" + str( i + 1 ) +
                                        " has incorrect view" +
                                        " of set " + onosSetName + ":\n" +
                                        str( getResponses[ i ] ) )
                        main.log.debug( "Expected: " + str( onosSet ) )
                        main.log.debug( "Actual: " + str( current ) )
                        getResults = main.FALSE
                else:
                    # error, set is not a set
                    main.log.error( "ONOS" + str( i + 1 ) +
                                    " has repeat elements in" +
                                    " set " + onosSetName + ":\n" +
                                    str( getResponses[ i ] ) )
                    getResults = main.FALSE
            elif getResponses[ i ] == main.ERROR:
                getResults = main.FALSE
        sizeResponses = []
        threads = []
        for i in range( numControllers ):
            t = main.Thread( target=CLIs[i].setTestSize,
                             name="setTestSize-" + str( i ),
                             args=[ onosSetName ] )
            threads.append( t )
            t.start()
        for t in threads:
            t.join()
            sizeResponses.append( t.result )
        sizeResults = main.TRUE
        for i in range( numControllers ):
            if size != sizeResponses[ i ]:
                sizeResults = main.FALSE
                main.log.error( "ONOS" + str( i + 1 ) +
                                " expected a size of " + str( size ) +
                                " for set " + onosSetName +
                                " but got " + str( sizeResponses[ i ] ) )
        addResults = addResults and getResults and sizeResults
        utilities.assert_equals( expect=main.TRUE,
                                 actual=addResults,
                                 onpass="Set add correct",
                                 onfail="Set add was incorrect" )

        main.step( "Distributed Set addAll()" )
        onosSet.update( addAllValue.split() )
        addResponses = []
        threads = []
        for i in range( numControllers ):
            t = main.Thread( target=CLIs[i].setTestAdd,
                             name="setTestAddAll-" + str( i ),
                             args=[ onosSetName, addAllValue ] )
            threads.append( t )
            t.start()
        for t in threads:
            t.join()
            addResponses.append( t.result )

        # main.TRUE = successfully changed the set
        # main.FALSE = action resulted in no change in set
        # main.ERROR - Some error in executing the function
        addAllResults = main.TRUE
        for i in range( numControllers ):
            if addResponses[ i ] == main.TRUE:
                # All is well
                pass
            elif addResponses[ i ] == main.FALSE:
                # Already in set, probably fine
                pass
            elif addResponses[ i ] == main.ERROR:
                # Error in execution
                addAllResults = main.FALSE
            else:
                # unexpected result
                addAllResults = main.FALSE
        if addAllResults != main.TRUE:
            main.log.error( "Error executing set addAll" )

        # Check if set is still correct
        size = len( onosSet )
        getResponses = []
        threads = []
        for i in range( numControllers ):
            t = main.Thread( target=CLIs[i].setTestGet,
                             name="setTestGet-" + str( i ),
                             args=[ onosSetName ] )
            threads.append( t )
            t.start()
        for t in threads:
            t.join()
            getResponses.append( t.result )
        getResults = main.TRUE
        for i in range( numControllers ):
            if isinstance( getResponses[ i ], list):
                current = set( getResponses[ i ] )
                if len( current ) == len( getResponses[ i ] ):
                    # no repeats
                    if onosSet != current:
                        main.log.error( "ONOS" + str( i + 1 ) +
                                        " has incorrect view" +
                                        " of set " + onosSetName + ":\n" +
                                        str( getResponses[ i ] ) )
                        main.log.debug( "Expected: " + str( onosSet ) )
                        main.log.debug( "Actual: " + str( current ) )
                        getResults = main.FALSE
                else:
                    # error, set is not a set
                    main.log.error( "ONOS" + str( i + 1 ) +
                                    " has repeat elements in" +
                                    " set " + onosSetName + ":\n" +
                                    str( getResponses[ i ] ) )
                    getResults = main.FALSE
            elif getResponses[ i ] == main.ERROR:
                getResults = main.FALSE
        sizeResponses = []
        threads = []
        for i in range( numControllers ):
            t = main.Thread( target=CLIs[i].setTestSize,
                             name="setTestSize-" + str( i ),
                             args=[ onosSetName ] )
            threads.append( t )
            t.start()
        for t in threads:
            t.join()
            sizeResponses.append( t.result )
        sizeResults = main.TRUE
        for i in range( numControllers ):
            if size != sizeResponses[ i ]:
                sizeResults = main.FALSE
                main.log.error( "ONOS" + str( i + 1 ) +
                                " expected a size of " + str( size ) +
                                " for set " + onosSetName +
                                " but got " + str( sizeResponses[ i ] ) )
        addAllResults = addAllResults and getResults and sizeResults
        utilities.assert_equals( expect=main.TRUE,
                                 actual=addAllResults,
                                 onpass="Set addAll correct",
                                 onfail="Set addAll was incorrect" )

        main.step( "Distributed Set contains()" )
        containsResponses = []
        threads = []
        for i in range( numControllers ):
            t = main.Thread( target=CLIs[i].setTestGet,
                             name="setContains-" + str( i ),
                             args=[ onosSetName ],
                             kwargs={ "values": addValue } )
            threads.append( t )
            t.start()
        for t in threads:
            t.join()
            # NOTE: This is the tuple
            containsResponses.append( t.result )

        containsResults = main.TRUE
        for i in range( numControllers ):
            if containsResponses[ i ] == main.ERROR:
                containsResults = main.FALSE
            else:
                containsResults = containsResults and\
                                  containsResponses[ i ][ 1 ]
        utilities.assert_equals( expect=main.TRUE,
                                 actual=containsResults,
                                 onpass="Set contains is functional",
                                 onfail="Set contains failed" )

        main.step( "Distributed Set containsAll()" )
        containsAllResponses = []
        threads = []
        for i in range( numControllers ):
            t = main.Thread( target=CLIs[i].setTestGet,
                             name="setContainsAll-" + str( i ),
                             args=[ onosSetName ],
                             kwargs={ "values": addAllValue } )
            threads.append( t )
            t.start()
        for t in threads:
            t.join()
            # NOTE: This is the tuple
            containsAllResponses.append( t.result )

        containsAllResults = main.TRUE
        for i in range( numControllers ):
            if containsResponses[ i ] == main.ERROR:
                containsResults = main.FALSE
            else:
                containsResults = containsResults and\
                                  containsResponses[ i ][ 1 ]
        utilities.assert_equals( expect=main.TRUE,
                                 actual=containsAllResults,
                                 onpass="Set containsAll is functional",
                                 onfail="Set containsAll failed" )

        main.step( "Distributed Set remove()" )
        onosSet.remove( addValue )
        removeResponses = []
        threads = []
        for i in range( numControllers ):
            t = main.Thread( target=CLIs[i].setTestRemove,
                             name="setTestRemove-" + str( i ),
                             args=[ onosSetName, addValue ] )
            threads.append( t )
            t.start()
        for t in threads:
            t.join()
            removeResponses.append( t.result )

        # main.TRUE = successfully changed the set
        # main.FALSE = action resulted in no change in set
        # main.ERROR - Some error in executing the function
        removeResults = main.TRUE
        for i in range( numControllers ):
            if removeResponses[ i ] == main.TRUE:
                # All is well
                pass
            elif removeResponses[ i ] == main.FALSE:
                # not in set, probably fine
                pass
            elif removeResponses[ i ] == main.ERROR:
                # Error in execution
                removeResults = main.FALSE
            else:
                # unexpected result
                removeResults = main.FALSE
        if removeResults != main.TRUE:
            main.log.error( "Error executing set remove" )

        # Check if set is still correct
        size = len( onosSet )
        getResponses = []
        threads = []
        for i in range( numControllers ):
            t = main.Thread( target=CLIs[i].setTestGet,
                             name="setTestGet-" + str( i ),
                             args=[ onosSetName ] )
            threads.append( t )
            t.start()
        for t in threads:
            t.join()
            getResponses.append( t.result )
        getResults = main.TRUE
        for i in range( numControllers ):
            if isinstance( getResponses[ i ], list):
                current = set( getResponses[ i ] )
                if len( current ) == len( getResponses[ i ] ):
                    # no repeats
                    if onosSet != current:
                        main.log.error( "ONOS" + str( i + 1 ) +
                                        " has incorrect view" +
                                        " of set " + onosSetName + ":\n" +
                                        str( getResponses[ i ] ) )
                        main.log.debug( "Expected: " + str( onosSet ) )
                        main.log.debug( "Actual: " + str( current ) )
                        getResults = main.FALSE
                else:
                    # error, set is not a set
                    main.log.error( "ONOS" + str( i + 1 ) +
                                    " has repeat elements in" +
                                    " set " + onosSetName + ":\n" +
                                    str( getResponses[ i ] ) )
                    getResults = main.FALSE
            elif getResponses[ i ] == main.ERROR:
                getResults = main.FALSE
        sizeResponses = []
        threads = []
        for i in range( numControllers ):
            t = main.Thread( target=CLIs[i].setTestSize,
                             name="setTestSize-" + str( i ),
                             args=[ onosSetName ] )
            threads.append( t )
            t.start()
        for t in threads:
            t.join()
            sizeResponses.append( t.result )
        sizeResults = main.TRUE
        for i in range( numControllers ):
            if size != sizeResponses[ i ]:
                sizeResults = main.FALSE
                main.log.error( "ONOS" + str( i + 1 ) +
                                " expected a size of " + str( size ) +
                                " for set " + onosSetName +
                                " but got " + str( sizeResponses[ i ] ) )
        removeResults = removeResults and getResults and sizeResults
        utilities.assert_equals( expect=main.TRUE,
                                 actual=removeResults,
                                 onpass="Set remove correct",
                                 onfail="Set remove was incorrect" )

        main.step( "Distributed Set removeAll()" )
        onosSet.difference_update( addAllValue.split() )
        removeAllResponses = []
        threads = []
        try:
            for i in range( numControllers ):
                t = main.Thread( target=CLIs[i].setTestRemove,
                                 name="setTestRemoveAll-" + str( i ),
                                 args=[ onosSetName, addAllValue ] )
                threads.append( t )
                t.start()
            for t in threads:
                t.join()
                removeAllResponses.append( t.result )
        except Exception, e:
            main.log.exception(e)

        # main.TRUE = successfully changed the set
        # main.FALSE = action resulted in no change in set
        # main.ERROR - Some error in executing the function
        removeAllResults = main.TRUE
        for i in range( numControllers ):
            if removeAllResponses[ i ] == main.TRUE:
                # All is well
                pass
            elif removeAllResponses[ i ] == main.FALSE:
                # not in set, probably fine
                pass
            elif removeAllResponses[ i ] == main.ERROR:
                # Error in execution
                removeAllResults = main.FALSE
            else:
                # unexpected result
                removeAllResults = main.FALSE
        if removeAllResults != main.TRUE:
            main.log.error( "Error executing set removeAll" )

        # Check if set is still correct
        size = len( onosSet )
        getResponses = []
        threads = []
        for i in range( numControllers ):
            t = main.Thread( target=CLIs[i].setTestGet,
                             name="setTestGet-" + str( i ),
                             args=[ onosSetName ] )
            threads.append( t )
            t.start()
        for t in threads:
            t.join()
            getResponses.append( t.result )
        getResults = main.TRUE
        for i in range( numControllers ):
            if isinstance( getResponses[ i ], list):
                current = set( getResponses[ i ] )
                if len( current ) == len( getResponses[ i ] ):
                    # no repeats
                    if onosSet != current:
                        main.log.error( "ONOS" + str( i + 1 ) +
                                        " has incorrect view" +
                                        " of set " + onosSetName + ":\n" +
                                        str( getResponses[ i ] ) )
                        main.log.debug( "Expected: " + str( onosSet ) )
                        main.log.debug( "Actual: " + str( current ) )
                        getResults = main.FALSE
                else:
                    # error, set is not a set
                    main.log.error( "ONOS" + str( i + 1 ) +
                                    " has repeat elements in" +
                                    " set " + onosSetName + ":\n" +
                                    str( getResponses[ i ] ) )
                    getResults = main.FALSE
            elif getResponses[ i ] == main.ERROR:
                getResults = main.FALSE
        sizeResponses = []
        threads = []
        for i in range( numControllers ):
            t = main.Thread( target=CLIs[i].setTestSize,
                             name="setTestSize-" + str( i ),
                             args=[ onosSetName ] )
            threads.append( t )
            t.start()
        for t in threads:
            t.join()
            sizeResponses.append( t.result )
        sizeResults = main.TRUE
        for i in range( numControllers ):
            if size != sizeResponses[ i ]:
                sizeResults = main.FALSE
                main.log.error( "ONOS" + str( i + 1 ) +
                                " expected a size of " + str( size ) +
                                " for set " + onosSetName +
                                " but got " + str( sizeResponses[ i ] ) )
        removeAllResults = removeAllResults and getResults and sizeResults
        utilities.assert_equals( expect=main.TRUE,
                                 actual=removeAllResults,
                                 onpass="Set removeAll correct",
                                 onfail="Set removeAll was incorrect" )

        main.step( "Distributed Set addAll()" )
        onosSet.update( addAllValue.split() )
        addResponses = []
        threads = []
        for i in range( numControllers ):
            t = main.Thread( target=CLIs[i].setTestAdd,
                             name="setTestAddAll-" + str( i ),
                             args=[ onosSetName, addAllValue ] )
            threads.append( t )
            t.start()
        for t in threads:
            t.join()
            addResponses.append( t.result )

        # main.TRUE = successfully changed the set
        # main.FALSE = action resulted in no change in set
        # main.ERROR - Some error in executing the function
        addAllResults = main.TRUE
        for i in range( numControllers ):
            if addResponses[ i ] == main.TRUE:
                # All is well
                pass
            elif addResponses[ i ] == main.FALSE:
                # Already in set, probably fine
                pass
            elif addResponses[ i ] == main.ERROR:
                # Error in execution
                addAllResults = main.FALSE
            else:
                # unexpected result
                addAllResults = main.FALSE
        if addAllResults != main.TRUE:
            main.log.error( "Error executing set addAll" )

        # Check if set is still correct
        size = len( onosSet )
        getResponses = []
        threads = []
        for i in range( numControllers ):
            t = main.Thread( target=CLIs[i].setTestGet,
                             name="setTestGet-" + str( i ),
                             args=[ onosSetName ] )
            threads.append( t )
            t.start()
        for t in threads:
            t.join()
            getResponses.append( t.result )
        getResults = main.TRUE
        for i in range( numControllers ):
            if isinstance( getResponses[ i ], list):
                current = set( getResponses[ i ] )
                if len( current ) == len( getResponses[ i ] ):
                    # no repeats
                    if onosSet != current:
                        main.log.error( "ONOS" + str( i + 1 ) +
                                        " has incorrect view" +
                                        " of set " + onosSetName + ":\n" +
                                        str( getResponses[ i ] ) )
                        main.log.debug( "Expected: " + str( onosSet ) )
                        main.log.debug( "Actual: " + str( current ) )
                        getResults = main.FALSE
                else:
                    # error, set is not a set
                    main.log.error( "ONOS" + str( i + 1 ) +
                                    " has repeat elements in" +
                                    " set " + onosSetName + ":\n" +
                                    str( getResponses[ i ] ) )
                    getResults = main.FALSE
            elif getResponses[ i ] == main.ERROR:
                getResults = main.FALSE
        sizeResponses = []
        threads = []
        for i in range( numControllers ):
            t = main.Thread( target=CLIs[i].setTestSize,
                             name="setTestSize-" + str( i ),
                             args=[ onosSetName ] )
            threads.append( t )
            t.start()
        for t in threads:
            t.join()
            sizeResponses.append( t.result )
        sizeResults = main.TRUE
        for i in range( numControllers ):
            if size != sizeResponses[ i ]:
                sizeResults = main.FALSE
                main.log.error( "ONOS" + str( i + 1 ) +
                                " expected a size of " + str( size ) +
                                " for set " + onosSetName +
                                " but got " + str( sizeResponses[ i ] ) )
        addAllResults = addAllResults and getResults and sizeResults
        utilities.assert_equals( expect=main.TRUE,
                                 actual=addAllResults,
                                 onpass="Set addAll correct",
                                 onfail="Set addAll was incorrect" )

        main.step( "Distributed Set clear()" )
        onosSet.clear()
        clearResponses = []
        threads = []
        for i in range( numControllers ):
            t = main.Thread( target=CLIs[i].setTestRemove,
                             name="setTestClear-" + str( i ),
                             args=[ onosSetName, " "],  # Values doesn't matter
                             kwargs={ "clear": True } )
            threads.append( t )
            t.start()
        for t in threads:
            t.join()
            clearResponses.append( t.result )

        # main.TRUE = successfully changed the set
        # main.FALSE = action resulted in no change in set
        # main.ERROR - Some error in executing the function
        clearResults = main.TRUE
        for i in range( numControllers ):
            if clearResponses[ i ] == main.TRUE:
                # All is well
                pass
            elif clearResponses[ i ] == main.FALSE:
                # Nothing set, probably fine
                pass
            elif clearResponses[ i ] == main.ERROR:
                # Error in execution
                clearResults = main.FALSE
            else:
                # unexpected result
                clearResults = main.FALSE
        if clearResults != main.TRUE:
            main.log.error( "Error executing set clear" )

        # Check if set is still correct
        size = len( onosSet )
        getResponses = []
        threads = []
        for i in range( numControllers ):
            t = main.Thread( target=CLIs[i].setTestGet,
                             name="setTestGet-" + str( i ),
                             args=[ onosSetName ] )
            threads.append( t )
            t.start()
        for t in threads:
            t.join()
            getResponses.append( t.result )
        getResults = main.TRUE
        for i in range( numControllers ):
            if isinstance( getResponses[ i ], list):
                current = set( getResponses[ i ] )
                if len( current ) == len( getResponses[ i ] ):
                    # no repeats
                    if onosSet != current:
                        main.log.error( "ONOS" + str( i + 1 ) +
                                        " has incorrect view" +
                                        " of set " + onosSetName + ":\n" +
                                        str( getResponses[ i ] ) )
                        main.log.debug( "Expected: " + str( onosSet ) )
                        main.log.debug( "Actual: " + str( current ) )
                        getResults = main.FALSE
                else:
                    # error, set is not a set
                    main.log.error( "ONOS" + str( i + 1 ) +
                                    " has repeat elements in" +
                                    " set " + onosSetName + ":\n" +
                                    str( getResponses[ i ] ) )
                    getResults = main.FALSE
            elif getResponses[ i ] == main.ERROR:
                getResults = main.FALSE
        sizeResponses = []
        threads = []
        for i in range( numControllers ):
            t = main.Thread( target=CLIs[i].setTestSize,
                             name="setTestSize-" + str( i ),
                             args=[ onosSetName ] )
            threads.append( t )
            t.start()
        for t in threads:
            t.join()
            sizeResponses.append( t.result )
        sizeResults = main.TRUE
        for i in range( numControllers ):
            if size != sizeResponses[ i ]:
                sizeResults = main.FALSE
                main.log.error( "ONOS" + str( i + 1 ) +
                                " expected a size of " + str( size ) +
                                " for set " + onosSetName +
                                " but got " + str( sizeResponses[ i ] ) )
        clearResults = clearResults and getResults and sizeResults
        utilities.assert_equals( expect=main.TRUE,
                                 actual=clearResults,
                                 onpass="Set clear correct",
                                 onfail="Set clear was incorrect" )

        main.step( "Distributed Set addAll()" )
        onosSet.update( addAllValue.split() )
        addResponses = []
        threads = []
        for i in range( numControllers ):
            t = main.Thread( target=CLIs[i].setTestAdd,
                             name="setTestAddAll-" + str( i ),
                             args=[ onosSetName, addAllValue ] )
            threads.append( t )
            t.start()
        for t in threads:
            t.join()
            addResponses.append( t.result )

        # main.TRUE = successfully changed the set
        # main.FALSE = action resulted in no change in set
        # main.ERROR - Some error in executing the function
        addAllResults = main.TRUE
        for i in range( numControllers ):
            if addResponses[ i ] == main.TRUE:
                # All is well
                pass
            elif addResponses[ i ] == main.FALSE:
                # Already in set, probably fine
                pass
            elif addResponses[ i ] == main.ERROR:
                # Error in execution
                addAllResults = main.FALSE
            else:
                # unexpected result
                addAllResults = main.FALSE
        if addAllResults != main.TRUE:
            main.log.error( "Error executing set addAll" )

        # Check if set is still correct
        size = len( onosSet )
        getResponses = []
        threads = []
        for i in range( numControllers ):
            t = main.Thread( target=CLIs[i].setTestGet,
                             name="setTestGet-" + str( i ),
                             args=[ onosSetName ] )
            threads.append( t )
            t.start()
        for t in threads:
            t.join()
            getResponses.append( t.result )
        getResults = main.TRUE
        for i in range( numControllers ):
            if isinstance( getResponses[ i ], list):
                current = set( getResponses[ i ] )
                if len( current ) == len( getResponses[ i ] ):
                    # no repeats
                    if onosSet != current:
                        main.log.error( "ONOS" + str( i + 1 ) +
                                        " has incorrect view" +
                                        " of set " + onosSetName + ":\n" +
                                        str( getResponses[ i ] ) )
                        main.log.debug( "Expected: " + str( onosSet ) )
                        main.log.debug( "Actual: " + str( current ) )
                        getResults = main.FALSE
                else:
                    # error, set is not a set
                    main.log.error( "ONOS" + str( i + 1 ) +
                                    " has repeat elements in" +
                                    " set " + onosSetName + ":\n" +
                                    str( getResponses[ i ] ) )
                    getResults = main.FALSE
            elif getResponses[ i ] == main.ERROR:
                getResults = main.FALSE
        sizeResponses = []
        threads = []
        for i in range( numControllers ):
            t = main.Thread( target=CLIs[i].setTestSize,
                             name="setTestSize-" + str( i ),
                             args=[ onosSetName ] )
            threads.append( t )
            t.start()
        for t in threads:
            t.join()
            sizeResponses.append( t.result )
        sizeResults = main.TRUE
        for i in range( numControllers ):
            if size != sizeResponses[ i ]:
                sizeResults = main.FALSE
                main.log.error( "ONOS" + str( i + 1 ) +
                                " expected a size of " + str( size ) +
                                " for set " + onosSetName +
                                " but got " + str( sizeResponses[ i ] ) )
        addAllResults = addAllResults and getResults and sizeResults
        utilities.assert_equals( expect=main.TRUE,
                                 actual=addAllResults,
                                 onpass="Set addAll correct",
                                 onfail="Set addAll was incorrect" )

        main.step( "Distributed Set retain()" )
        onosSet.intersection_update( retainValue.split() )
        retainResponses = []
        threads = []
        for i in range( numControllers ):
            t = main.Thread( target=CLIs[i].setTestRemove,
                             name="setTestRetain-" + str( i ),
                             args=[ onosSetName, retainValue ],
                             kwargs={ "retain": True } )
            threads.append( t )
            t.start()
        for t in threads:
            t.join()
            retainResponses.append( t.result )

        # main.TRUE = successfully changed the set
        # main.FALSE = action resulted in no change in set
        # main.ERROR - Some error in executing the function
        retainResults = main.TRUE
        for i in range( numControllers ):
            if retainResponses[ i ] == main.TRUE:
                # All is well
                pass
            elif retainResponses[ i ] == main.FALSE:
                # Already in set, probably fine
                pass
            elif retainResponses[ i ] == main.ERROR:
                # Error in execution
                retainResults = main.FALSE
            else:
                # unexpected result
                retainResults = main.FALSE
        if retainResults != main.TRUE:
            main.log.error( "Error executing set retain" )

        # Check if set is still correct
        size = len( onosSet )
        getResponses = []
        threads = []
        for i in range( numControllers ):
            t = main.Thread( target=CLIs[i].setTestGet,
                             name="setTestGet-" + str( i ),
                             args=[ onosSetName ] )
            threads.append( t )
            t.start()
        for t in threads:
            t.join()
            getResponses.append( t.result )
        getResults = main.TRUE
        for i in range( numControllers ):
            if isinstance( getResponses[ i ], list):
                current = set( getResponses[ i ] )
                if len( current ) == len( getResponses[ i ] ):
                    # no repeats
                    if onosSet != current:
                        main.log.error( "ONOS" + str( i + 1 ) +
                                        " has incorrect view" +
                                        " of set " + onosSetName + ":\n" +
                                        str( getResponses[ i ] ) )
                        main.log.debug( "Expected: " + str( onosSet ) )
                        main.log.debug( "Actual: " + str( current ) )
                        getResults = main.FALSE
                else:
                    # error, set is not a set
                    main.log.error( "ONOS" + str( i + 1 ) +
                                    " has repeat elements in" +
                                    " set " + onosSetName + ":\n" +
                                    str( getResponses[ i ] ) )
                    getResults = main.FALSE
            elif getResponses[ i ] == main.ERROR:
                getResults = main.FALSE
        sizeResponses = []
        threads = []
        for i in range( numControllers ):
            t = main.Thread( target=CLIs[i].setTestSize,
                             name="setTestSize-" + str( i ),
                             args=[ onosSetName ] )
            threads.append( t )
            t.start()
        for t in threads:
            t.join()
            sizeResponses.append( t.result )
        sizeResults = main.TRUE
        for i in range( numControllers ):
            if size != sizeResponses[ i ]:
                sizeResults = main.FALSE
                main.log.error( "ONOS" + str( i + 1 ) +
                                " expected a size of " +
                                str( size ) + " for set " + onosSetName +
                                " but got " + str( sizeResponses[ i ] ) )
        retainResults = retainResults and getResults and sizeResults
        utilities.assert_equals( expect=main.TRUE,
                                 actual=retainResults,
                                 onpass="Set retain correct",
                                 onfail="Set retain was incorrect" )

