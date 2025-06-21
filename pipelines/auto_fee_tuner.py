from pipelines.tip_auto_tuner import tip_auto_tuner

def get_priority_fee() -> int:
    return tip_auto_tuner.get_tip_lamports()
