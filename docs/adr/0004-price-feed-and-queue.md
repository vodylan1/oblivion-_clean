# ADR-004 – Price-Feed & Event Queue

| Status | Context Date |
|--------|--------------|
| *Proposed* | 2025-03-‹today› |

## Context  
Alpha-Mesh now emits mint events (Phase-6).  Strategies also need **real-time SOL/USD**  
to size positions and compute PnL.  We’ll ingest Helius price ticks and push them,  
together with MintEvents, into a LiteDB queue (file-based, CI-friendly).

## Decision  
1. `pipelines.price_feed.sol_usd()` — single authoritative helper.  
2. Background task writes `{slot, mint, price}` tuples into `data/mesh.db`.  
3. Strategies subscribe via the existing SynergyConductor bus (Phase-8 hook).  

## Consequences  
* CI unaffected (fixed price = 125 $).  
* LiteDB keeps local state; prod can swap to Kafka later.  

