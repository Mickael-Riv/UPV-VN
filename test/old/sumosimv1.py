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

    "Create a network."
    net = Mininet_wifi(link=wmediumd, wmediumd_mode=interference, switch=OVSSwitch)

    info( '*** Adding controller\n' )
    c0 = net.addController(name='c0',
                           controller=RemoteController,
                           ip='127.0.0.1',
                           protocols="OpenFlow13",
                           port=6653)


    info("*** Creating nodes\n")
    for i in range (1,20):
        net.addCar('car'+str(i), ip='10.0.16.'+str(i)+'/16', range=50)

    #c1 = net.addCar('car1',ip='10.0.16.1/16', range=50)
    #c2 = net.addCar('car2',ip='10.0.16.2/16', range=50)
    #c3 = net.addCar('car3',ip='10.0.16.3/16', range=50)
    #c4 = net.addCar('car4',ip='10.0.16.4/16', range=50)
    #c5 = net.addCar('car5',ip='10.0.16.5/16', range=50)
    #c6 = net.addCar('car6',ip='10.0.16.6/16', range=50)
    #c7 = net.addCar('car7',ip='10.0.16.7/16', range=50)
    #c8 = net.addCar('car8',ip='10.0.16.8/16', range=50)
    #c9 = net.addCar('car9',ip='10.0.16.9/16', range=50)
    #c10 = net.addCar('car10',ip='10.0.16.10/16', range=50)

    info( '*** Add switches/APs\n')
    ap1 = net.addAccessPoint('ap1', ssid='ap1-ssid',
                             channel='6', mode='g', position='0,0,0', range=200)

    ap2 = net.addAccessPoint('ap2', ssid='ap2-ssid',
                             channel='6', mode='g', position='0,1200.0,0', range=200)

    ap3 = net.addAccessPoint('ap3', ssid='ap3-ssid',
                             channel='6', mode='g', position='1200,0,0', range=200)

    ap4 = net.addAccessPoint('ap4', ssid='ap4-ssid',
                             channel='6', mode='g', position='1200,1200.0,0', range=200)

    info( '*** Add switches/APs\n')
    ap5 = net.addAccessPoint('ap5', ssid='ap5-ssid',
                             channel='6', mode='g', position='0,600,0', range=200)

    ap6 = net.addAccessPoint('ap6', ssid='ap6-ssid',
                             channel='6', mode='g', position='600,1200.0,0', range=200)

    ap7 = net.addAccessPoint('ap7', ssid='ap7-ssid',
                             channel='6', mode='g', position='1200,600,0', range=200)

    ap8 = net.addAccessPoint('ap8', ssid='ap8-ssid',
                             channel='6', mode='g', position='600,0.0,0', range=200)



    s1 = net.addSwitch('s1')
    s2 = net.addSwitch('s2')
    s3 = net.addSwitch('s3')
    s4 = net.addSwitch('s4')

    info( '*** Add hosts/stations\n')
    sta1 = net.addStation('sta1', ip='10.0.8.1/16',
                           position='0,10,0', range=100)
    sta2 = net.addStation('sta2', ip='10.0.8.2/16',
                           position='0,1210,0', range=100)


    sta3 = net.addStation('sta3', ip='10.0.8.3/16',
                           position='1200,10,0', range=100)
    sta4 = net.addStation('sta4', ip='10.0.8.4/16',
                           position='1200,1210.0,0', range=100)


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
                           config_file='road.sumocfg',
                           #extra_params=["--start --delay 1000"],
                           extra_params=["--delay 1000 --lateral-resolution 1"],
                           clients=2, exec_order=0)

    info("*** Starting network\n")
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches/APs\n')
    #net.get('ap1').start([c0])
    #net.get('ap2').start([c0])
    #net.get('ap3').start([c0])
    #net.get('ap4').start([c0])
    for ap in net.aps:
        net.get(ap.name).start([c0])

    net.get('s1').start([c0])
    net.get('s2').start([c0])
    net.get('s3').start([c0])
    net.get('s4').start([c0])

    # Track the position of the nodes
    nodes = net.cars + net.aps #+ net.stations
    net.telemetry(nodes=nodes, data_type='position',
                  min_x=-100, min_y=-100,
                  max_x=1300, max_y=1300)

    sta3.cmd("echo '0' > /proc/sys/net/ipv4/icmp_echo_ignore_broadcasts")
    sta2.cmd("echo '0' > /proc/sys/net/ipv4/icmp_echo_ignore_broadcasts")
    sta1.cmd("echo '0' > /proc/sys/net/ipv4/icmp_echo_ignore_broadcasts")
    sta4.cmd("echo '0' > /proc/sys/net/ipv4/icmp_echo_ignore_broadcasts")

    #c2.cmd("echo '0' > /proc/sys/net/ipv4/icmp_echo_ignore_broadcasts")
    #c3.cmd("echo '0' > /proc/sys/net/ipv4/icmp_echo_ignore_broadcasts")
    #c4.cmd("echo '0' > /proc/sys/net/ipv4/icmp_echo_ignore_broadcasts")
    for c in net.cars:
        if c.name != "car1":
            c.cmd("echo '0' > /proc/sys/net/ipv4/icmp_echo_ignore_broadcasts")
            c.cmd("python3.8 topo-sumo.py " + c.name + " &")

    net.pingAll()

    info("*** Running CLI\n")
    test = True
    dis = {}
    flag = True
    #flag = False
    last = ""
    conn=""
    while flag :
        #print(c1.position)
        for ap in net.aps :
            #dis.append(c1.get_distance_to(ap))
            c1 = net.get("car1")
            dis[ap] = c1.get_distance_to(ap)
        #dis.sort()
        res = sorted(dis.items(), key=lambda t: t[1])

        #fin = list(dis.keys())[1]
        fin = res[1][0]
        #print(fin)
        #if fin == ap3 and fin != last:
        if fin != conn and fin != last:
            #region old 
            #c1.waiting = False
            #conn = str(c1.cmd("iw dev car1-wlan0 link | grep SSID"))
            #c1.monitor()
            #conn.replace(" ","") 
            #print(conn)
            #print(len(conn))
            #print(fin.params['ssid'])
            #if conn != "":
            #    try:
            #        conn = conn.split(':')[1]
            #    except:
            #        print("Something went wrong") 
            #        flag = False
            #else:
            #    test = False
                #flag = False
            #if test and (fin.params['ssid'] != conn):
            #endregion old
            if dis[res[0][0]] <20 and test:
                #print(conn)
                cmd = "python3.8 test.py " + fin.dpid
                try:
                    c1.cmd(cmd) # a regler, doit exec une seul fois
                    print("envoi du message")
                    
                except:
                    print("Something else went wrong") 
                    flag = False
                #net.pingAll()
                net.pingAll()
                cmd = "ping -c 5 10.0.255.255 -b"
                #c1.monitor()
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


