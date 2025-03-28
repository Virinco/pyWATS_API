from enum import Enum


class ContextType(Enum):
    Defaults = "Defaults"
    LegacyData = "LegacyData"

class DeserializationContext:
    def __init__(self, type: ContextType, defaults: dict):
        self.type = type
        self.defaults = defaults