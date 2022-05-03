import asyncio
import datetime
from os import listdir
from os.path import join, isfile
from pathlib import Path

import aiohttp
import pandas as pd

from examples.moex_iss_dumper.repository.trades import TradesRepository


def get_directory_files(path):
    return [join(path, f) for f in listdir(path) if isfile(join(path, f))]


class MoexIssDumper:
    def __init__(self, url, start_date, end_date, dump_dir, db_filepath, external_directory):
        self.url = url
        self.start_date = start_date
        self.end_date = end_date
        self.current_date = start_date
        self.dump_dir = dump_dir
        self.external_directory = external_directory
        self.trades = TradesRepository(db_filepath)
        self.processed_dates = []
        self.processed_external_files = []
        self.current_dataframe = pd.DataFrame()
        self.offset = 0
        self.previous_length = 0

    @property
    def current_date_str(self):
        return self.current_date.strftime("%Y%m%d")

    def write_to_csv(self, filename):
        if len(self.current_dataframe) != 0:
            Path(Path(filename).parent).mkdir(parents=True, exist_ok=True)
            self.current_dataframe.to_csv(filename)

    def write_to_db(self):
        self.trades.clear_date(int(self.current_date_str))
        for _, row in self.current_dataframe.iterrows():
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

    def transform(self):
        self.current_dataframe['TRADEDATE'] = pd.to_datetime(self.current_dataframe.TRADEDATE). \
            apply(lambda x: x.year * 10000 + x.month * 100 + x.day)
        self.current_dataframe['TRADETIME'] = pd.to_datetime(self.current_dataframe.TRADETIME). \
            apply(lambda x: x.hour * 10000 + x.minute * 100 + x.second)

    async def get_batch_from_url(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{self.url}?date={self.current_date_str}&start={self.offset}') as resp:
                json_data = await resp.json()
                data = json_data['trades']['data']
                columns = json_data['trades']['columns']
                tmp_df = pd.DataFrame(data, columns=columns)
                if len(tmp_df) == 0:
                    return False
                self.current_dataframe = pd.concat([self.current_dataframe, tmp_df])
                self.offset += 5000
        return True

    def clear_buffer(self):
        self.current_dataframe = pd.DataFrame()
        self.offset = 0
        self.previous_length = 0

    async def get_from_url(self):
        while await self.get_batch_from_url():
            print(
                f'loaded {len(self.current_dataframe) - self.previous_length}: from {self.previous_length} to {len(self.current_dataframe)}')
            self.previous_length = len(self.current_dataframe)

    async def dump(self):
        await self.get_from_url()
        if len(self.current_dataframe) > 0:
            self.write_to_csv(f'{self.dump_dir}/{self.current_date_str}.csv')
            self.transform()
            self.write_to_db()
        self.processed_dates.append(self.current_date_str)
        self.current_date += datetime.timedelta(days=1)

    async def external_upload(self, filepath):
        df_buffer = self.current_dataframe.copy()
        date_buffer = self.current_date

        self.current_dataframe = pd.read_csv(filepath)
        self.current_date = datetime.datetime.strptime(Path(filepath).name[:-4], "%Y%m%d")
        if len(self.current_dataframe) > 0:
            self.transform()
            self.write_to_db()
        self.processed_dates.append(self.current_date_str)
        self.current_date = date_buffer
        self.current_dataframe = df_buffer
        self.processed_external_files.append(filepath)

    async def external_upload_predicate(self):
        files = get_directory_files(self.external_directory)
        await asyncio.sleep(0)
        return len(set(files).difference(self.processed_external_files)) > 0

    async def external_upload_action(self):
        files = get_directory_files(self.external_directory)
        files = set(files).difference(self.processed_external_files)
        await asyncio.sleep(0)
        for file in files:
            print(f'external uploading {file}')
            await self.external_upload(file)
