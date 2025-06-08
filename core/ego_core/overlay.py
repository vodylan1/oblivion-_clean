class EmotionOverlay:
    """
    Simple rage / fear overlay driven by consecutive PnL.
    • rage: +20 % confidence boost after 3 wins in a row
    • fear: –50 % confidence after 2 losses in a row
    """

    def __init__(self):
        self.win_streak = 0
        self.loss_streak = 0

    def update(self, pnl: float):
        if pnl > 0:
            self.win_streak += 1
            self.loss_streak = 0
        elif pnl < 0:
            self.loss_streak += 1
            self.win_streak = 0

    def apply(self, confidence: float) -> float:
        if self.win_streak >= 3:          # rage
            return min(confidence * 1.2, 1.0)
        if self.loss_streak >= 2:         # fear
            return confidence * 0.5
        return confidence
