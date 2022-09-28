from ryu.base import app_manager
from ryu.controller import ofp_event, network, dpset
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib.packet import ether_types
from ryu.lib.packet import ethernet, ipv4, arp, udp, in_proto
from ryu.lib.packet import packet
from ryu.ofproto import ofproto_v1_3

from ryu.lib import dpid as dpid_lib
from ryu.lib import stplib
from ryu.topology.api import get_switch, get_link
from ryu.app.wsgi import ControllerBase
from ryu.topology import event, switches
from ryu.ofproto.ofproto_v1_2 import OFPG_ANY
import networkx as nx
import random
import ryu.app.ofctl.api as ofctl_api
import datetime, threading
import time


class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.topology_api_app = self
        self.net = nx.DiGraph()
        self.nodes = []
        self.val = 0
        self.links_list = []
        self.ambu = ""
        self.tic = None
        self.toc = None

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER) #creation of switches first flow
    def switch_features_handler(self, ev):
        """
        The switch_features_handler function is called when the switch connects to the controller. It adds a
        flow entry to the switch's flow table that matches all packets and sends them to the controller.
        
        :param ev: the event object
        """
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None): #Function to add flow
        """
        The function takes in a datapath, priority, match, actions, and buffer_id. It then creates an
        instruction and a flow modification. The flow modification is then sent to the datapath.
        
        :param datapath: the switch object
        :param priority: The priority of the flow
        :param match: The match fields to match against
        :param actions: The actions to be taken on the packet
        :param buffer_id: The buffer ID assigned by the switch
        """
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, #instruction
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id, #Match instruc
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod) #send the flow

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER) #when packet enter
    def _packet_in_handler(self, ev):
        """
        It's a packet_in handler
        
        :param ev: the event object
        :return: the shortest path between two nodes in a graph.
        """
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg #get the message
        datapath = msg.datapath #get the object
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port'] #in port

        pkt = packet.Packet(msg.data) #the data packet
        eth = pkt.get_protocols(ethernet.ethernet)[0] #the protocol packet

        if eth.ethertype == ether_types.ETH_TYPE_LLDP: #check protocol
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src

        dpid = datapath.id #get the object id
        self.mac_to_port.setdefault(dpid, {})

        #self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port #created of an database

# The above code is finding the shortest path between the source and destination.
        if src not in self.net: #creation of a graph of the network
            self.net.add_node(src)
            self.net.add_edge(dpid, src, port=in_port)
            self.net.add_edge(src, dpid)

        if dst in self.net:
            path = nx.shortest_path(self.net, src, dst)
            #print(path)
            next = path[path.index(dpid) + 1]
            out_port = self.net[dpid][next]['port']

        else:
            out_port = ofproto.OFPP_FLOOD #send as a broadcast

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:

            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)#, eth_src=src)

            if eth.ethertype == ether_types.ETH_TYPE_IP: #check if is an IP protocol
                ip = pkt.get_protocol(ipv4.ipv4)
                srcip = ip.src #get ip's
                dstip = ip.dst
                protocol = ip.proto

                #self.logger.info("packet in %s %s %s %s", dpid, srcip, dstip, in_port)

                match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,ip_proto = protocol, ipv4_src=srcip, ipv4_dst=dstip) #on passe tout en ip

                self.add_flow(datapath, 1, match, actions)



# The above code is sending the packet out of the switch.
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

        #print("**********NODES**************")
        if eth.ethertype == ether_types.ETH_TYPE_IP:
                ip = pkt.get_protocol(ipv4.ipv4)
                srcip = ip.src
                dstip = ip.dst
                protocol = ip.proto

                #self.logger.info("packet in %s %s %s %s", dpid, srcip, dstip, in_port) #pour afficher les paquets a destination inconnu par le réseau
                # A function that is called when a packet is received. It is used to get the next
                # destination of the ambulance.
                if protocol == in_proto.IPPROTO_UDP:
                    u = pkt.get_protocol(udp.udp) #if we have an UDP packet
                    print("#########UDP Packet!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                   
                    print("-----------------MESSAGE------------------------")
                    print(str(pkt).split('sortie:')[1]) #we get the value of the sortie field
                    val = str(pkt).split('sortie:')[1]
                    if val[0] != "c": #useless
                        self.val = int(val[:-1],16) #val = our next destination
                        self.ambu = src #ambulance = the sender
                        #self.remove_flows(datapath,0)
                        self.newflow(datapath, parser) #regenerate flow

        #print(self.nodes)
        self.create_route_4(datapath, src)


    def create_route_4(self, datapath, src):
        """
        It checks if the source is an ambulance, if it is, it sets the destination to the hospital,
        otherwise it sets the destination to a random node.
        
        :param datapath: the switch object
        :param src: the source MAC address of the packet
        """
        parser = datapath.ofproto_parser
        dpid = datapath.id
        if src.split(':')[0] == '02' and src.split(':')[1] == '00' and src not in self.nodes: #verification if is an wifi host
            self.nodes.append(src)
        if dpid < 10 : #add flow only on switches no on AP
            if len(self.nodes) > 2:
                #dst = self.nodes[random.randint(0, len(self.nodes)-1)]
                if self.val != 0 and self.ambu == src: #if messages from ambulancve
                    dst = self.val #so we take the next destination
                else :
                    dst = self.nodes[random.randint(0, len(self.nodes)-1)]
                self.check(src, dst, datapath, dpid, parser)

    
# Checking if the path already exist and create the flow
    def check(self, src, dst, datapath, dpid, parser): #check if the path already exist and create the flow
        """
        If the source and destination are in the network, find the shortest path between them, and if the
        current switch is in the path, find the next switch in the path and add a flow to the current switch
        to send the packet to the next switch.
        
        :param src: source host
        :param dst: destination host
        :param datapath: the datapath object that represents the switch
        :param dpid: the switch ID
        :param parser: the parser for the datapath
        """

        if str(src) in self.nodes:
            if src and dst in self.net:
                path = nx.shortest_path(self.net, src, dst)
                #print(path)
                if dpid in path :
                    next = path[path.index(dpid) + 1]
                    out_port = self.net[dpid][next]['port'] #get the next out port on the path
                    #we need to match ip and protocol
# The above code is adding a flow entry to the switch. The flow entry is for the ICMP packets that are
# destined to the broadcast address. The flow entry is added with a priority of 2222. The flow entry
# is added to the switch with the datapath as the parameter. The match field is set to the ICMP
# packets that are destined to the broadcast address. The action field is set to output the packet to
# the out_port.
                    match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,eth_src=src,ip_proto = in_proto.IPPROTO_ICMP, ipv4_dst='10.0.255.255')
                    actions = [parser.OFPActionOutput(out_port)] #,parser.OFPActionSetField(eth_src=src)]
                    self.add_flow(datapath=datapath, priority=2222, match=match, actions=actions)

    
    @set_ev_cls(event.EventLinkAdd, MAIN_DISPATCHER) #event when a link is created
    def get_topology_data(self, ev):
        """
        It updates the networkx graph with the latest topology data.
        
        :param ev: event object
        """
        print("********************************Lien Cree***********************************************")
        #we update our switches list and our link list.
        switch_list = get_switch(self.topology_api_app, None)
        switches = [switch.dp.id for switch in switch_list]
        self.net.add_nodes_from(switches)
        self.links_list = get_link(self.topology_api_app, None)
        # print links_list
        links = [(link.src.dpid, link.dst.dpid, {'port': link.src.port_no}) for link in self.links_list]
        # print links
        self.net.add_edges_from(links)
        links = [(link.dst.dpid, link.src.dpid, {'port': link.dst.port_no}) for link in self.links_list]
        # print links
        self.net.add_edges_from(links)
        #print("**********List of links")
        #print(self.net.edges())
        if self.tic != None :
            self.toc = time.perf_counter()
            print("Time : ", self.toc-self.tic)




    @set_ev_cls(event.EventLinkDelete, MAIN_DISPATCHER)
    def get_topology(self, ev):
        """
        It gets the list of switches and links from the topology discovery app, and then adds them to the
        graph.
        
        :param ev: event object
        """
        print("********************************Lien perdu***********************************************")
        print(ev)
        switch_list = get_switch(self.topology_api_app, None)
        switches = [switch.dp.id for switch in switch_list]
        self.net.add_nodes_from(switches)
        links_list = get_link(self.topology_api_app, None)
        # print links_list
        links = [(link.src.dpid, link.dst.dpid, {'port': link.src.port_no}) for link in links_list]
        # print links
        self.net.add_edges_from(links)
        links = [(link.dst.dpid, link.src.dpid, {'port': link.dst.port_no}) for link in links_list]
        # print links
        self.net.add_edges_from(links)
        print("**********List of links")
        print(self.net.edges())

        
    
    def newflow(self, datapath, parser): #function to erase and create new flows on all switches
        """
        It creates a new flow table for the switch, and adds two default flows to it. The first flow is a
        catch-all flow that sends all packets to the controller. The second flow is a flow that sends LLDP
        packets to the controller
        
        :param datapath: the switch object
        :param parser: the parser for the datapath
        """
        ofproto = datapath.ofproto
        self.remove_flows(datapath,0)
        self.net.clear()
        self.links_list.clear()

        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]    #default Action, send controller
        match = parser.OFPMatch()
        print(match)
        self.add_flow(datapath, 0, match, actions)
        #                                                                   Permet de reset les lien apres un del-flows

        match = parser.OFPMatch(eth_dst="01:80:c2:00:00:0e",eth_type=0x88cc) #default Action, send controller
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,)]
        self.add_flow(datapath, 65535, match, actions)
        #self.get_topology_data(None)

    def remove_flows(self, datapath, table_id): #remove all flow from an table id
        """
        > This function removes all the flow entries from a table
        
        :param datapath: the datapath object
        :param table_id: the table to remove flows from
        """
        self.tic = time.perf_counter()
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        empty_match = parser.OFPMatch()
        instructions = []
        flow_mod = self.remove_table_flows(datapath, table_id,
                                        empty_match, instructions)
        print("deleting all flow entries in table ", table_id)
        datapath.send_msg(flow_mod)
    

    def remove_table_flows(self, datapath, table_id, match, instructions):
        """
        It creates a flow_mod message that deletes all flows in the table that match the given match and
        instructions
        
        :param datapath: the datapath object
        :param table_id: The table to install the flow entry
        :param match: The match fields to match on
        :param instructions: The actions to be performed on the packet
        :return: The flow_mod is being returned.
        """
        ofproto = datapath.ofproto
        flow_mod = datapath.ofproto_parser.OFPFlowMod(datapath, 0, 0, table_id,
                                                      ofproto.OFPFC_DELETE, 0, 0,
                                                      1,
                                                      ofproto.OFPCML_NO_BUFFER,
                                                      ofproto.OFPP_ANY,
                                                      OFPG_ANY, 0,
                                                      match, instructions)
        return flow_mod


