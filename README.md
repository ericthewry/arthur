# A Tutorial on Networking Tables

The goal here is to give an interactive tutorial on how tables work.
I've implemented a simple "table" data structure in python that
behaves loosely like a P4 table. By the end of this tutorial, 
we will write simple programs that manipulate packet state and trigger
table lookups.

## Match-Action Tables

Let's start with the core data plane programming construct, a `Table`. We can construct a table as follows:
```python
t = Table(keys, actions, default_action)
```
where: 
- `keys` is a list of strings defining the "keys" to the table,
- `actions` is a list of functions that correspond to the possible actions that can be triggered
- `default_action` is a 0-argument function that corresponds to the "else" case.

Before we write down an example, I'll say something about the basic programming model that we'll use.

The goal here is to model basic networking programs: this means packet-processing functions. 
To do this, we need a way to model "Packets" and transformations thereupon.

For our purposes, a _packet_ is a simply a map (that is a `dict`) from variables ("strings") to values (`ints`). For instance, here's a packet with IPv4 destination address `8888` and IPv4 source address `1111`:
```python
packet = {
    "ipv4.dst": 8888,
    "ipv4.src": 1111
}
```

Our toy data plane programs will initialize a global variable `packet` and transform its fields as appropriate.

For instance, we can define a simple function `set_port` that sets the forwarding port (called `egress_port`) that performs IPv4 forwarding on a packet:
```python
def set_port(p):
    packet["egress_port"] = p
```
We can also define a function `rewrite` that performs the standard "routing" logic: the Ethernet source is rewritten to the destination, the Ethernet destination is written to some new value `d`, and the IPv4 headers Time To Live field is decremented by 1.
```python
def rewrite(d):
    packet["eth.src"] = packet["eth.dst"]
    packet["eth.dst"] = d
    packet["ipv4.ttl"] = packet["ipv4.ttl"] - 1
```

Okay, now let's dive into tables. 

The following table performs basic IPv4/Ethernet forwarding:
```python
ipv4_fwd = Table(["ipv4.dst"], [fwd, drop], drop)
```
where `fwd` is defined as follows:
```python
def fwd(p, d):
    setport(p)
    rewrite(d)
```
and `drop` is defined:
```python
def drop():
    setport(511)
```
where `511` is a "virtual" port value that indicates the packet should be dropped, i.e. not forwarded.

## Pipeline Program

We can now write a simple, single-table pipeline.

```python
def pipeline(pkt):
    # "read" the packet
    # i.e. copy it into global 
    global packet
    packet = pkt 
    # execute the table
    ipv4_fwd.apply()
    # if the virtual drop port 511 has been indicated
    if packet["egress_port"] == 511:
        ## drop the packet
        print ("packet dropped")
        return None
    else:
        ## otherwise, return (forward) the packet
        return packet
```
Great! Now we have a pipeline program! Let's invoke our program on the command line, as below, and create a very simple packet with just an ipv4 destination address.

```python
python -i ipv4_fwd.py
>>> pkt = {
    "eth.dst" : 80808,
    "eth.src" : 10101,
    "ipv4.dst" : 8888, 
    "ipv4.ttl" : 255
}
```
Now, we can invoke the pipeline on this packet
```python
>>> pipeline(pkt)
packet dropped
```
And the packet has been dropped!!! In fact, every packet that we pass through this program will exectue `drop`. This is because we haven't configured the table with any forwarding rules, so at the moment, the `ipv4_fwd` table will _always_ run the `drop` action.

Let's change this.

## The Control Plane

To quote the 2018 SIGCOMM paper `p4v`, a pipeline is "only half a program". In fact, much of the program is dynamically produced  by the control plane.

At runtime, that is while the switches are actively processing networking traffic, the so-called _control plane_ dynamically changes the entries in the table to modify the system.

In this tutorial, you will simulate the control plane by configuring the `ipv4_fwd` table and observing differences in the packet forwarding behavior.

The basic unit of a table configuration is an `Entry`. Loosely, a configuration is a list of such entries. Here's how we create an `Entry`:
```python
e = Entry(match, action, args, priority)
```
where
- `match` specifies a set of values
- on which the function `action` should be run
- with the arguments `args`

The entry's `priority` is used to disambiguate between when a value is contained in multiple `match` sets.

Let's start with singleton sets, which we'll call `ExactMatch`es. We'll construct an exact match from a simple integer value `i`. Its `matches(j)` method will be true iff `i` and `j` are equal. That is: 
```python
>>> m = ExactMatch(8888)
>>> m.matches(8888)
True
>>> m.matches(12)
False
```

Now, we can use the actions from the table `ipv4_fwd` to create an entry for that table:
```
e = Entry(ExactMatch(8888), fwd, (8, 47), 0)
```
This entry triggers `fwd(8,47)` whenever the input value to the table (in the case of `ipv4_fwd`, its the value of `packet["ipv4.dst"]`). We can ignore the priority field. 

> *__Aside__. While this tutorial does not make this restriction, in a real switch, only the actions declared in the table can be used in the table itself*

Now we can, playing the role of the control plane, add this entry into the `ipv4_fwd` Table.

```python
>>> ipv4_fwd.add(m)
```

Now, let's return to the data plane pipeline and see what happens when the exact same packet is run through the pipeline with the updated configuration:
```python
>>> pipeline({"ipv4.dst" : 8888, "ipv4.ttl" : 255, "eth.dst" : 80808, "eth.src": 10101})
{'ipv4.dst': 8888, 'ipv4.ttl': 254, 'eth.dst': 10101, 'eth.src': 47, 'egress_port': 88}
```
Notice, now that the `egress_port` is `88`, which is the forwarding port that we specified in the match-action entry `m`.

Of course, if we run a packet that has some other `ipv4.dst`, i.e. that's not equal to `8888`, we'll see that `pipeline` drop that packet:
```python
>>> pipeline({
    "ipv4.dst" : 00000, ### Different address!!!
    "ipv4.ttl" : 255, 
    "eth.dst" : 80808, 
    "eth.src": 10101})
packet dropped
```
We have not added any rule into `ipv4_fwd` table to deal with packets with `ipv4.dst` equal to `00000`. As a result, the default action is triggered, which causes the packet to be dropped.

## Multiple Rules & Inexact Matches

>>>>> TODO