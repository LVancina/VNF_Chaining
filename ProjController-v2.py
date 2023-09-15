from pox.core import core
from pox.lib.util import dpid_to_str
import pox.openflow.libopenflow_01 as of
from pox.lib.packet import *
# import VNF_Controller

log = core.getLogger()


class SwitchController (object):
    """
  A SwitchController object is created for each switch that connects.
  A Connection object for that switch is passed to the __init__ function.
  """
    def __init__ (self, connection):
        self.connection = connection

        # This binds our PacketIn event listener
        connection.addListeners(self)

        # Use this table to keep track of which ethernet address is on
        # which switch port (keys are MACs, values are ports).
        self.macTable = {}


    def resend_packet (self, packet_in, out_port):
        """
        Instructs the switch to resend a packet that it had sent to us.
        "packet_in" is the ofp_packet_in object the switch had sent to the
        controller due to a table-miss.
        """
        msg = of.ofp_packet_out()
        msg.data = packet_in

        # Add an action to send to the specified port
        action = of.ofp_action_output(port = out_port)
        msg.actions.append(action)

        # Send message to switch
        self.connection.send(msg)


    def handle_arp (self, packet, packet_in):
        """
        Implement switch-like behavior.
        """

        self.macTable[packet.src] = packet_in.in_port
        print(dpid_to_str(self.connection.dpid) + " Mac Table: " + str(self.macTable))

        # if the port associated with the destination MAC of the packet is known:
        if packet.dst in self.macTable.keys():
            # print("src/dst recognized")

            # print("Installing new flow for src: {}, dst: {}", packet.dst, packet.src)
            log.debug("Installing flow...")
          # Maybe the log statement should have source/destination/port?

            msg = of.ofp_flow_mod()

            # Set fields to match received packet
            msg.match = of.ofp_match.from_packet(packet_in)
            msg.idle_timeout = 350
            msg.priority = 1
            msg.actions.append(of.ofp_action_output(port=self.macTable[packet.dst]))
            print("sending msg, idle_timeout = " + str(msg.idle_timeout))
            self.connection.send(msg)

        else:
            # print("Broadcasting packet")
            # Flood the packet out everything but the input port
            # This part looks familiar, right?
            self.resend_packet(packet_in, of.OFPP_ALL)

    def direct_to_chain(self, packet, packet_in):
        '''Direct the flow throught the correct function chain.'''
        msg = of.ofp_flow_mod()
        src_ip = packet.payload.srcip
        if src_ip == "10.0.1.1":
            msg.actions.append(of.ofp_action_output(port=1))
        elif src_ip == "10.0.2.1":
            msg.actions.append(of.ofp_action_output(port=2))
        # elif src_ip == "10.0.3.1":
        #     # self.act_like_switch(packet, packet_in)
        #     msg.actions.append(of.ofp_action_output(port=4))
        #     return

        msg.match = of.ofp_match.from_packet(packet_in)
        msg.idle_timeout = 360
        msg.priority = 1
        # print("sending msg, idle_timeout = " + str(msg.idle_timeout))
        # print("***IP***Installing new flow for src: {}, dst: {}", packet.dst, packet.src)
        self.connection.send(msg)

    def chain_forward(self, packet, packet_in):
        '''Simply forward to the next link of the chain'''
        msg = of.ofp_flow_mod()
        msg.match = of.ofp_match.from_packet(packet_in)
        msg.idle_timeout = 360
        msg.priority = 1
        src_ip = packet.payload.srcip
        # if src_ip == '10.0.3.1':
        #     # print("Forwarding source IP: " + str(src_ip))
        #     # print("***Received return packet from: " + str(src_ip))
        #     msg.actions.append(of.ofp_action_output(port=4))
        # else:
        #     msg.actions.append(of.ofp_action_output(port=1))
        msg.actions.append(of.ofp_action_output(port=1))
        # print("sending msg, idle_timeout = " + str(msg.idle_timeout))
        print("Doing action " + str(msg.actions))
        # print("***IP***Installing new flow for src: {}, dst: {}", packet.dst, packet.src)
        self.connection.send(msg)

    def returnTraffic(self, packet, packet_in):
        '''Only allow traffic to return to the outside world'''

        # self.macTable[packet.src] = packet_in.in_port
        msg = of.ofp_flow_mod()
        msg.actions.append(of.ofp_action_output(port=4))
        msg.match = of.ofp_match.from_packet(packet_in)
        msg.idle_timeout = 350
        msg.priority = 1
        self.connection.send(msg)

    def dropPacket(self, packet_in):
        msg = of.ofp_flow_mod()
        msg.actions.append(of.ofp_action_output(port=of.OFPP_NONE))
        msg.match = of.ofp_match.from_packet(packet_in)
        msg.idle_timeout = 350
        msg.priority = 1
        self.connection.send(msg)

    def _handle_PacketIn (self, event):
        """
        Handles packet in messages from the switch.
        """

        packet = event.parsed # This is the parsed packet data.
        if not packet.parsed:
            log.warning("Ignoring incomplete packet")
            return

        packet_in = event.ofp # The actual ofp_packet_in message.
        # self.macTable[packet.src] = packet_in.in_port
        dpid = event.connection.dpid
        print("***Packet received from: " + dpid_to_str(dpid))
        print("Packet = " + str(packet))

        # Switch name
        swName = dpid_to_str(dpid).split('-')[-1]

        # if packet.find('ipv4') or packet.find('udp'):
        if isinstance(packet.next, ipv4):

            # determine whether if the source of the event was s1.
            # if so, then choose a chain.
            if swName == '01':
                print("Direct to chain!")
                self.direct_to_chain(packet, packet_in)
            # elif swName == '05':
            #     print("Return traffic")
            #     self.returnTraffic(packet, packet_in)
            else:
                self.chain_forward(packet, packet_in)
                print("Chain forward!")
        else:
            self.handle_arp(packet, packet_in)
            if swName == '01' or swName == '05':
                print("handle ARP")
                self.handle_arp(packet, packet_in)
            else:
                self.dropPacket(packet_in)


def launch ():
    """
  Starts the component
  """
    def start_switch (event):
        # event.connection.listen(port=6653)
        log.debug("Controlling %s" % (event.connection,))
        # print(str(event.ofp))
        print("Connection dpid: " + str(event.connection.dpid))
        SwitchController(event.connection)

    core.openflow.addListenerByName("ConnectionUp", start_switch)
