from table import *

packet = {
    "egress_port" : 0,
    "eth.src" : 47,
    "eth.dst" : 99,
    "ipv4.ttl" : 255,
    "ipv4.dst" : 8888 
}


def set_port (p):
    packet["egress_port"] = p

def rewrite(dst):
    packet["eth.src"] = dst
    packet["eth.dst"] = packet["eth.src"]
    packet["ipv4.ttl"] = packet["ipv4.ttl"] - 1


def drop ():
    packet["egress_port"] = 511
    
ipv4_set_port = Table([32], [set_port, drop], drop)
ipv4_rewrites = Table([32], [rewrite, drop], drop)

def pipeline(pkt):
    packet = pkt
    ipv4_set_port.apply(packet["ipv4.dst"])
    ipv4_rewrites.apply(packet["ipv4.dst"])

