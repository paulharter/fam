
import requests

def clear_db():

    url = "http://localhost:8080/emulator/v1/projects/localtest/databases/(default)/documents"
    rsp = requests.delete(url)
    if rsp.status_code != 200:
        raise Exception("failed to clear test db")

