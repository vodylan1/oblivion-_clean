    async def tick(self, market_tick: dict | None = None) -> TradeSignal | None:
        market_tick = market_tick or {}

        # ---- Pass A : high‑priority Trump‑Card strategies ----
        for name in STRATEGY_PRIORITY:
            strat = self._strategies[name]
            try:
                sig: Optional[TradeSignal] = await strat.decide(market_tick)
            except Exception as exc:
                print(f"[conductor] {name} error:", exc)
                sig = None

            if sig and self._risk_mgr.accept(sig):
                return sig

        # ---- Pass B : legacy agents ----
        signals: List[TradeSignal] = []
        for ag in self._agents:
            # skip agents that don’t implement tick()
            if not hasattr(ag, "tick"):
                continue
            try:
                s = await ag.tick(market_tick)
            except Exception as exc:
                print(f"[conductor] agent error:", exc)
                continue
            if s:
                # ensure every TradeSignal has .agent for weighting
                if not hasattr(s, "agent"):
                    s.agent = ag
                signals.append(s)

        if not signals:
            # emit neutral HOLD so downstream loggers have a signal object
            return TradeSignal(action="HOLD", confidence=0.0, meta={})

        # periodic weight decay + random reward
        self._tick_cnt += 1
        if self._tick_cnt % 20 == 0:
            for ag in self._weights:
                self._weights[ag] *= self._decay
            winner = random.choice(signals).agent
            self._weights[winner] += 0.1

        return max(
            signals,
            key=lambda s: s.confidence * self._weights.get(getattr(s, "agent", None), 1.0),
        )
