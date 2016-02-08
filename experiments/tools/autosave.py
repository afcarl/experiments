import time

last_save = time.time()

def autosave(period=300):
    global last_save
    if time.time() > period + last_save:
        last_save = time.time()
        return True
    return False
