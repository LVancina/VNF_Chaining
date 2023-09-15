#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info


def myNetwork():

    net = Mininet(switch=OVSSwitch)

    info('*** Adding controller\n')
    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6633)

    info('*** Add switches\n')
    s1 = net.addSwitch('s1', cls=OVSSwitch, stp=True)
    s2 = net.addSwitch('s2', cls=OVSSwitch, stp=True)
    s3 = net.addSwitch('s3', cls=OVSSwitch, stp=True)
    s4 = net.addSwitch('s4', cls=OVSSwitch, stp=True)
    # s5 = net.addSwitch('s5', cls=OVSSwitch, stp=True)

    info('*** Add hosts\n')
    h1 = net.addHost('h1', ip='10.0.1.1')
    h2 = net.addHost('h2', ip='10.0.2.1')
    h3 = net.addHost('h3', ip='10.0.3.1')

    info('*** Add links\n')
    # net.addLink(s5, s3, port2=1)
    # net.addLink(s5, s4, port2=1)
    net.addLink(s4, h3, port1=1)
    net.addLink(s3, h3, port1=1)
    net.addLink(s2, s3, port1=1)
    net.addLink(s1, s2, port1=1)
    net.addLink(s1, s4, port1=2)
    # net.addLink(s5, s1, port1=4)
    # net.addLink(h3, s5, port1=1)
    net.addLink(h1, s1)
    net.addLink(h2, s1)

    info('*** Starting controllers\n')
    s2.start([c0])

    info('*** Starting network\n')
    net.start()

    s1.cmd('ovs-vsctl set bridge s1 stp_enable=true')
    s2.cmd('ovs-vsctl set bridge s2 stp_enable=true')
    s3.cmd('ovs-vsctl set bridge s3 stp_enable=true')
    s4.cmd('ovs-vsctl set bridge s4 stp_enable=true')
    # s5.cmd('ovs-vsctl set bridge s5 stp_enable=true')

    info('*** Post configure switches and hosts\n')

    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    myNetwork()
