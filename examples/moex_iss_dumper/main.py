import datetime
import json
import urllib.request
import asyncio
import aiohttp

import pandas as pd


class MoexIssDumper:
    def __init__(self, url, start_date, end_date, dump_dir):
        self.url = url
        self.start_date = start_date
        self.end_date = end_date
        self.current_date = start_date
        self.dump_dir = dump_dir

    async def dump(self):
        while self.current_date <= self.end_date:
            df = pd.DataFrame()
            current_day_str = self.current_date.strftime("%Y%m%d")
            start = 0
            while True:

                async with aiohttp.ClientSession() as session:
                    async with session.get(f'{self.url}?date={current_day_str}&start={start}') as resp:
                        json_data = await resp.json()
                        data = json_data['trades']['data']
                        columns = json_data['trades']['columns']
                        tmp_df = pd.DataFrame(data, columns=columns)
                        if len(tmp_df) == 0:
                            break
                        df = pd.concat([df, tmp_df])
                        start += 5000

                if len(df) != 0:
                    df.to_csv(f'{self.dump_dir}/{current_day_str}.csv')
                self.current_date += datetime.timedelta(days=1)

            if len(df) != 0:
                df.to_csv(f'{self.dump_dir}/{current_day_str}.csv')
            self.current_date += datetime.timedelta(days=1)


if __name__ == '__main__':
    url = 'https://iss.moex.com/iss/history/engines/currency/markets/selt/trades.json'
    start_date = datetime.datetime(2002, 1, 10)
    end_date = datetime.datetime(2002, 1, 10)
    dump_dir = "E:/iss_dump/"
    dumper = MoexIssDumper(url, start_date, end_date, dump_dir)
    asyncio.run(dumper.dump())
