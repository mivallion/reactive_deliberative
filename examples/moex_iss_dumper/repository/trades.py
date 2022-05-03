from sqlalchemy import Column, Integer, Text, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Trades(Base):
    __tablename__ = "TRADES"
    id = Column('ID', Integer, primary_key=True, autoincrement=True)
    trade_date = Column('TRADEDATE', Integer)
    trade_time = Column('TRADETIME', Integer)
    sec_id = Column('SECID', Text)
    board_id = Column('BOARDID', Text)
    price = Column('PRICE', Float)
    vol_cur = Column('VOLCUR', Integer)
    inv_cur_vol = Column('INVCURVOL', Float)
    buy_sell = Column('BUYSELL', Text)
    trade_no = Column('TRADENO', Integer)


class TradesRepository:
    def __init__(self, sqlite_filepath):
        self.engine = create_engine(f"sqlite:///{sqlite_filepath}")
        Session = sessionmaker()
        Session.configure(bind=self.engine)
        self.session = Session()

    def add_trade(self, trade_date, trade_time, sec_id, board_id, price, vol_cur, inv_cur_vol, buy_sell, trade_no):
        new_trade = Trades(trade_date=trade_date,
                           trade_time=trade_time,
                           sec_id=sec_id,
                           board_id=board_id,
                           price=price,
                           vol_cur=vol_cur,
                           inv_cur_vol=inv_cur_vol,
                           buy_sell=buy_sell,
                           trade_no=trade_no)
        self.session.add(new_trade)

    def commit(self):
        self.session.commit()

    def clear_date(self, date):
        self.session.query(Trades).filter(Trades.trade_date == date).delete()
        self.session.commit()
