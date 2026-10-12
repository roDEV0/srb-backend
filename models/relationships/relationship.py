import enum

class PlayerRelationship(enum.Enum):
    CITIZEN = "citizen"
    MAYOR = "mayor"
    KING = "king"
    OUTLAWED = "outlawed"
    TRUSTED = "trusted"
    NOMAD = "nomad"