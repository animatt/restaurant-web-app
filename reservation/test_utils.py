from django.db import IntegrityError

class ConcurrencyError(IntegrityError):
    pass

def TEST_SIM_RACE_CONDITION():
    '''
    For use with `mock.patch` to simulate a race condition.
    '''
    pass
