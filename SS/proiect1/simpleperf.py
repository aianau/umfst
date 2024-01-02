#!/usr/bin/env python

# This script is intented to be placed in /home/mininet/mininet/examples/simpleperf.py
# and ran: `sudo ./mininet/examples/simpleperf.py`

"""
Simple example of setting network and CPU parameters

NOTE: link params limit BW, add latency, and loss.
There is a high chance that pings WILL fail and that
iperf will hang indefinitely if the TCP handshake fails
to complete.
"""

from sys import argv
import time

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel, info
from mininet.cli import CLI

# It would be nice if we didn't have to do this:
# pylint: disable=arguments-differ

def my_print(*args, **kwargs):
    print('[+] ', *args, **kwargs)

class SingleSwitchTopo( Topo ):
    "Single switch connected to n hosts."
    def build( self, n=2, lossy=True ):
        switch = self.addSwitch('s1')
        for h in range(n):
            # Each host gets 50%/n of system CPU
            host = self.addHost('h%s' % (h + 1),
                                cpu=.5 / n)
            if lossy:
                # 10 Mbps, 5ms delay, 10% packet loss
                self.addLink(host, switch,
                             bw=10, delay='5ms', loss=10, use_htb=True)
            else:
                # 10 Mbps, 5ms delay, no packet loss
                self.addLink(host, switch,
                             bw=10, delay='5ms', loss=0, use_htb=True)

def perfTest( lossy=True ):
    "Create network and run simple performance test"
    topo = SingleSwitchTopo( n=4, lossy=lossy )
    net = Mininet( topo=topo,
                   host=CPULimitedHost, link=TCLink,
                   autoStaticArp=True )
    net.start()
    info( "Dumping host connections\n" )
    dumpNodeConnections(net.hosts)
    info( "Testing bandwidth between h1 and h4\n" )
    h1, h2, h3 = net.getNodeByName('h1', 'h2', 'h3')

    # Prepare attack traffic
    my_print('***')
    my_print("doing attack")
    h3.cmd('tcpdump -i h3-eth0 "icmp[0]==8" -w attackf.pcap &')
    h3.cmd("ping 10.0.0.1 &")
    seconds = 10
    my_print(f"Waiting {seconds}s to have some attack traffic")
    time.sleep(seconds)
    my_print ("done.. stopping attack")
    h3.cmd("killall ping")
    h3.cmd("killall tcpdump")
    my_print("stopped attack")
    my_print('***')
    
    # # Regular experiment
    # my_print('starting regular experiment')
    # tag = 'regular-exp'
    # h1.cmd("iperf -s &")
    # h1.cmd(f"tcpdump -i h1-eth0 -w h1-{tag}.pcap &")
    # h2.cmd("iperf -c 10.0.0.1 -t 100 &")
    
    # my_print ("sleeping.. please wait")
    # time.sleep(20)
    # my_print ("done sleeping, killing...")
    # h1.cmd("killall iperf")
    # h2.cmd("killall iperf")
    # h1.cmd ("killall tcpdump")
    # my_print("finished regular experiment")
    # my_print('***')
    
    seconds = 5
    my_print(f"Waiting {seconds}s between experiments.")
    my_print('***')
    time.sleep(seconds)


    # Attack experiment
    my_print("Starting Attack experiment")
    tag = 'attack-exp'
    h1.cmd(f"tcpdump -i h1-eth0 -w h1-{tag}.pcap &")
    h2.cmd(f"tcpdump -i h2-eth0 -w h2-{tag}.pcap &")
    h3.cmd(f"tcpdump -i h3-eth0 -w h3-{tag}.pcap &")
    my_print("setupped tcpdumps")

    h1.cmd("iperf -s &")
    h2.cmd("iperf -c 10.0.0.1 -t 100 &")
    seconds = 60
    my_print(f'setuped regular traffic. running for {seconds} seconds')
    time.sleep(seconds)
    seconds = 20
    my_print(f'replaying the attack with tcpreplay. Run for {seconds} seconds')
    h1.cmd('tcpreplay -i h1-eth0 -t -l 10000 attackf.pcap &')
    time.sleep(seconds)

    my_print(f'killing the attack traffic.')
    h3.cmd('killall tcpreplay')
    seconds = 20
    my_print(f'waiting for another {seconds} seconds')
    time.sleep(seconds)

    my_print("done sleeping, killing all remaining processes")
    h1.cmd("killall iperf")
    h2.cmd("killall iperf")
    h1.cmd("killall tcpdump")
    h2.cmd("killall tcpdump")
    h3.cmd("killall tcpdump")

    my_print('finished')
    my_print('***')


    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel( 'info' )
    # Prevent test_simpleperf from failing due to packet loss
    perfTest( lossy=( 'testmode' not in argv ) )
