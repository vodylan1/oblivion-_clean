import asyncio, os, sqlite3, time, pytest
from oblivion.price_consumer.price_consumer import price_feed
from oblivion.core.models import PriceSample

@pytest.mark.asyncio
async def test_yields_recent_sample(tmp_path):
    db = tmp_path/"price_queue.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE queue(ts INTEGER, price REAL);")
    conn.execute("INSERT INTO queue VALUES(?,?)", (time.time_ns(), 123.45))
    conn.commit(); conn.close()
    os.environ["OBLIVION_PRICE_DB"] = str(db)
    gen = price_feed()
    sample = await asyncio.wait_for(gen.__anext__(), 0.2)
    assert isinstance(sample, PriceSample) and sample.price == 123.45

# ...five more stub tests for edge cases...
