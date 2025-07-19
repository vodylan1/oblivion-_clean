import asyncio, pytest, sqlite3, time, os
from oblivion.price_consumer.router import robust_price_feed
from oblivion.core.models import PriceSample

@pytest.mark.asyncio
async def test_fallback_to_birdeye(monkeypatch, tmp_path):
    # empty local DB so it must use API
    db = tmp_path/"q.db"
    sqlite3.connect(db).execute("CREATE TABLE queue(ts INTEGER, price REAL);")
    os.environ["OBLIVION_PRICE_DB"] = str(db)

    async def fake_api():
        return PriceSample(timestamp_ns=time.time_ns(), price=99.99)
    monkeypatch.setattr("oblivion.price_consumer.birdeye_client.fetch_price", fake_api)

    gen = robust_price_feed()
    price = await asyncio.wait_for(gen.__anext__(), 0.2)
    assert price.price == 99.99
