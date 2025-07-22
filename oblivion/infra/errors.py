import os, sentry_sdk
def init_errors():
    dsn = os.getenv("SENTRY_DSN")
    if dsn:
        sentry_sdk.init(dsn, traces_sample_rate=0.2)
