from .blud import StringField

class EmailField(StringField):
    pattern = """/^(([a-zA-Z]|[0-9])|([-]|[_]|[.]))+[@](([a-zA-Z0-9])|([-])){2,63}[.](([a-zA-Z0-9]){2,63})+$/gi"""

class DateTimeField(StringField):
    pattern = """^([0-9]{4})-((0[1-9])|(1[0-2]))-(([0-2][0-9])|(3[0-1]))T(([0-1][0-9])|(2[0-3])):([0-5][0-9]):([0-5][0-9])(.[0-9]{1,4}|)(Z|(\+|\-)([0-5][0-9]):([0-5][0-9]))$"""