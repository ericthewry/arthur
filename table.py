class TernaryMatch:
    def __init__(self, value, mask):
        self.value = value
        self.mask = mask

    def matches(self, value):
        return self.value & self.mask == value & self.mask

class ExactMatch:
    def __init__(self, value):
        self.value = value
    
    def matches(self, value):
        return self.value == value

class Entry:
    def __init__(self, match, action, args, priority):
        self.match = match
        self.action = action
        self.args = args
        self.priority = priority

class Table:
    def __init__(self, key_types, actions, default_action):
        self.key_types = key_types
        self.actions = actions
        self.entries = []
        self.default_action = default_action

    def apply(self, value):
        matching_entries = [
            entry
            for entry in self.entries
            if entry.match.matches(value)
        ]
        if matching_entries:
            entry = max(matching_entries, key = lambda entry: entry.priority)
            return entry.action(*entry.args)
        else:
            return self.default_action()
    
    def add(self, entry):
        self.entries.append(entry)