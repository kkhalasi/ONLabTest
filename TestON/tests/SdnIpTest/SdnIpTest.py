
# Testing the functionality of SDN-IP with single ONOS instance
class SdnIpTest:

    def __init__( self ):
        self.default = ''
        global branchName

    # This case is to setup ONOS
    def CASE100( self, main ):
        """
           CASE100 is to compile ONOS and push it to the test machines
           Startup sequence:
           git pull
           mvn clean install
           onos-package
           cell <name>
           onos-verify-cell
           onos-install -f
           onos-wait-for-start
        """
        import time
        main.case( "Setting up test environment" )

        cellName = main.params[ 'ENV' ][ 'cellName' ]
        ONOS1Ip = main.params[ 'CTRL' ][ 'ip1' ]

        main.step( "Applying cell variable to environment" )
        cellResult = main.ONOSbench.setCell( cellName )
        verifyResult = main.ONOSbench.verifyCell()

        branchName = main.ONOSbench.getBranchName()
        main.log.info( "ONOS is on branch: " + branchName )

        main.log.report( "Uninstalling ONOS" )
        main.ONOSbench.onosUninstall( ONOS1Ip )

        cleanInstallResult = main.TRUE
        gitPullResult = main.TRUE

        main.step( "Git pull" )
        gitPullResult = main.ONOSbench.gitPull()

        main.step( "Using mvn clean & install" )
        cleanInstallResult = main.TRUE
#         if gitPullResult == main.TRUE:
#             cleanInstallResult = main.ONOSbench.cleanInstall()
#         else:
#             main.log.warn( "Did not pull new code so skipping mvn " +
#                             "clean install" )
        cleanInstallResult = main.ONOSbench.cleanInstall( mciTimeout= 1000 )
        main.ONOSbench.getVersion( report=True )

        main.step( "Creating ONOS package" )
        packageResult = main.ONOSbench.onosPackage( opTimeout=500 )

        main.step( "Installing ONOS package" )
        onos1InstallResult = main.ONOSbench.onosInstall( options="-f",
                                                           node=ONOS1Ip )

        main.step( "Checking if ONOS is up yet" )
        for i in range( 2 ):
            onos1Isup = main.ONOSbench.isup( ONOS1Ip, timeout=420 )
            if onos1Isup:
                break
        if not onos1Isup:
            main.log.report( "ONOS1 didn't start!" )

        cliResult = main.ONOScli.startOnosCli( ONOS1Ip,
                commandlineTimeout=100, onosStartTimeout=600)

        case1Result = ( cleanInstallResult and packageResult and
                        cellResult and verifyResult and
                        onos1InstallResult and
                        onos1Isup and cliResult )

        utilities.assert_equals( expect=main.TRUE, actual=case1Result,
                                 onpass="ONOS startup successful",
                                 onfail="ONOS startup NOT successful" )

        if case1Result == main.FALSE:
            main.cleanup()
            main.exit()

    def CASE4( self, main ):
        """
        Test the SDN-IP functionality
        allRoutesExpected: all expected routes for all BGP peers
        routeIntentsExpected: all expected MultiPointToSinglePointIntent \
        intents
        bgpIntentsExpected: expected PointToPointIntent intents
        allRoutesActual: all routes from ONOS LCI
        routeIntentsActual: actual MultiPointToSinglePointIntent intents from \
        ONOS CLI
        bgpIntentsActual: actual PointToPointIntent intents from ONOS CLI
        """
        import time
        import json
        from operator import eq
        from time import localtime, strftime

        main.case("This case is to testing the functionality of SDN-IP with \
        single ONOS instance" )
        SDNIPJSONFILEPATH = \
            "/home/admin/ONOS/tools/package/config/sdnip.json"
        # all expected routes for all BGP peers
        allRoutesExpected = []
        main.step( "Start to generate routes for all BGP peers" )
        main.log.info( "Generate prefixes for host3" )
        prefixesHost3 = main.QuaggaCliHost3.generatePrefixes( 3, 10 )
        main.log.info( prefixesHost3 )
        # generate route with next hop
        for prefix in prefixesHost3:
            allRoutesExpected.append( prefix + "/" + "192.168.20.1" )
        routeIntentsExpectedHost3 = \
            main.QuaggaCliHost3.generateExpectedOnePeerRouteIntents(
            prefixesHost3, "192.168.20.1", "00:00:00:00:02:02",
            SDNIPJSONFILEPATH )

        main.log.info( "Generate prefixes for host4" )
        prefixesHost4 = main.QuaggaCliHost4.generatePrefixes( 4, 10 )
        main.log.info( prefixesHost4 )
        # generate route with next hop
        for prefix in prefixesHost4:
            allRoutesExpected.append( prefix + "/" + "192.168.30.1" )
        routeIntentsExpectedHost4 = \
            main.QuaggaCliHost4.generateExpectedOnePeerRouteIntents(
            prefixesHost4, "192.168.30.1", "00:00:00:00:03:01",
            SDNIPJSONFILEPATH )

        main.log.info( "Generate prefixes for host5" )
        prefixesHost5 = main.QuaggaCliHost5.generatePrefixes( 5, 10 )
        main.log.info( prefixesHost5 )
        for prefix in prefixesHost5:
            allRoutesExpected.append( prefix + "/" + "192.168.60.2" )
        routeIntentsExpectedHost5 = \
            main.QuaggaCliHost5.generateExpectedOnePeerRouteIntents(
            prefixesHost5, "192.168.60.1", "00:00:00:00:06:02",
            SDNIPJSONFILEPATH )

        routeIntentsExpected = routeIntentsExpectedHost3 + \
            routeIntentsExpectedHost4 + routeIntentsExpectedHost5

        main.step( "Get devices in the network" )
        listResult = main.ONOScli.devices( jsonFormat=False )
        main.log.info( listResult )
        time.sleep( 10 )
        main.log.info( "Activate sdn-ip application" )
        main.ONOScli.activateApp( "org.onosproject.sdnip" )
        time.sleep( 10 )
        main.step( "Login all BGP peers and add routes into peers" )

        main.log.info( "Login Quagga CLI on host3" )
        main.QuaggaCliHost3.loginQuagga( "1.168.30.2" )
        main.log.info( "Enter configuration model of Quagga CLI on host3" )
        main.QuaggaCliHost3.enterConfig( 64514 )
        main.log.info( "Add routes to Quagga on host3" )
        main.QuaggaCliHost3.addRoutes( prefixesHost3, 1 )

        main.log.info( "Login Quagga CLI on host4" )
        main.QuaggaCliHost4.loginQuagga( "1.168.30.3" )
        main.log.info( "Enter configuration model of Quagga CLI on host4" )
        main.QuaggaCliHost4.enterConfig( 64516 )
        main.log.info( "Add routes to Quagga on host4" )
        main.QuaggaCliHost4.addRoutes( prefixesHost4, 1 )

        main.log.info( "Login Quagga CLI on host5" )
        main.QuaggaCliHost5.loginQuagga( "1.168.30.5" )
        main.log.info( "Enter configuration model of Quagga CLI on host5" )
        main.QuaggaCliHost5.enterConfig( 64521 )
        main.log.info( "Add routes to Quagga on host5" )
        main.QuaggaCliHost5.addRoutes( prefixesHost5, 1 )

        for i in range( 101, 201 ):
            prefixesHostX = main.QuaggaCliHost.generatePrefixes( str( i ), 10 )
            main.log.info( prefixesHostX )
            for prefix in prefixesHostX:
                allRoutesExpected.append( prefix + "/" + "192.168.40."
                                           + str( i - 100 ) )

            routeIntentsExpectedHostX = \
            main.QuaggaCliHost.generateExpectedOnePeerRouteIntents(
                prefixesHostX, "192.168.40." + str( i - 100 ),
                "00:00:%02d:00:00:90" % ( i - 101 ), SDNIPJSONFILEPATH )
            routeIntentsExpected = routeIntentsExpected + \
                routeIntentsExpectedHostX

            main.log.info( "Login Quagga CLI on host" + str( i ) )
            QuaggaCliHostX = getattr( main, ( 'QuaggaCliHost' + str( i ) ) )
            QuaggaCliHostX.loginQuagga( "1.168.30." + str( i ) )
            main.log.info(
                "Enter configuration model of Quagga CLI on host" + str( i ) )
            QuaggaCliHostX.enterConfig( 65000 + i - 100 )
            main.log.info( "Add routes to Quagga on host" + str( i ) )
            QuaggaCliHostX.addRoutes( prefixesHostX, 1 )

        time.sleep( 60 )
        # get routes inside SDN-IP
        getRoutesResult = main.ONOScli.routes( jsonFormat=True )

        allRoutesActual = \
            main.QuaggaCliHost3.extractActualRoutesMaster( getRoutesResult )

        allRoutesStrExpected = str( sorted( allRoutesExpected ) )
        allRoutesStrActual = str( allRoutesActual ).replace( 'u', "" )
        main.step( "Check routes installed" )
        main.log.info( "Routes expected:" )
        main.log.info( allRoutesStrExpected )
        main.log.info( "Routes get from ONOS CLI:" )
        main.log.info( allRoutesStrActual )
        utilities.assertEquals(
            expect=allRoutesStrExpected, actual=allRoutesStrActual,
            onpass="***Routes in SDN-IP are correct!***",
            onfail="***Routes in SDN-IP are wrong!***" )
        if( eq( allRoutesStrExpected, allRoutesStrActual ) ):
            main.log.report(
                "***Routes in SDN-IP after adding routes are correct!***" )
        else:
            main.log.report(
                "***Routes in SDN-IP after adding routes are wrong!***" )

        time.sleep( 20 )
        getIntentsResult = main.ONOScli.intents( jsonFormat=True )

        main.step( "Check MultiPointToSinglePointIntent intents installed" )
        # routeIntentsExpected are generated when generating routes
        # get route intents from ONOS CLI
        routeIntentsActualNum = \
            main.QuaggaCliHost3.extractActualRouteIntentNum( getIntentsResult )
        routeIntentsExpectedNum = 1030
        main.log.info( "MultiPointToSinglePoint Intent Num expected is:" )
        main.log.info( routeIntentsExpectedNum )
        main.log.info( "MultiPointToSinglePoint Intent NUM Actual is:" )
        main.log.info( routeIntentsActualNum )
        utilities.assertEquals(
            expect=True,
            actual=eq( routeIntentsExpectedNum, routeIntentsActualNum ),
            onpass="***MultiPointToSinglePoint Intent Num in SDN-IP is \
            correct!***",
            onfail="***MultiPointToSinglePoint Intent Num in SDN-IP is \
            wrong!***" )

        if( eq( routeIntentsExpectedNum, routeIntentsActualNum ) ):
            main.log.report( "***MultiPointToSinglePoint Intents before \
            deleting routes correct!***" )
        else:
            main.log.report( "***MultiPointToSinglePoint Intents before \
            deleting routes wrong!***" )

        main.step( "Check BGP PointToPointIntent intents installed" )

        bgpIntentsActualNum = \
            main.QuaggaCliHost3.extractActualBgpIntentNum( getIntentsResult )
        bgpIntentsExpectedNum = 624
        main.log.info( "bgpIntentsExpected num is:" )
        main.log.info( bgpIntentsExpectedNum )
        main.log.info( "bgpIntentsActual num is:" )
        main.log.info( bgpIntentsActualNum)
        utilities.assertEquals(
            expect=True,
            actual=eq( bgpIntentsExpectedNum, bgpIntentsActualNum ),
            onpass="***PointToPointIntent Intent Num in SDN-IP are correct!***",
            onfail="***PointToPointIntent Intent Num in SDN-IP are wrong!***" )
        if ( eq( bgpIntentsExpectedNum, bgpIntentsActualNum ) ):
            main.log.report(
                "***PointToPointIntent Intents in SDN-IP are correct!***" )
        else:
            main.log.report(
                "***PointToPointIntent Intents in SDN-IP are wrong!***" )

        #============================= Ping Test ========================
        # Wait until all MultiPointToSinglePoint intents are in system
        time.sleep( 20 )
        pingTestScript = "~/SDNIP/test-tools/CASE4-ping-as2host.sh"
        pingTestResultsFile = \
        "~/SDNIP/SdnIpIntentDemo/log/CASE4-ping-results-before-delete-routes-"\
            + strftime( "%Y-%m-%d_%H:%M:%S", localtime() ) + ".txt"
        pingTestResults = main.QuaggaCliHost.pingTest(
            "1.168.30.100", pingTestScript, pingTestResultsFile )
        main.log.info( pingTestResults )
        time.sleep( 20 )

        #============================= Deleting Routes ==================
        main.step( "Check deleting routes installed" )
        main.QuaggaCliHost3.deleteRoutes( prefixesHost3, 1 )
        main.QuaggaCliHost4.deleteRoutes( prefixesHost4, 1 )
        main.QuaggaCliHost5.deleteRoutes( prefixesHost5, 1 )

        for i in range( 101, 201 ):
            prefixesHostX = main.QuaggaCliHost.generatePrefixes( str( i ), 10 )
            main.log.info( prefixesHostX )
            QuaggaCliHostX = getattr( main, ( 'QuaggaCliHost' + str( i ) ) )
            QuaggaCliHostX.deleteRoutes( prefixesHostX, 1 )

        getRoutesResult = main.ONOScli.routes( jsonFormat=True )
        allRoutesActual = \
            main.QuaggaCliHost3.extractActualRoutesMaster( getRoutesResult )
        main.log.info( "allRoutes_actual = " )
        main.log.info( allRoutesActual )

        utilities.assertEquals(
            expect="[]", actual=str( allRoutesActual ),
            onpass="***Route number in SDN-IP is 0, correct!***",
            onfail="***Routes number in SDN-IP is not 0, wrong!***" )

        if( eq( allRoutesStrExpected, allRoutesStrActual ) ):
            main.log.report( "***Routes in SDN-IP after deleting correct!***" )
        else:
            main.log.report( "***Routes in SDN-IP after deleting wrong!***" )

        main.step( "Check intents after deleting routes" )
        getIntentsResult = main.ONOScli.intents( jsonFormat=True )
        routeIntentsActualNum = \
            main.QuaggaCliHost3.extractActualRouteIntentNum(
                getIntentsResult )
        main.log.info( "route Intents Actual Num is: " )
        main.log.info( routeIntentsActualNum )
        utilities.assertEquals(
            expect=0, actual=routeIntentsActualNum,
            onpass="***MultiPointToSinglePoint Intent Num in SDN-IP is 0, \
            correct!***",
            onfail="***MultiPointToSinglePoint Intent Num in SDN-IP is not 0, \
            wrong!***" )

        if( eq( 0, routeIntentsActualNum ) ):
            main.log.report( "***MultiPointToSinglePoint Intents after \
            deleting routes correct!***" )
        else:
            main.log.report( "***MultiPointToSinglePoint Intents after \
            deleting routes wrong!***" )

        time.sleep( 20 )
        pingTestScript = "~/SDNIP/test-tools/CASE4-ping-as2host.sh"
        pingTestResultsFile = \
        "~/SDNIP/SdnIpIntentDemo/log/CASE4-ping-results-after-delete-routes-"\
            + strftime( "%Y-%m-%d_%H:%M:%S", localtime() ) + ".txt"
        pingTestResults = main.QuaggaCliHost.pingTest(
            "1.168.30.100", pingTestScript, pingTestResultsFile )
        main.log.info( pingTestResults )
        time.sleep( 100 )

    def CASE_4_origin( self, main ):
        """
        Test the SDN-IP functionality
        allRoutesExpected: all expected routes for all BGP peers
        routeIntentsExpected: all expected MultiPointToSinglePointIntent \
        intents
        bgpIntentsExpected: expected PointToPointIntent intents
        allRoutesActual: all routes from ONOS LCI
        routeIntentsActual: actual MultiPointToSinglePointIntent intents from \
        ONOS CLI
        bgpIntentsActual: actual PointToPointIntent intents from ONOS CLI
        """
        import time
        import json
        from operator import eq
        from time import localtime, strftime

        main.case("This case is to testing the functionality of SDN-IP with \
        single ONOS instance" )
        SDNIPJSONFILEPATH = \
            "/home/admin/ONOS/tools/package/config/sdnip.json"
        # all expected routes for all BGP peers
        allRoutesExpected = []
        main.step( "Start to generate routes for all BGP peers" )
        main.log.info( "Generate prefixes for host3" )
        prefixesHost3 = main.QuaggaCliHost3.generatePrefixes( 3, 10 )
        main.log.info( prefixesHost3 )
        # generate route with next hop
        for prefix in prefixesHost3:
            allRoutesExpected.append( prefix + "/" + "192.168.20.1" )
        routeIntentsExpectedHost3 = \
            main.QuaggaCliHost3.generateExpectedOnePeerRouteIntents(
            prefixesHost3, "192.168.20.1", "00:00:00:00:02:02",
            SDNIPJSONFILEPATH )

        main.log.info( "Generate prefixes for host4" )
        prefixesHost4 = main.QuaggaCliHost4.generatePrefixes( 4, 10 )
        main.log.info( prefixesHost4 )
        # generate route with next hop
        for prefix in prefixesHost4:
            allRoutesExpected.append( prefix + "/" + "192.168.30.1" )
        routeIntentsExpectedHost4 = \
            main.QuaggaCliHost4.generateExpectedOnePeerRouteIntents(
            prefixesHost4, "192.168.30.1", "00:00:00:00:03:01",
            SDNIPJSONFILEPATH )

        main.log.info( "Generate prefixes for host5" )
        prefixesHost5 = main.QuaggaCliHost5.generatePrefixes( 5, 10 )
        main.log.info( prefixesHost5 )
        for prefix in prefixesHost5:
            allRoutesExpected.append( prefix + "/" + "192.168.60.2" )
        routeIntentsExpectedHost5 = \
            main.QuaggaCliHost5.generateExpectedOnePeerRouteIntents(
            prefixesHost5, "192.168.60.1", "00:00:00:00:06:02",
            SDNIPJSONFILEPATH )

        routeIntentsExpected = routeIntentsExpectedHost3 + \
            routeIntentsExpectedHost4 + routeIntentsExpectedHost5

        main.step( "Get devices in the network" )
        listResult = main.ONOScli.devices( jsonFormat=False )
        main.log.info( listResult )
        time.sleep( 10 )
        if branchName == "onos-1.1":
            main.log.info( "Installing sdn-ip feature" )
            main.ONOScli.featureInstall( "onos-app-sdnip" )
        else:
            main.log.info( "Activate sdn-ip application" )
            main.ONOScli.activateApp( "org.onosproject.sdnip" )
        #main.log.info( "Installing sdn-ip feature" )
        #main.ONOScli.featureInstall( "onos-app-sdnip" )
        time.sleep( 10 )
        main.step( "Login all BGP peers and add routes into peers" )

        main.log.info( "Login Quagga CLI on host3" )
        main.QuaggaCliHost3.loginQuagga( "1.168.30.2" )
        main.log.info( "Enter configuration model of Quagga CLI on host3" )
        main.QuaggaCliHost3.enterConfig( 64514 )
        main.log.info( "Add routes to Quagga on host3" )
        main.QuaggaCliHost3.addRoutes( prefixesHost3, 1 )

        main.log.info( "Login Quagga CLI on host4" )
        main.QuaggaCliHost4.loginQuagga( "1.168.30.3" )
        main.log.info( "Enter configuration model of Quagga CLI on host4" )
        main.QuaggaCliHost4.enterConfig( 64516 )
        main.log.info( "Add routes to Quagga on host4" )
        main.QuaggaCliHost4.addRoutes( prefixesHost4, 1 )

        main.log.info( "Login Quagga CLI on host5" )
        main.QuaggaCliHost5.loginQuagga( "1.168.30.5" )
        main.log.info( "Enter configuration model of Quagga CLI on host5" )
        main.QuaggaCliHost5.enterConfig( 64521 )
        main.log.info( "Add routes to Quagga on host5" )
        main.QuaggaCliHost5.addRoutes( prefixesHost5, 1 )

        for i in range( 101, 201 ):
            prefixesHostX = main.QuaggaCliHost.generatePrefixes( str( i ), 10 )
            main.log.info( prefixesHostX )
            for prefix in prefixesHostX:
                allRoutesExpected.append( prefix + "/" + "192.168.40."
                                           + str( i - 100 ) )

            routeIntentsExpectedHostX = \
            main.QuaggaCliHost.generateExpectedOnePeerRouteIntents(
                prefixesHostX, "192.168.40." + str( i - 100 ),
                "00:00:%02d:00:00:90" % ( i - 101 ), SDNIPJSONFILEPATH )
            routeIntentsExpected = routeIntentsExpected + \
                routeIntentsExpectedHostX

            main.log.info( "Login Quagga CLI on host" + str( i ) )
            QuaggaCliHostX = getattr( main, ( 'QuaggaCliHost' + str( i ) ) )
            QuaggaCliHostX.loginQuagga( "1.168.30." + str( i ) )
            main.log.info(
                "Enter configuration model of Quagga CLI on host" + str( i ) )
            QuaggaCliHostX.enterConfig( 65000 + i - 100 )
            main.log.info( "Add routes to Quagga on host" + str( i ) )
            QuaggaCliHostX.addRoutes( prefixesHostX, 1 )

        time.sleep( 60 )
        # get routes inside SDN-IP
        getRoutesResult = main.ONOScli.routes( jsonFormat=True )

        # parse routes from ONOS CLI
        #if branchName == "master":
        #    allRoutesActual = \
        #    main.QuaggaCliHost3.extractActualRoutesMaster( getRoutesResult )
        #elif branchName == "onos-1.0":
        #    allRoutesActual = \
        #    main.QuaggaCliHost3.extractActualRoutesOneDotZero( getRoutesResult )
        #else:
        #    main.log("ONOS is on wrong branch")
        #    exit

        allRoutesActual = \
            main.QuaggaCliHost3.extractActualRoutesMaster( getRoutesResult )

        allRoutesStrExpected = str( sorted( allRoutesExpected ) )
        allRoutesStrActual = str( allRoutesActual ).replace( 'u', "" )
        main.step( "Check routes installed" )
        main.log.info( "Routes expected:" )
        main.log.info( allRoutesStrExpected )
        main.log.info( "Routes get from ONOS CLI:" )
        main.log.info( allRoutesStrActual )
        utilities.assertEquals(
            expect=allRoutesStrExpected, actual=allRoutesStrActual,
            onpass="***Routes in SDN-IP are correct!***",
            onfail="***Routes in SDN-IP are wrong!***" )
        if( eq( allRoutesStrExpected, allRoutesStrActual ) ):
            main.log.report(
                "***Routes in SDN-IP after adding routes are correct!***" )
        else:
            main.log.report(
                "***Routes in SDN-IP after adding routes are wrong!***" )

        time.sleep( 20 )
        getIntentsResult = main.ONOScli.intents( jsonFormat=True )

        main.step( "Check MultiPointToSinglePointIntent intents installed" )
        # routeIntentsExpected are generated when generating routes
        # get route intents from ONOS CLI
        routeIntentsActual = \
            main.QuaggaCliHost3.extractActualRouteIntents(
                getIntentsResult )
        routeIntentsStrExpected = str( sorted( routeIntentsExpected ) )
        routeIntentsStrActual = str( routeIntentsActual ).replace( 'u', "" )
        main.log.info( "MultiPointToSinglePoint intents expected:" )
        main.log.info( routeIntentsStrExpected )
        main.log.info( "MultiPointToSinglePoint intents get from ONOS CLI:" )
        main.log.info( routeIntentsStrActual )
        utilities.assertEquals(
            expect=True,
            actual=eq( routeIntentsStrExpected, routeIntentsStrActual ),
            onpass="***MultiPointToSinglePoint Intents in SDN-IP are \
            correct!***",
            onfail="***MultiPointToSinglePoint Intents in SDN-IP are \
            wrong!***" )

        if( eq( routeIntentsStrExpected, routeIntentsStrActual ) ):
            main.log.report( "***MultiPointToSinglePoint Intents before \
            deleting routes correct!***" )
        else:
            main.log.report( "***MultiPointToSinglePoint Intents before \
            deleting routes wrong!***" )

        main.step( "Check BGP PointToPointIntent intents installed" )
        # bgp intents expected
        bgpIntentsExpected = \
            main.QuaggaCliHost3.generateExpectedBgpIntents( SDNIPJSONFILEPATH )
        # get BGP intents from ONOS CLI
        bgpIntentsActual = \
            main.QuaggaCliHost3.extractActualBgpIntents( getIntentsResult )

        bgpIntentsStrExpected = str( bgpIntentsExpected ).replace( 'u', "" )
        bgpIntentsStrActual = str( bgpIntentsActual )
        main.log.info( "PointToPointIntent intents expected:" )
        main.log.info( bgpIntentsStrExpected )
        main.log.info( "PointToPointIntent intents get from ONOS CLI:" )
        main.log.info( bgpIntentsStrActual )

        utilities.assertEquals(
            expect=True,
            actual=eq( bgpIntentsStrExpected, bgpIntentsStrActual ),
            onpass="***PointToPointIntent Intents in SDN-IP are correct!***",
            onfail="***PointToPointIntent Intents in SDN-IP are wrong!***" )

        if ( eq( bgpIntentsStrExpected, bgpIntentsStrActual ) ):
            main.log.report(
                "***PointToPointIntent Intents in SDN-IP are correct!***" )
        else:
            main.log.report(
                "***PointToPointIntent Intents in SDN-IP are wrong!***" )

        #============================= Ping Test ========================
        # Wait until all MultiPointToSinglePoint intents are in system
        time.sleep( 20 )
        pingTestScript = "~/SDNIP/test-tools/CASE4-ping-as2host.sh"
        pingTestResultsFile = \
        "~/SDNIP/SdnIpIntentDemo/log/CASE4-ping-results-before-delete-routes-" \
            + strftime( "%Y-%m-%d_%H:%M:%S", localtime() ) + ".txt"
        pingTestResults = main.QuaggaCliHost.pingTest(
            "1.168.30.100", pingTestScript, pingTestResultsFile )
        main.log.info( pingTestResults )
        time.sleep( 20 )

        #============================= Deleting Routes ==================
        main.step( "Check deleting routes installed" )
        main.QuaggaCliHost3.deleteRoutes( prefixesHost3, 1 )
        main.QuaggaCliHost4.deleteRoutes( prefixesHost4, 1 )
        main.QuaggaCliHost5.deleteRoutes( prefixesHost5, 1 )

        for i in range( 101, 201 ):
            prefixesHostX = main.QuaggaCliHost.generatePrefixes( str( i ), 10 )
            main.log.info( prefixesHostX )
            QuaggaCliHostX = getattr( main, ( 'QuaggaCliHost' + str( i ) ) )
            QuaggaCliHostX.deleteRoutes( prefixesHostX, 1 )

        getRoutesResult = main.ONOScli.routes( jsonFormat=True )
        allRoutesActual = \
            main.QuaggaCliHost3.extractActualRoutes( getRoutesResult )
        main.log.info( "allRoutes_actual = " )
        main.log.info( allRoutesActual )

        utilities.assertEquals(
            expect="[]", actual=str( allRoutesActual ),
            onpass="***Route number in SDN-IP is 0, correct!***",
            onfail="***Routes number in SDN-IP is not 0, wrong!***" )

        if( eq( allRoutesStrExpected, allRoutesStrActual ) ):
            main.log.report( "***Routes in SDN-IP after deleting correct!***" )
        else:
            main.log.report( "***Routes in SDN-IP after deleting wrong!***" )

        main.step( "Check intents after deleting routes" )
        getIntentsResult = main.ONOScli.intents( jsonFormat=True )
        routeIntentsActual = \
            main.QuaggaCliHost3.extractActualRouteIntents(
                getIntentsResult )
        main.log.info( "main.ONOScli.intents()= " )
        main.log.info( routeIntentsActual )
        utilities.assertEquals(
            expect="[]", actual=str( routeIntentsActual ),
            onpass="***MultiPointToSinglePoint Intents number in SDN-IP is 0, \
            correct!***",
            onfail="***MultiPointToSinglePoint Intents number in SDN-IP is 0, \
            wrong!***" )

        if( eq( routeIntentsStrExpected, routeIntentsStrActual ) ):
            main.log.report( "***MultiPointToSinglePoint Intents after \
            deleting routes correct!***" )
        else:
            main.log.report( "***MultiPointToSinglePoint Intents after \
            deleting routes wrong!***" )

        time.sleep( 20 )
        pingTestScript = "~/SDNIP/test-tools/CASE4-ping-as2host.sh"
        pingTestResultsFile = \
        "~/SDNIP/SdnIpIntentDemo/log/CASE4-ping-results-after-delete-routes-"\
            + strftime( "%Y-%m-%d_%H:%M:%S", localtime() ) + ".txt"
        pingTestResults = main.QuaggaCliHost.pingTest(
            "1.168.30.100", pingTestScript, pingTestResultsFile )
        main.log.info( pingTestResults )
        time.sleep( 100 )

    def CASE3( self, main ):
        """
        Test the SDN-IP functionality
        allRoutesExpected: all expected routes for all BGP peers
        routeIntentsExpected: all expected MultiPointToSinglePointIntent \
        intents
        bgpIntentsExpected: expected PointToPointIntent intents
        allRoutesActual: all routes from ONOS LCI
        routeIntentsActual: actual MultiPointToSinglePointIntent intents from \
        ONOS CLI
        bgpIntentsActual: actual PointToPointIntent intents from ONOS CLI
        """
        import time
        import json
        from operator import eq
        # from datetime import datetime
        from time import localtime, strftime

        main.case( "The test case is to help to setup the TestON \
            environment and test new drivers" )
        # SDNIPJSONFILEPATH = "../tests/SdnIpTest/sdnip.json"
        SDNIPJSONFILEPATH = \
            "/home/admin/ONOS/tools/package/config/sdnip.json"
        # all expected routes for all BGP peers
        allRoutesExpected = []
        main.step( "Start to generate routes for all BGP peers" )
        main.log.info( "Generate prefixes for host3" )
        prefixesHost3 = main.QuaggaCliHost3.generatePrefixes( 3, 10 )
        main.log.info( prefixesHost3 )
        # generate route with next hop
        for prefix in prefixesHost3:
            allRoutesExpected.append( prefix + "/" + "192.168.20.1" )
        routeIntentsExpectedHost3 = \
            main.QuaggaCliHost3.generateExpectedOnePeerRouteIntents(
            prefixesHost3, "192.168.20.1", "00:00:00:00:02:02",
            SDNIPJSONFILEPATH )

        main.log.info( "Generate prefixes for host4" )
        prefixesHost4 = main.QuaggaCliHost4.generatePrefixes( 4, 10 )
        main.log.info( prefixesHost4 )
        # generate route with next hop
        for prefix in prefixesHost4:
            allRoutesExpected.append( prefix + "/" + "192.168.30.1" )
        routeIntentsExpectedHost4 = \
            main.QuaggaCliHost4.generateExpectedOnePeerRouteIntents(
            prefixesHost4, "192.168.30.1", "00:00:00:00:03:01",
            SDNIPJSONFILEPATH )

        routeIntentsExpected = routeIntentsExpectedHost3 + \
            routeIntentsExpectedHost4

        cellName = main.params[ 'ENV' ][ 'cellName' ]
        ONOS1Ip = main.params[ 'CTRL' ][ 'ip1' ]
        main.step( "Set cell for ONOS-cli environment" )
        main.ONOScli.setCell( cellName )
        verifyResult = main.ONOSbench.verifyCell()

        main.log.report( "Removing raft logs" )
        main.ONOSbench.onosRemoveRaftLogs()
        main.log.report( "Uninstalling ONOS" )
        main.ONOSbench.onosUninstall( ONOS1Ip )

        main.step( "Installing ONOS package" )
        onos1InstallResult = main.ONOSbench.onosInstall(
            options="-f", node=ONOS1Ip )

        main.step( "Checking if ONOS is up yet" )
        time.sleep( 60 )
        onos1Isup = main.ONOSbench.isup( ONOS1Ip )
        if not onos1Isup:
            main.log.report( "ONOS1 didn't start!" )

        main.step( "Start ONOS-cli" )

        main.ONOScli.startOnosCli( ONOS1Ip )

        main.step( "Get devices in the network" )
        listResult = main.ONOScli.devices( jsonFormat=False )
        main.log.info( listResult )
        time.sleep( 10 )
        if branchName == "onos-1.1":
            main.log.info( "Installing sdn-ip feature" )
            main.ONOScli.featureInstall( "onos-app-sdnip" )
        else:
            main.log.info( "Activate sdn-ip application" )
            main.ONOScli.activateApp( "org.onosproject.sdnip" )
        time.sleep( 10 )
        main.step( "Login all BGP peers and add routes into peers" )

        main.log.info( "Login Quagga CLI on host3" )
        main.QuaggaCliHost3.loginQuagga( "1.168.30.2" )
        main.log.info( "Enter configuration model of Quagga CLI on host3" )
        main.QuaggaCliHost3.enterConfig( 64514 )
        main.log.info( "Add routes to Quagga on host3" )
        main.QuaggaCliHost3.addRoutes( prefixesHost3, 1 )

        main.log.info( "Login Quagga CLI on host4" )
        main.QuaggaCliHost4.loginQuagga( "1.168.30.3" )
        main.log.info( "Enter configuration model of Quagga CLI on host4" )
        main.QuaggaCliHost4.enterConfig( 64516 )
        main.log.info( "Add routes to Quagga on host4" )
        main.QuaggaCliHost4.addRoutes( prefixesHost4, 1 )

        for i in range( 101, 201 ):
            prefixesHostX = \
                main.QuaggaCliHost.generatePrefixes( str( i ), 10 )
            main.log.info( prefixesHostX )
            for prefix in prefixesHostX:
                allRoutesExpected.append(
                    prefix + "/" + "192.168.40." + str( i - 100 ) )

            routeIntentsExpectedHostX = \
                main.QuaggaCliHost.generateExpectedOnePeerRouteIntents(
                prefixesHostX, "192.168.40." + str( i - 100 ),
                "00:00:%02d:00:00:90" % ( i - 101 ), SDNIPJSONFILEPATH )
            routeIntentsExpected = routeIntentsExpected + \
                routeIntentsExpectedHostX

            main.log.info( "Login Quagga CLI on host" + str( i ) )
            QuaggaCliHostX = getattr( main, ( 'QuaggaCliHost' + str( i ) ) )
            QuaggaCliHostX.loginQuagga( "1.168.30." + str( i ) )
            main.log.info(
                "Enter configuration model of Quagga CLI on host" + str( i ) )
            QuaggaCliHostX.enterConfig( 65000 + i - 100 )
            main.log.info( "Add routes to Quagga on host" + str( i ) )
            QuaggaCliHostX.addRoutes( prefixesHostX, 1 )

        time.sleep( 60 )

        # get routes inside SDN-IP
        getRoutesResult = main.ONOScli.routes( jsonFormat=True )

        # parse routes from ONOS CLI
        allRoutesActual = \
            main.QuaggaCliHost3.extractActualRoutes( getRoutesResult )

        allRoutesStrExpected = str( sorted( allRoutesExpected ) )
        allRoutesStrActual = str( allRoutesActual ).replace( 'u', "" )
        main.step( "Check routes installed" )
        main.log.info( "Routes expected:" )
        main.log.info( allRoutesStrExpected )
        main.log.info( "Routes get from ONOS CLI:" )
        main.log.info( allRoutesStrActual )
        utilities.assertEquals(
            expect=allRoutesStrExpected, actual=allRoutesStrActual,
            onpass="***Routes in SDN-IP are correct!***",
            onfail="***Routes in SDN-IP are wrong!***" )
        if( eq( allRoutesStrExpected, allRoutesStrActual ) ):
            main.log.report(
                "***Routes in SDN-IP after adding routes are correct!***" )
        else:
            main.log.report(
                "***Routes in SDN-IP after adding routes are wrong!***" )

        time.sleep( 20 )
        getIntentsResult = main.ONOScli.intents( jsonFormat=True )

        main.step( "Check MultiPointToSinglePointIntent intents installed" )
        # routeIntentsExpected are generated when generating routes
        # get rpoute intents from ONOS CLI
        routeIntentsActual = \
            main.QuaggaCliHost3.extractActualRouteIntents(
                getIntentsResult )
        routeIntentsStrExpected = str( sorted( routeIntentsExpected ) )
        routeIntentsStrActual = str( routeIntentsActual ).replace( 'u', "" )
        main.log.info( "MultiPointToSinglePoint intents expected:" )
        main.log.info( routeIntentsStrExpected )
        main.log.info( "MultiPointToSinglePoint intents get from ONOS CLI:" )
        main.log.info( routeIntentsStrActual )
        utilities.assertEquals(
            expect=True,
            actual=eq( routeIntentsStrExpected, routeIntentsStrActual ),
            onpass="***MultiPointToSinglePoint Intents in SDN-IP are \
            correct!***",
            onfail="***MultiPointToSinglePoint Intents in SDN-IP are \
            wrong!***" )

        if( eq( routeIntentsStrExpected, routeIntentsStrActual ) ):
            main.log.report(
                "***MultiPointToSinglePoint Intents before deleting routes \
                correct!***" )
        else:
            main.log.report(
                "***MultiPointToSinglePoint Intents before deleting routes \
                wrong!***" )

        main.step( "Check BGP PointToPointIntent intents installed" )
        # bgp intents expected
        bgpIntentsExpected = main.QuaggaCliHost3.generateExpectedBgpIntents(
            SDNIPJSONFILEPATH )
        # get BGP intents from ONOS CLI
        bgpIntentsActual = main.QuaggaCliHost3.extractActualBgpIntents(
            getIntentsResult )

        bgpIntentsStrExpected = str( bgpIntentsExpected ).replace( 'u', "" )
        bgpIntentsStrActual = str( bgpIntentsActual )
        main.log.info( "PointToPointIntent intents expected:" )
        main.log.info( bgpIntentsStrExpected )
        main.log.info( "PointToPointIntent intents get from ONOS CLI:" )
        main.log.info( bgpIntentsStrActual )

        utilities.assertEquals(
            expect=True,
            actual=eq( bgpIntentsStrExpected, bgpIntentsStrActual ),
            onpass="***PointToPointIntent Intents in SDN-IP are correct!***",
            onfail="***PointToPointIntent Intents in SDN-IP are wrong!***" )

        if ( eq( bgpIntentsStrExpected, bgpIntentsStrActual ) ):
            main.log.report(
                "***PointToPointIntent Intents in SDN-IP are correct!***" )
        else:
            main.log.report(
                "***PointToPointIntent Intents in SDN-IP are wrong!***" )

        #============================= Ping Test ========================
        # wait until all MultiPointToSinglePoint
        time.sleep( 20 )
        pingTestScript = "~/SDNIP/test-tools/CASE3-ping-as2host.sh"
        pingTestResultsFile = \
        "~/SDNIP/SdnIpIntentDemo/log/CASE3-ping-results-before-delete-routes-" \
            + strftime( "%Y-%m-%d_%H:%M:%S", localtime() ) + ".txt"
        pingTestResults = main.QuaggaCliHost.pingTest(
            "1.168.30.100", pingTestScript, pingTestResultsFile )
        main.log.info( pingTestResults )
        time.sleep( 20 )

        #============================= Deleting Routes ==================
        main.step( "Check deleting routes installed" )
        main.QuaggaCliHost3.deleteRoutes( prefixesHost3, 1 )
        main.QuaggaCliHost4.deleteRoutes( prefixesHost4, 1 )
        for i in range( 101, 201 ):
            prefixesHostX = \
                main.QuaggaCliHost.generatePrefixes( str( i ), 10 )
            main.log.info( prefixesHostX )
            QuaggaCliHostX = getattr( main, ( 'QuaggaCliHost' + str( i ) ) )
            QuaggaCliHostX.deleteRoutes( prefixesHostX, 1 )

        getRoutesResult = main.ONOScli.routes( jsonFormat=True )
        allRoutesActual = main.QuaggaCliHost3.extractActualRoutes(
            getRoutesResult )
        main.log.info( "allRoutes_actual = " )
        main.log.info( allRoutesActual )

        utilities.assertEquals(
            expect="[]", actual=str( allRoutesActual ),
            onpass="***Route number in SDN-IP is 0, correct!***",
            onfail="***Routes number in SDN-IP is not 0, wrong!***" )

        if( eq( allRoutesStrExpected, allRoutesStrActual ) ):
            main.log.report(
                "***Routes in SDN-IP after deleting correct!***" )
        else:
            main.log.report(
                "***Routes in SDN-IP after deleting wrong!***" )

        main.step( "Check intents after deleting routes" )
        getIntentsResult = main.ONOScli.intents( jsonFormat=True )
        routeIntentsActual = \
            main.QuaggaCliHost3.extractActualRouteIntents(
                getIntentsResult )
        main.log.info( "main.ONOScli.intents()= " )
        main.log.info( routeIntentsActual )
        utilities.assertEquals(
            expect="[]", actual=str( routeIntentsActual ),
            onpass="***MultiPointToSinglePoint Intents number in SDN-IP is \
            0, correct!***",
            onfail="***MultiPointToSinglePoint Intents number in SDN-IP is \
            0, wrong!***" )

        if( eq( routeIntentsStrExpected, routeIntentsStrActual ) ):
            main.log.report(
                "***MultiPointToSinglePoint Intents after deleting routes \
                correct!***" )
        else:
            main.log.report(
                "***MultiPointToSinglePoint Intents after deleting routes \
                wrong!***" )

        time.sleep( 20 )
        pingTestScript = "~/SDNIP/test-tools/CASE3-ping-as2host.sh"
        pingTestResultsFile = \
        "~/SDNIP/SdnIpIntentDemo/log/CASE3-ping-results-after-delete-routes-" \
            + strftime( "%Y-%m-%d_%H:%M:%S", localtime() ) + ".txt"
        pingTestResults = main.QuaggaCliHost.pingTest(
            "1.168.30.100", pingTestScript, pingTestResultsFile )
        main.log.info( pingTestResults )
        time.sleep( 100 )

        # main.step( "Test whether Mininet is started" )
        # main.Mininet2.handle.sendline( "xterm host1" )
        # main.Mininet2.handle.expect( "mininet>" )

    def CASE1( self, main ):
        """
        Test the SDN-IP functionality
        allRoutesExpected: all expected routes for all BGP peers
        routeIntentsExpected: all expected MultiPointToSinglePointIntent \
        intents
        bgpIntentsExpected: expected PointToPointIntent intents
        allRoutesActual: all routes from ONOS LCI
        routeIntentsActual: actual MultiPointToSinglePointIntent intents \
        from ONOS CLI
        bgpIntentsActual: actual PointToPointIntent intents from ONOS CLI
        """
        import time
        import json
        from operator import eq
        # from datetime import datetime
        from time import localtime, strftime

        main.case("The test case is to help to setup the TestON environment \
            and test new drivers" )
        SDNIPJSONFILEPATH = "../tests/SdnIpTest/sdnip.json"
        # all expected routes for all BGP peers
        allRoutesExpected = []
        main.step( "Start to generate routes for all BGP peers" )
        # bgpPeerHosts = []
        # for i in range( 3, 5 ):
        #    bgpPeerHosts.append( "host" + str( i ) )
        # main.log.info( "BGP Peer Hosts are:" + bgpPeerHosts )

        # for i in range( 3, 5 ):
         #   QuaggaCliHost = "QuaggaCliHost" + str( i )
          #  prefixes = main.QuaggaCliHost.generatePrefixes( 3, 10 )

           # main.log.info( prefixes )
            # allRoutesExpected.append( prefixes )
        main.log.info( "Generate prefixes for host3" )
        prefixesHost3 = main.QuaggaCliHost3.generatePrefixes( 3, 10 )
        main.log.info( prefixesHost3 )
        # generate route with next hop
        for prefix in prefixesHost3:
            allRoutesExpected.append( prefix + "/" + "192.168.20.1" )
        routeIntentsExpectedHost3 = \
            main.QuaggaCliHost3.generateExpectedOnePeerRouteIntents(
            prefixesHost3, "192.168.20.1", "00:00:00:00:02:02",
            SDNIPJSONFILEPATH )

        main.log.info( "Generate prefixes for host4" )
        prefixesHost4 = main.QuaggaCliHost4.generatePrefixes( 4, 10 )
        main.log.info( prefixesHost4 )
        # generate route with next hop
        for prefix in prefixesHost4:
            allRoutesExpected.append( prefix + "/" + "192.168.30.1" )
        routeIntentsExpectedHost4 = \
            main.QuaggaCliHost4.generateExpectedOnePeerRouteIntents(
            prefixesHost4, "192.168.30.1", "00:00:00:00:03:01",
            SDNIPJSONFILEPATH )

        routeIntentsExpected = routeIntentsExpectedHost3 + \
            routeIntentsExpectedHost4

        cellName = main.params[ 'ENV' ][ 'cellName' ]
        ONOS1Ip = main.params[ 'CTRL' ][ 'ip1' ]
        main.step( "Set cell for ONOS-cli environment" )
        main.ONOScli.setCell( cellName )
        verifyResult = main.ONOSbench.verifyCell()
        main.log.report( "Removing raft logs" )
        main.ONOSbench.onosRemoveRaftLogs()
        main.log.report( "Uninstalling ONOS" )
        main.ONOSbench.onosUninstall( ONOS1Ip )
        main.step( "Creating ONOS package" )
        packageResult = main.ONOSbench.onosPackage()

        main.step( "Starting ONOS service" )
        # TODO: start ONOS from Mininet Script
        # startResult = main.ONOSbench.onosStart( "127.0.0.1" )
        main.step( "Installing ONOS package" )
        onos1InstallResult = main.ONOSbench.onosInstall(
            options="-f", node=ONOS1Ip )

        main.step( "Checking if ONOS is up yet" )
        time.sleep( 60 )
        onos1Isup = main.ONOSbench.isup( ONOS1Ip )
        if not onos1Isup:
            main.log.report( "ONOS1 didn't start!" )

        main.step( "Start ONOS-cli" )
        # TODO: change the hardcode in startOnosCli method in ONOS CLI driver

        main.ONOScli.startOnosCli( ONOS1Ip )

        main.step( "Get devices in the network" )
        listResult = main.ONOScli.devices( jsonFormat=False )
        main.log.info( listResult )
        time.sleep( 10 )
        main.log.info( "Installing sdn-ip feature" )
        main.ONOScli.featureInstall( "onos-app-sdnip" )
        time.sleep( 10 )
        main.step( "Login all BGP peers and add routes into peers" )
        main.log.info( "Login Quagga CLI on host3" )
        main.QuaggaCliHost3.loginQuagga( "1.168.30.2" )
        main.log.info( "Enter configuration model of Quagga CLI on host3" )
        main.QuaggaCliHost3.enterConfig( 64514 )
        main.log.info( "Add routes to Quagga on host3" )
        main.QuaggaCliHost3.addRoutes( prefixesHost3, 1 )

        main.log.info( "Login Quagga CLI on host4" )
        main.QuaggaCliHost4.loginQuagga( "1.168.30.3" )
        main.log.info( "Enter configuration model of Quagga CLI on host4" )
        main.QuaggaCliHost4.enterConfig( 64516 )
        main.log.info( "Add routes to Quagga on host4" )
        main.QuaggaCliHost4.addRoutes( prefixesHost4, 1 )
        time.sleep( 60 )

        # get all routes inside SDN-IP
        getRoutesResult = main.ONOScli.routes( jsonFormat=True )

        # parse routes from ONOS CLI
        allRoutesActual = \
            main.QuaggaCliHost3.extractActualRoutes( getRoutesResult )

        allRoutesStrExpected = str( sorted( allRoutesExpected ) )
        allRoutesStrActual = str( allRoutesActual ).replace( 'u', "" )
        main.step( "Check routes installed" )
        main.log.info( "Routes expected:" )
        main.log.info( allRoutesStrExpected )
        main.log.info( "Routes get from ONOS CLI:" )
        main.log.info( allRoutesStrActual )
        utilities.assertEquals(
            expect=allRoutesStrExpected, actual=allRoutesStrActual,
            onpass="***Routes in SDN-IP are correct!***",
            onfail="***Routes in SDN-IP are wrong!***" )
        if( eq( allRoutesStrExpected, allRoutesStrActual ) ):
            main.log.report(
                "***Routes in SDN-IP after adding routes are correct!***" )
        else:
            main.log.report(
                "***Routes in SDN-IP after adding routes are wrong!***" )

        time.sleep( 20 )
        getIntentsResult = main.ONOScli.intents( jsonFormat=True )

        main.step( "Check MultiPointToSinglePointIntent intents installed" )
        # routeIntentsExpected are generated when generating routes
        # get rpoute intents from ONOS CLI
        routeIntentsActual = \
            main.QuaggaCliHost3.extractActualRouteIntents(
                getIntentsResult )
        routeIntentsStrExpected = str( sorted( routeIntentsExpected ) )
        routeIntentsStrActual = str( routeIntentsActual ).replace( 'u', "" )
        main.log.info( "MultiPointToSinglePoint intents expected:" )
        main.log.info( routeIntentsStrExpected )
        main.log.info( "MultiPointToSinglePoint intents get from ONOS CLI:" )
        main.log.info( routeIntentsStrActual )
        utilities.assertEquals(
            expect=True,
            actual=eq( routeIntentsStrExpected, routeIntentsStrActual ),
            onpass="***MultiPointToSinglePoint Intents in SDN-IP are \
            correct!***",
            onfail="***MultiPointToSinglePoint Intents in SDN-IP are \
            wrong!***" )

        if( eq( routeIntentsStrExpected, routeIntentsStrActual ) ):
            main.log.report(
                "***MultiPointToSinglePoint Intents before deleting routes \
                correct!***" )
        else:
            main.log.report(
                "***MultiPointToSinglePoint Intents before deleting routes \
                wrong!***" )

        main.step( "Check BGP PointToPointIntent intents installed" )
        # bgp intents expected
        bgpIntentsExpected = \
            main.QuaggaCliHost3.generateExpectedBgpIntents( SDNIPJSONFILEPATH )
        # get BGP intents from ONOS CLI
        bgpIntentsActual = main.QuaggaCliHost3.extractActualBgpIntents(
            getIntentsResult )

        bgpIntentsStrExpected = str( bgpIntentsExpected ).replace( 'u', "" )
        bgpIntentsStrActual = str( bgpIntentsActual )
        main.log.info( "PointToPointIntent intents expected:" )
        main.log.info( bgpIntentsStrExpected )
        main.log.info( "PointToPointIntent intents get from ONOS CLI:" )
        main.log.info( bgpIntentsStrActual )

        utilities.assertEquals(
            expect=True,
            actual=eq( bgpIntentsStrExpected, bgpIntentsStrActual ),
            onpass="***PointToPointIntent Intents in SDN-IP are correct!***",
            onfail="***PointToPointIntent Intents in SDN-IP are wrong!***" )

        if ( eq( bgpIntentsStrExpected, bgpIntentsStrActual ) ):
            main.log.report(
                "***PointToPointIntent Intents in SDN-IP are correct!***" )
        else:
            main.log.report(
                "***PointToPointIntent Intents in SDN-IP are wrong!***" )

        #============================= Ping Test ========================
        # wait until all MultiPointToSinglePoint
        time.sleep( 20 )
        pingTestScript = "~/SDNIP/SdnIpIntentDemo/CASE1-ping-as2host.sh"
        pingTestResultsFile = \
        "~/SDNIP/SdnIpIntentDemo/log/CASE1-ping-results-before-delete-routes-" \
             + strftime( "%Y-%m-%d_%H:%M:%S", localtime() ) + ".txt"
        pingTestResults = main.QuaggaCliHost.pingTest(
            "1.168.30.100", pingTestScript, pingTestResultsFile )
        main.log.info( pingTestResults )

        # ping test

        #============================= Deleting Routes ==================
        main.step( "Check deleting routes installed" )
        main.QuaggaCliHost3.deleteRoutes( prefixesHost3, 1 )
        main.QuaggaCliHost4.deleteRoutes( prefixesHost4, 1 )

        # main.log.info( "main.ONOScli.get_routes_num() = " )
        # main.log.info( main.ONOScli.getRoutesNum() )
        # utilities.assertEquals( expect="Total SDN-IP routes = 1", actual=
        # main.ONOScli.getRoutesNum(),
        getRoutesResult = main.ONOScli.routes( jsonFormat=True )
        allRoutesActual = \
            main.QuaggaCliHost3.extractActualRoutes( getRoutesResult )
        main.log.info( "allRoutes_actual = " )
        main.log.info( allRoutesActual )

        utilities.assertEquals(
            expect="[]", actual=str( allRoutesActual ),
            onpass="***Route number in SDN-IP is 0, correct!***",
            onfail="***Routes number in SDN-IP is not 0, wrong!***" )

        if( eq( allRoutesStrExpected, allRoutesStrActual ) ):
            main.log.report(
                "***Routes in SDN-IP after deleting correct!***" )
        else:
            main.log.report(
                "***Routes in SDN-IP after deleting wrong!***" )

        main.step( "Check intents after deleting routes" )
        getIntentsResult = main.ONOScli.intents( jsonFormat=True )
        routeIntentsActual = \
            main.QuaggaCliHost3.extractActualRouteIntents(
                getIntentsResult )
        main.log.info( "main.ONOScli.intents()= " )
        main.log.info( routeIntentsActual )
        utilities.assertEquals(
            expect="[]", actual=str( routeIntentsActual ),
            onpass="***MultiPointToSinglePoint Intents number in SDN-IP is \
            0, correct!***",
            onfail="***MultiPointToSinglePoint Intents number in SDN-IP is \
            0, wrong!***" )

        if( eq( routeIntentsStrExpected, routeIntentsStrActual ) ):
            main.log.report(
                "***MultiPointToSinglePoint Intents after deleting routes \
                correct!***" )
        else:
            main.log.report(
                "***MultiPointToSinglePoint Intents after deleting routes \
                wrong!***" )

        time.sleep( 20 )
        pingTestScript = "~/SDNIP/SdnIpIntentDemo/CASE1-ping-as2host.sh"
        pingTestResultsFile = \
        "~/SDNIP/SdnIpIntentDemo/log/CASE1-ping-results-after-delete-routes-" \
             + strftime( "%Y-%m-%d_%H:%M:%S", localtime() ) + ".txt"
        pingTestResults = main.QuaggaCliHost.pingTest(
            "1.168.30.100", pingTestScript, pingTestResultsFile )
        main.log.info( pingTestResults )
        time.sleep( 30 )

        # main.step( "Test whether Mininet is started" )
        # main.Mininet2.handle.sendline( "xterm host1" )
        # main.Mininet2.handle.expect( "mininet>" )

    def CASE2( self, main ):
        """
        Test the SDN-IP functionality
        allRoutesExpected: all expected routes for all BGP peers
        routeIntentsExpected: all expected MultiPointToSinglePointIntent \
        intents
        bgpIntentsExpected: expected PointToPointIntent intents
        allRoutesActual: all routes from ONOS LCI
        routeIntentsActual: actual MultiPointToSinglePointIntent intents \
        from ONOS CLI
        bgpIntentsActual: actual PointToPointIntent intents from ONOS CLI
        """
        import time
        import json
        from operator import eq
        from time import localtime, strftime

        main.case(
            "The test case is to help to setup the TestON environment and \
            test new drivers" )
        SDNIPJSONFILEPATH = "../tests/SdnIpTest/sdnip.json"
        # all expected routes for all BGP peers
        allRoutesExpected = []
        main.step( "Start to generate routes for all BGP peers" )

        main.log.info( "Generate prefixes for host3" )
        prefixesHost3 = main.QuaggaCliHost3.generatePrefixes( 3, 10 )
        main.log.info( prefixesHost3 )
        # generate route with next hop
        for prefix in prefixesHost3:
            allRoutesExpected.append( prefix + "/" + "192.168.20.1" )
        routeIntentsExpectedHost3 = \
            main.QuaggaCliHost3.generateExpectedOnePeerRouteIntents(
            prefixesHost3, "192.168.20.1", "00:00:00:00:02:02",
            SDNIPJSONFILEPATH )

        main.log.info( "Generate prefixes for host4" )
        prefixesHost4 = main.QuaggaCliHost4.generatePrefixes( 4, 10 )
        main.log.info( prefixesHost4 )
        # generate route with next hop
        for prefix in prefixesHost4:
            allRoutesExpected.append( prefix + "/" + "192.168.30.1" )
        routeIntentsExpectedHost4 = \
            main.QuaggaCliHost4.generateExpectedOnePeerRouteIntents(
            prefixesHost4, "192.168.30.1", "00:00:00:00:03:01",
            SDNIPJSONFILEPATH )

        routeIntentsExpected = routeIntentsExpectedHost3 + \
            routeIntentsExpectedHost4

        main.log.report( "Removing raft logs" )
        main.ONOSbench.onosRemoveRaftLogs()
        main.log.report( "Uninstalling ONOS" )
        main.ONOSbench.onosUninstall( ONOS1Ip )

        cellName = main.params[ 'ENV' ][ 'cellName' ]
        ONOS1Ip = main.params[ 'CTRL' ][ 'ip1' ]
        main.step( "Set cell for ONOS-cli environment" )
        main.ONOScli.setCell( cellName )
        verifyResult = main.ONOSbench.verifyCell()
        # main.log.report( "Removing raft logs" )
        # main.ONOSbench.onosRemoveRaftLogs()
        # main.log.report( "Uninstalling ONOS" )
        # main.ONOSbench.onosUninstall( ONOS1Ip )
        main.step( "Creating ONOS package" )
        # packageResult = main.ONOSbench.onosPackage()

        main.step( "Installing ONOS package" )
        # onos1InstallResult = main.ONOSbench.onosInstall( options="-f",
        # node=ONOS1Ip )

        main.step( "Checking if ONOS is up yet" )
        # time.sleep( 60 )
        onos1Isup = main.ONOSbench.isup( ONOS1Ip )
        if not onos1Isup:
            main.log.report( "ONOS1 didn't start!" )

        main.step( "Start ONOS-cli" )
        main.ONOScli.startOnosCli( ONOS1Ip )

        main.step( "Get devices in the network" )
        listResult = main.ONOScli.devices( jsonFormat=False )
        main.log.info( listResult )
        time.sleep( 10 )
        main.log.info( "Installing sdn-ip feature" )
        main.ONOScli.featureInstall( "onos-app-sdnip" )
        time.sleep( 10 )

        main.step( "Check BGP PointToPointIntent intents installed" )
        # bgp intents expected
        bgpIntentsExpected = main.QuaggaCliHost3.generateExpectedBgpIntents(
            SDNIPJSONFILEPATH )
        # get BGP intents from ONOS CLI
        getIntentsResult = main.ONOScli.intents( jsonFormat=True )
        bgpIntentsActual = main.QuaggaCliHost3.extractActualBgpIntents(
            getIntentsResult )

        bgpIntentsStrExpected = str( bgpIntentsExpected ).replace( 'u', "" )
        bgpIntentsStrActual = str( bgpIntentsActual )
        main.log.info( "PointToPointIntent intents expected:" )
        main.log.info( bgpIntentsStrExpected )
        main.log.info( "PointToPointIntent intents get from ONOS CLI:" )
        main.log.info( bgpIntentsStrActual )

        utilities.assertEquals(
            expect=True,
            actual=eq( bgpIntentsStrExpected, bgpIntentsStrActual ),
            onpass="***PointToPointIntent Intents in SDN-IP are correct!***",
            onfail="***PointToPointIntent Intents in SDN-IP are wrong!***" )

        if ( eq( bgpIntentsStrExpected, bgpIntentsStrActual ) ):
            main.log.report(
                "***PointToPointIntent Intents in SDN-IP are correct!***" )
        else:
            main.log.report(
                "***PointToPointIntent Intents in SDN-IP are wrong!***" )

        allRoutesStrExpected = str( sorted( allRoutesExpected ) )
        routeIntentsStrExpected = str( sorted( routeIntentsExpected ) )
        pingTestScript = "~/SDNIP/SdnIpIntentDemo/CASE1-ping-as2host.sh"
        # roundNum = 0;
        # while( True ):
        for roundNum in range( 1, 6 ):
            # round = round + 1;
            main.log.report( "The Round " + str( roundNum ) +
                             " test starts................................" )

            main.step( "Login all BGP peers and add routes into peers" )
            main.log.info( "Login Quagga CLI on host3" )
            main.QuaggaCliHost3.loginQuagga( "1.168.30.2" )
            main.log.info(
                "Enter configuration model of Quagga CLI on host3" )
            main.QuaggaCliHost3.enterConfig( 64514 )
            main.log.info( "Add routes to Quagga on host3" )
            main.QuaggaCliHost3.addRoutes( prefixesHost3, 1 )

            main.log.info( "Login Quagga CLI on host4" )
            main.QuaggaCliHost4.loginQuagga( "1.168.30.3" )
            main.log.info(
                "Enter configuration model of Quagga CLI on host4" )
            main.QuaggaCliHost4.enterConfig( 64516 )
            main.log.info( "Add routes to Quagga on host4" )
            main.QuaggaCliHost4.addRoutes( prefixesHost4, 1 )
            time.sleep( 60 )

            # get all routes inside SDN-IP
            getRoutesResult = main.ONOScli.routes( jsonFormat=True )

            # parse routes from ONOS CLI
            allRoutesActual = \
                main.QuaggaCliHost3.extractActualRoutes( getRoutesResult )

            # allRoutesStrExpected = str( sorted( allRoutesExpected ) )
            allRoutesStrActual = str( allRoutesActual ).replace( 'u', "" )
            main.step( "Check routes installed" )
            main.log.info( "Routes expected:" )
            main.log.info( allRoutesStrExpected )
            main.log.info( "Routes get from ONOS CLI:" )
            main.log.info( allRoutesStrActual )
            utilities.assertEquals(
                expect=allRoutesStrExpected, actual=allRoutesStrActual,
                onpass="***Routes in SDN-IP are correct!***",
                onfail="***Routes in SDN-IP are wrong!***" )
            if( eq( allRoutesStrExpected, allRoutesStrActual ) ):
                main.log.report(
                    "***Routes in SDN-IP after adding correct!***" )
            else:
                main.log.report(
                    "***Routes in SDN-IP after adding wrong!***" )

            time.sleep( 20 )
            getIntentsResult = main.ONOScli.intents( jsonFormat=True )

            main.step(
                "Check MultiPointToSinglePointIntent intents installed" )
            # routeIntentsExpected are generated when generating routes
            # get route intents from ONOS CLI
            routeIntentsActual = \
                main.QuaggaCliHost3.extractActualRouteIntents(
                    getIntentsResult )
            # routeIntentsStrExpected = str( sorted( routeIntentsExpected ) )
            routeIntentsStrActual = str(
                routeIntentsActual ).replace( 'u', "" )
            main.log.info( "MultiPointToSinglePoint intents expected:" )
            main.log.info( routeIntentsStrExpected )
            main.log.info(
                "MultiPointToSinglePoint intents get from ONOS CLI:" )
            main.log.info( routeIntentsStrActual )
            utilities.assertEquals(
                expect=True,
                actual=eq( routeIntentsStrExpected, routeIntentsStrActual ),
                onpass="***MultiPointToSinglePoint Intents in SDN-IP are \
                correct!***",
                onfail="***MultiPointToSinglePoint Intents in SDN-IP are \
                wrong!***" )

            if( eq( routeIntentsStrExpected, routeIntentsStrActual ) ):
                main.log.report(
                    "***MultiPointToSinglePoint Intents after adding routes \
                    correct!***" )
            else:
                main.log.report(
                    "***MultiPointToSinglePoint Intents after adding routes \
                    wrong!***" )

            #============================= Ping Test ========================
            # wait until all MultiPointToSinglePoint
            time.sleep( 20 )
            # pingTestScript = "~/SDNIP/SdnIpIntentDemo/CASE1-ping-as2host.sh"
            pingTestResultsFile = \
                "~/SDNIP/SdnIpIntentDemo/log/CASE2-Round" \
                + str( roundNum ) + "-ping-results-before-delete-routes-" \
                + strftime( "%Y-%m-%d_%H:%M:%S", localtime() ) + ".txt"
            pingTestResults = main.QuaggaCliHost.pingTest(
                "1.168.30.100", pingTestScript, pingTestResultsFile )
            main.log.info( pingTestResults )
            # ping test

            #============================= Deleting Routes ==================
            main.step( "Check deleting routes installed" )
            main.log.info( "Delete routes to Quagga on host3" )
            main.QuaggaCliHost3.deleteRoutes( prefixesHost3, 1 )
            main.log.info( "Delete routes to Quagga on host4" )
            main.QuaggaCliHost4.deleteRoutes( prefixesHost4, 1 )

            getRoutesResult = main.ONOScli.routes( jsonFormat=True )
            allRoutesActual = \
                main.QuaggaCliHost3.extractActualRoutes( getRoutesResult )
            main.log.info( "allRoutes_actual = " )
            main.log.info( allRoutesActual )

            utilities.assertEquals(
                expect="[]", actual=str( allRoutesActual ),
                onpass="***Route number in SDN-IP is 0, correct!***",
                onfail="***Routes number in SDN-IP is not 0, wrong!***" )

            if( eq( allRoutesStrExpected, allRoutesStrActual ) ):
                main.log.report(
                    "***Routes in SDN-IP after deleting correct!***" )
            else:
                main.log.report(
                    "***Routes in SDN-IP after deleting wrong!***" )

            main.step( "Check intents after deleting routes" )
            getIntentsResult = main.ONOScli.intents( jsonFormat=True )
            routeIntentsActual = \
                main.QuaggaCliHost3.extractActualRouteIntents(
                    getIntentsResult )
            main.log.info( "main.ONOScli.intents()= " )
            main.log.info( routeIntentsActual )
            utilities.assertEquals(
                expect="[]", actual=str( routeIntentsActual ),
                onpass=
                "***MultiPointToSinglePoint Intents number in SDN-IP \
                is 0, correct!***",
                onfail="***MultiPointToSinglePoint Intents number in SDN-IP \
                is 0, wrong!***" )

            if( eq( routeIntentsStrExpected, routeIntentsStrActual ) ):
                main.log.report(
                    "***MultiPointToSinglePoint Intents after deleting \
                    routes correct!***" )
            else:
                main.log.report(
                    "***MultiPointToSinglePoint Intents after deleting \
                    routes wrong!***" )

            time.sleep( 20 )
            # pingTestScript = "~/SDNIP/SdnIpIntentDemo/CASE1-ping-as2host.sh"
            pingTestResultsFile = \
                "~/SDNIP/SdnIpIntentDemo/log/CASE2-Round" \
                + str( roundNum ) + "-ping-results-after-delete-routes-" \
                + strftime( "%Y-%m-%d_%H:%M:%S", localtime() ) + ".txt"
            pingTestResults = main.QuaggaCliHost.pingTest(
                "1.168.30.100", pingTestScript, pingTestResultsFile )
            main.log.info( pingTestResults )
            time.sleep( 30 )

