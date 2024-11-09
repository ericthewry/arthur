from table import *

packet = {"ipv4.dst" : 8888,
          "eth.dst" : 47
          }

e1 = Entry([ExactMatch(8888)], "fwd", (88, 77), 0)
e2 = Entry([ExactMatch(9999)], "fwd", (99, 1), 104)

def set_port (p):
    packet["egress_port"] = p

def rewrite(dst):
    packet["eth.dst"] = packet["eth.src"]
    packet["eth.src"] = dst
    packet["ipv4.ttl"] = packet["ipv4.ttl"] - 1

def fwd(p,dst):
    set_port(p)
    rewrite(dst)

def drop ():
    packet["egress_port"] = 511
    
ipv4_fwd = Table(packet, ["ipv4.dst"], {"fwd" : fwd, "drop": drop}, "drop")

def pipeline(pkt):
    global packet
    packet = pkt
    ipv4_fwd.apply()
    if packet["egress_port"] == 511:
        print ("packet dropped")
        return None
    else:
        return packet

