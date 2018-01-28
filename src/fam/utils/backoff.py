import requests
import time

from fam.exceptions import FamResourceConflict

def http_backoff(func):

    def func_wrapper(*args, **kwargs):

        if kwargs.get("backoff"):
            connected = False
            counter = 0

            # retry with a backoff
            while not connected:
                try:
                    return func(*args, **kwargs)
                except (requests.exceptions.ConnectionError, FamResourceConflict) as e:
                    counter += 1
                    if counter < 8:
                        nap = 2 ** counter
                        msg = """Failed to connect!.
                         Has failed {} times.
                         Will try again after {} seconds backoff
                         Origional Error: {}""".format(counter, nap, e)
                        print(msg)
                        time.sleep(nap)
                    else:
                        raise e
        else:
            # print args
            return func(*args, **kwargs)

    return func_wrapper
