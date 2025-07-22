from prometheus_client import Gauge, start_http_server
QUEUE_LAG = Gauge("price_queue_lag_ms", "Lag of local price queue")
PRICE = Gauge("price_usd", "Current SOL/USD price")

def expose(port=9102):
    start_http_server(port)
