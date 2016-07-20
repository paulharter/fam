class FamDbConnectionException(Exception):
    pass

class FamResourceConflict(Exception):
    pass

class FamValidationError(Exception):
    pass

class FamImmutableError(Exception):
    pass

class FamUniqueError(Exception):
    pass

class FamError(Exception):
    pass