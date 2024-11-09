import math

def pad(string, max_width):
    padding_width = max(0, max_width - len(string))
    if padding_width == 0:
        return string
    else:
        lpadd = int(math.floor(padding_width / 2.0))
        rpadd = int(math.ceil(padding_width / 2.0))
        return (" " * lpadd) + string + (" " * rpadd)


class TernaryMatch:
    def __init__(self, value, mask, length):
        self.value = value
        self.mask = mask
        self.value_s = format(value, "0" + str(length) + "b")
        self.mask_s = format(value, "0" + str(length) + "b")

    def matches(self, value):
        return self.value & self.mask == value & self.mask

    def __str__(self):
        ternary = ""
        for vbit, mbit in zip(self.value_s, self.mask_s):
            if mbit == "0":
                ternary += "*"
            else:
                ternary += vbit
        return ternary

class ExactMatch:
    def __init__(self, value):
        self.value = value
    
    def matches(self, value):
        return self.value == value
    
    def __str__(self):
        return str(self.value)
    
    def __repr__(self):
        return str(self)

class Entry:
    def __init__(self, matches, action, args, priority):
        self.matches = matches
        self.action = action
        self.args = args
        self.priority = priority

    def __str__(self):
        return str(self.priority) + " : " + str(self.matches) + " ==> " + self.action + "(" + ",".join(str(a) for a in self.args) + ")"
    
    def __repr__(self):
        return str(self)

class Table:
    def __init__(self, packet, keys, actions, default_action):
        self.packet = packet
        self.keys = keys
        self.actions = actions
        self.entries = []
        self.default_action = default_action

    def apply(self):
        values = [self.packet[k] for k in self.keys]
        matching_entries = [
            entry
            for entry in self.entries
            if all( m.matches(values[i])
                    for m,i in enumerate(entry.matches))
        ]
        if matching_entries:
            entry = max(matching_entries, key = lambda entry: entry.priority)
            return self.actions[entry.action](*entry.args)
        else:
            return self.actions[self.default_action]()
    
    def normalize(self):
        self.entries.sort(key = lambda e: e.priority)

    def add(self, entry):
        self.entries.append(entry)
        self.normalize()

    def __str__(self):
        self.normalize()
        keys_str = " ".join(self.keys)
        prio_width = 0
        key_width = len(keys_str)
        str_entries = []
        for e in self.entries:
            prio = str(e.priority)
            prio_width = max(prio_width, len(prio))
            key = ",".join(str(m) for m in e.matches)
            key_width = max(key_width, len(key))
            str_entries.append([
                prio, key, e.action + "("+ ",".join(str(a) for a in e.args) + ")"
            ])
        str_entries = [
            pad(p, prio_width) + " : " +
            pad(k, key_width) + " ==> " +
            act
            for [p,k,act] in str_entries
        ]
        header = (" " * (prio_width + 3)) \
            + pad(keys_str, key_width) \
            + "  |  " + " ".join(self.actions.keys())
        return header + "\n" \
            + "---------------------\n" \
            + "\n".join(str_entries) + "\n" \
            + (" " * (prio_width + 3)) \
            + pad("*", key_width) + " ==> " + self.default_action + "()"
        
    def __repr__(self):
        return str(self)