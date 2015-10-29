import time

period = 300
last_save = time.time()

def autosave():
    global last_save
    if time.time() > period + last_save:
        last_save = time.time()
        return True
    return False
