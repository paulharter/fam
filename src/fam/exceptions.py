class FamDbConnectionException(Exception):
    pass

class FamResourceConflict(Exception):
    pass

class FamViewError(Exception):
    pass

class FamValidationError(Exception):
    pass

class FamImmutableError(Exception):
    pass

class FamUniqueError(Exception):
    pass

class FamWriteError(Exception):
    pass

class FamError(Exception):
    pass

class FamPermissionError(Exception):
    pass

class FamTransactionError(Exception):
    pass