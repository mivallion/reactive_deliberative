import datetime

from examples.moex_iss_dumper.moex_iss_dumper import MoexIssDumper
from py_rete import Production, V, Fact
from reactive_deliberative.reactive_deliberative import ReactiveDeliberative


@Production(V('fact') << Fact(state="not loaded"), priority=2, timeout=1)
async def dump(net, fact):
    fact['state'] = 'loading'
    print(dumper.current_date_str, 'started')
    net.update_fact(fact)
    await dumper.dump()
    print(dumper.current_date_str, 'finish')
    fact['state'] = 'not loaded'
    net.update_fact(fact)


@Production(V('fact') << Fact(state="not loaded"), priority=2, timeout=1)
async def dump(net, fact):
    fact['state'] = 'loading'
    print(dumper.current_date_str, 'started')
    net.update_fact(fact)
    await dumper.dump()
    print(dumper.current_date_str, 'finish')
    fact['state'] = 'not loaded'
    net.update_fact(fact)


if __name__ == '__main__':
    url = 'https://iss.moex.com/iss/history/engines/currency/markets/selt/trades.json'
    db_filepath = r'C:\Users\vikto\Documents\source\repos\reactive_deliberative\db.db'
    start_date = datetime.datetime(2002, 1, 10)
    end_date = datetime.datetime(2002, 1, 10)
    dump_dir = "./iss_dump/"
    dumper = MoexIssDumper(url, start_date, end_date, dump_dir, db_filepath)

    # asyncio.run(dumper.dump())
    rd = ReactiveDeliberative()
    # rd.add_fact("green", "light_color")
    rd.add_fact("not loaded", "state")
    rd.add_production(dump)
    # rd.add_production(make_green)
    # rd.add_production(make_red_high_priority)
    # rd.add_reactive_action(keyboard_predicate, keyboard_reactive)
    rd.run()
