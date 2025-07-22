from collections import deque
def median_of_3(series):
    q = deque(maxlen=3)
    while True:
        price = yield
        q.append(price)
        if len(q) == 3:
            yield sorted(q)[1]

def ema(alpha=0.2):
    value = None
    while True:
        price = yield
        value = price if value is None else (alpha*price + (1-alpha)*value)
        yield value
