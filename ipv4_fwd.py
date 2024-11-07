from table import *

packet = {}

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
    
ipv4_fwd = Table([32], [fwd, drop], drop)

def pipeline(pkt):
    global packet
    packet = pkt
    ipv4_fwd.apply(packet["ipv4.dst"])
    if packet["egress_port"] == 511:
        print ("packet dropped")
        return None
    else:
        return packet

