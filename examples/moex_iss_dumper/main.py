import asyncio
import datetime

from examples.moex_iss_dumper.moex_iss_dumper import MoexIssDumper
from py_rete import Production, V, Fact
from reactive_deliberative.reactive_deliberative import ReactiveDeliberative


async def external_upload_predicate():
    return await dumper.external_upload_predicate()


async def external_upload_action():
    return await dumper.external_upload_action()


@Production(V('fact') << Fact(state="not loaded"), priority=2, timeout=1)
async def start_load(net, fact):
    if dumper.current_date > dumper.end_date:
        fact['state'] = 'finished'
        net.update_fact(fact)
        print(f'finish at date {dumper.end_date}')
        return
    await asyncio.sleep(0)
    dumper.clear_buffer()
    fact['state'] = 'get_from_url'
    net.update_fact(fact)


@Production(V('fact') << Fact(state="get_from_url"), priority=2, timeout=1)
async def get_from_url(net, fact):
    await dumper.get_from_url()
    if len(dumper.current_dataframe) > 0:
        fact['state'] = 'write_to_csv'
    else:
        dumper.current_date += datetime.timedelta(days=1)
        print(f'date {dumper.current_date} skipped')
        fact['state'] = 'not loaded'
    net.update_fact(fact)


@Production(V('fact') << Fact(state="write_to_csv"), priority=2, timeout=1)
async def write_to_csv(net, fact):
    dumper.write_to_csv(f'{dumper.dump_dir}/{dumper.current_date_str}.csv')
    fact['state'] = 'transform'
    net.update_fact(fact)


@Production(V('fact') << Fact(state="transform"), priority=2, timeout=1)
async def transform(net, fact):
    dumper.transform()
    fact['state'] = 'write_to_db'
    net.update_fact(fact)


@Production(V('fact') << Fact(state="write_to_db"), priority=2, timeout=1)
async def write_to_db(net, fact):
    dumper.write_to_db()
    print(f'date {dumper.current_date} finished')
    dumper.current_date += datetime.timedelta(days=1)
    fact['state'] = 'not loaded'
    net.update_fact(fact)


if __name__ == '__main__':
    url = 'https://iss.moex.com/iss/history/engines/currency/markets/selt/trades.json'
    db_filepath = r'C:\Users\mivallion\source\repos\reactive_deliberative\db.db'
    start_date = datetime.datetime(2022, 1, 10)
    end_date = datetime.datetime(2022, 1, 20)
    dump_dir = "./iss_dump/"
    external_directory = "./external/"
    dumper = MoexIssDumper(url, start_date, end_date, dump_dir, db_filepath, external_directory)

    rd = ReactiveDeliberative()
    rd.add_fact("not loaded", "state")
    rd.add_production(start_load)
    rd.add_production(get_from_url)
    rd.add_production(write_to_csv)
    rd.add_production(transform)
    rd.add_production(write_to_db)

    rd.add_reactive_action(external_upload_predicate, external_upload_action)
    rd.run()
