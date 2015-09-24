from .blud import StringField

class EmailField(StringField):
    pattern = """^([-!#$%&'*+/=?^_`{}|~0-9a-zA-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9a-zA-Z]+)*|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*")@(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}\.?$"""

class DateTimeField(StringField):
    pattern = """^([0-9]{4})-((0[1-9])|(1[0-2]))-(([0-2][0-9])|(3[0-1]))T(([0-1][0-9])|(2[0-3])):([0-5][0-9]):([0-5][0-9])(.[0-9]{1,4}|)(Z|(\+|\-)([0-5][0-9]):([0-5][0-9]))$"""