import enum

class EventReason(enum.Enum):
    AFK = "afk"
    TRANSFERRED = "transferred"
    LEFT = "left"
    DISBANDED = "disbanded"