import asyncio
import datetime

import aiohttp
import pandas as pd

from repository.trades import TradesRepository


class MoexIssDumper:
    def __init__(self, url, start_date, end_date, dump_dir, db_filepath):
        self.url = url
        self.start_date = start_date
        self.end_date = end_date
        self.current_date = start_date
        self.dump_dir = dump_dir
        self.trades = TradesRepository(db_filepath)
        self.processed_dates = []

    @property
    def current_date_str(self):
        return self.current_date.strftime("%Y%m%d")

    @staticmethod
    def write_to_csv(df, filename):
        if len(df) != 0:
            df.to_csv(filename)

    def write_to_db(self, df):
        self.trades.clear_date(int(self.current_date_str))
        for _, row in df.iterrows():
            self.trades.add_trade(
                row['TRADEDATE'],
                row['TRADETIME'],
                row['SECID'],
                row['BOARDID'],
                row['PRICE'],
                row['VOLCUR'],
                row['INVCURVOL'],
                row['BUYSELL'],
                row['TRADENO'],
            )
        self.trades.commit()

    @staticmethod
    def transform(df):
        transformed_df = df.copy()
        transformed_df['TRADEDATE'] = pd.to_datetime(df.TRADEDATE).apply(
            lambda x: x.year * 10000 + x.month * 100 + x.day)
        transformed_df['TRADETIME'] = pd.to_datetime(df.TRADETIME).apply(
            lambda x: x.hour * 10000 + x.minute * 100 + x.second)
        return transformed_df

    async def get_from_url(self):
        df = pd.DataFrame()
        start = 0
        while True:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'{self.url}?date={self.current_date_str}&start={start}') as resp:
                    json_data = await resp.json()
                    data = json_data['trades']['data']
                    columns = json_data['trades']['columns']
                    tmp_df = pd.DataFrame(data, columns=columns)
                    if len(tmp_df) == 0:
                        break
                    df = pd.concat([df, tmp_df])
                    start += 5000
        return df

    async def dump(self):
        while self.current_date <= self.end_date:
            df = await self.get_from_url()
            self.write_to_csv(df, f'{self.dump_dir}/{self.current_date_str}.csv')
            df = self.transform(df)
            self.write_to_db(df)
            self.processed_dates.append(self.current_date_str)
            self.current_date += datetime.timedelta(days=1)


if __name__ == '__main__':
    url = 'https://iss.moex.com/iss/history/engines/currency/markets/selt/trades.json'
    db_filepath = r'./db.db'
    start_date = datetime.datetime(2002, 1, 10)
    end_date = datetime.datetime(2002, 1, 10)
    dump_dir = "./iss_dump/"
    dumper = MoexIssDumper(url, start_date, end_date, dump_dir, db_filepath)
    asyncio.run(dumper.dump())
