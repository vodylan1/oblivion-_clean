from mutation_engine.models import Gene, Genome
from mutation_engine.genetics import crossover, score

def test_simple_crossover():
    a = Genome([Gene("x",1),Gene("y",2)])
    b = Genome([Gene("x",3),Gene("y",4)])
    child = crossover(a,b)
    assert len(child.genes)==2 and child.genes[0].value==1 and child.genes[1].value==4

def test_dummy_score():
    g = Genome([Gene("a",5),Gene("b",5)])
    s = score(g)
    assert s.sharpe==1.0 and s.pnl==10

# async scorer monkey‑patch
import asyncio, httpx, types
import pipelines.route_scorer as rs

async def fake_call(*_,**__):
    return {"routes":[{"outAmountUsd": "123.45"}]}
def test_route_score(monkeypatch):
    m = types.SimpleNamespace(json=lambda: {"routes":[{"outAmountUsd":"200"}]})
    async def fake_get(*a,**k): return m
    monkeypatch.setattr(httpx.AsyncClient,"get",fake_get)
    v = asyncio.run(rs.impact_score(100))
    assert v==2.0
