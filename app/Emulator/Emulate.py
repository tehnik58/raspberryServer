class EmulatedGPIO:
    def __init__(self):
        self.pins = {i: {"mode": None, "value": 0} for i in range(40)}
    
    def setup(self, pin, mode):
        self.pins[pin]["mode"] = mode
    
    def output(self, pin, value):
        self.pins[pin]["value"] = value