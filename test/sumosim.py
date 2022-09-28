#!/usr/bin/python

"""Sample file for SUMO

***Requirements***:

Kernel version: 5.8+ (due to the 802.11p support)
sumo 1.5.0 or higher
sumo-gui"""

from mininet.log import setLogLevel, info
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi
from mn_wifi.sumo.runner import sumo
from mn_wifi.link import wmediumd, ITSLink
from mn_wifi.wmediumdConnector import interference

from time import time
from mininet.node import Controller, OVSKernelSwitch, Host, RemoteController, OVSSwitch
from mininet.log import setLogLevel, info
from mn_wifi.net import Mininet_wifi
from mn_wifi.node import Station, OVSKernelAP
from subprocess import call


def topology():
    """
    It creates a network, adds a controller, adds switches, adds access points, adds stations,
    configures the network, and then starts the network
    """

    "Create a network."
    net = Mininet_wifi(link=wmediumd, wmediumd_mode=interference, switch=OVSSwitch)

    info( '*** Adding controller\n' )
    c0 = net.addController(name='c0',
                           controller=RemoteController,
                           ip='127.0.0.1',
                           protocols="OpenFlow13",
                           port=6653)


    info("*** Creating nodes\n")
    for i in range (1,201):
        net.addCar('car'+str(i), ip='10.0.16.'+str(i)+'/16', range=50)

    info( '*** Add switches/APs\n')
    ap1 = net.addAccessPoint('ap1', ssid='ap1-ssid',
                             channel='6', mode='g', position='1350,796,0', range=200)

    ap2 = net.addAccessPoint('ap2', ssid='ap2-ssid',
                             channel='6', mode='g', position='1515,495.0,0', range=200)

    ap3 = net.addAccessPoint('ap3', ssid='ap3-ssid',
                             channel='6', mode='g', position='1223,1016,0', range=200)

    ap4 = net.addAccessPoint('ap4', ssid='ap4-ssid',
                             channel='6', mode='g', position='1755,1174.0,0', range=200)

    info( '*** Add switches/APs\n')
    ap5 = net.addAccessPoint('ap5', ssid='ap5-ssid',
                             channel='6', mode='g', position='1975,803,0', range=200)

    ap6 = net.addAccessPoint('ap6', ssid='ap6-ssid',
                             channel='6', mode='g', position='1470,1090.0,0', range=200)

    ap7 = net.addAccessPoint('ap7', ssid='ap7-ssid',
                             channel='6', mode='g', position='847,441,0', range=200)

    ap8 = net.addAccessPoint('ap8', ssid='ap8-ssid',
                             channel='6', mode='g', position='2238,959.0,0', range=200)



    s1 = net.addSwitch('s1')
    s2 = net.addSwitch('s2')
    s3 = net.addSwitch('s3')
    s4 = net.addSwitch('s4')

    info( '*** Add hosts/stations\n')
    sta1 = net.addStation('sta1', ip='10.0.8.1/16',
                           position='1355,796,0', range=100)
    sta2 = net.addStation('sta2', ip='10.0.8.2/16',
                           position='1520,495.0,0', range=100)


    sta3 = net.addStation('sta3', ip='10.0.8.3/16',
                           position='1225,1016,0', range=100)
    sta4 = net.addStation('sta4', ip='10.0.8.4/16',
                           position='1755,1175.0,0', range=100)


    h1 = net.addHost('h1', cls=Host, ip='10.0.0.1/16', defaultRoute=None)

    info("*** Configuring Propagation Model\n")
    net.setPropagationModel(model="logDistance", exp=2.8)

    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()

    info( '*** Add links\n')
    #net.addLink(ap1, sta1)
    net.addLink(ap2, sta2)
    net.addLink(ap3, sta3)
    net.addLink(ap4, sta4)


    net.addLink(s3, ap1)
    net.addLink(s4, ap2)
    net.addLink(s3, ap3)
    net.addLink(s4, ap4)

    net.addLink(s1, ap5)
    net.addLink(s2, ap6)
    net.addLink(s1, ap7)
    net.addLink(s2, ap8)



    net.addLink(h1, s1)

    net.addLink(s1, s2)

    net.addLink(s1, s3)
    net.addLink(s2, s4)

    print(net.cars)
    # exec_order: Tells TraCI to give the current
    # client the given position in the execution order.
    # We may have to change it from 0 to 1 if we want to
    # load/reload the current simulation from a 2nd client
    net.useExternalProgram(program=sumo, port=8813,
                           #config_file='map.sumocfg', # optional
                           config_file='./map/osm.sumocfg',
                           #extra_params=["--delay 1000"],
                           extra_params=["--delay 1000 --lateral-resolution 1"],
                           #clients=1, exec_order=0)
                           clients=2, exec_order=0)

    info("*** Starting network\n")
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches/APs\n')

    for ap in net.aps:
        net.get(ap.name).start([c0])

    net.get('s1').start([c0])
    net.get('s2').start([c0])
    net.get('s3').start([c0])
    net.get('s4').start([c0])

    # Track the position of the nodes
    nodes = net.cars + net.aps #+ net.stations
    net.telemetry(nodes=nodes, data_type='position',
                  min_x=-97, min_y=-72,
                  max_x=2511, max_y=1410)

    sta3.cmd("echo '0' > /proc/sys/net/ipv4/icmp_echo_ignore_broadcasts")
    sta2.cmd("echo '0' > /proc/sys/net/ipv4/icmp_echo_ignore_broadcasts")
    sta1.cmd("echo '0' > /proc/sys/net/ipv4/icmp_echo_ignore_broadcasts")
    sta4.cmd("echo '0' > /proc/sys/net/ipv4/icmp_echo_ignore_broadcasts")

    # A loop that is used to set the broadcast of the cars to 0.
    for c in net.cars:
        if c.name != "car1":
            c.cmd("echo '0' > /proc/sys/net/ipv4/icmp_echo_ignore_broadcasts")

    net.pingAll()

    info("*** Running CLI\n")
    test = True
    dis = {}
    flag = True
    #flag = False
    last = ""
    conn=""
    c1 = net.get("car1")
    
    # A loop that is used to check the distance between the car and the APs.
    while flag :
        #print(c1.position)
        for ap in net.aps :
            dis[ap] = c1.get_distance_to(ap)

        res = sorted(dis.items(), key=lambda t: t[1])


        fin = res[1][0]
        #print(fin)
        if fin != conn and fin != last:
            # Used to send a message to the car that is the closest to the car1.
            if dis[res[0][0]] <40 and test:
                #print(conn)
                for c in net.cars:
                    try:
                        if c.name != "car1":
                            c.cmd("python3.8 carsdata.py " + c.name + " &")
                    except:
                        continue
                cmd = "python3.8 sendudp.py " + fin.dpid
                #add the lane 
                try:
                    c1.cmd(cmd) 
                    print("envoi du message")
                    
                except:
                    print("Something else went wrong") 
                    flag = False
                    continue
                net.pingAll()
                cmd = "ping -c 7 10.0.255.255 -b"

                c1.cmdPrint(cmd)
                test = False
                last = fin
                conn = res[0][0]
        else :
            test = True
            #flag = False
    print(sta1.cmd("iw dev sta1-wlan0 link | grep SSID"))
    CLI(net)
    info("*** Stopping network\n")
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    topology()


