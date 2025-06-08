# architecture_overview.md

Placeholder for detailed architecture overview (will be expanded).

Add a short “Derivatives Layer” bullet: “Plugs into Mango/Drift; supports SHORT & CLOSE_SHORT; margin monitored by Kill-Switch.”

#### Derivatives Layer (NEW – Phase 7)
> Interfaces with Solana margin/perps protocols (Mango Markets first).  
> Exposes  
> `open_short(symbol, size)` / `close_short(symbol)` / future `adjust_margin()`.  
> Risk limits forwarded to **Kill-Switch**; PnL recorded by **ReflectionEngine**.
