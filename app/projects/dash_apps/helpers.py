import asyncio
import aiohttp
import bs4
import datetime as dt
import json
import os
import pandas as pd
from functools import reduce

PROJECTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def get_dropdown_and_symbols():
    csv_file = pd.read_csv(PROJECTS_DIR + '/resources/companies.csv')
    companies = csv_file['Company'].fillna('None')
    symbols = csv_file['Symbol'].fillna('None')
    dropdown_options = [{"label": stock, 'value':symb} for stock, symb in zip(companies, symbols)]
    dropdown_options.extend([{"label": symb, 'value':symb} for symb in symbols])
    return dropdown_options, symbols.tolist()


def dt_to_str(time_stamp):
    return time_stamp.strftime('%Y-%m-%d %H:%M:%S')


def str_to_dt(date_str):
    return dt.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')


def load_stock_data(symbol):
    with open("stock_minute_data/{0}/{0}_{1}.json".format(symbol.lower(), (dt.datetime.date(dt.datetime.today()))), "r") as stock_json:
        data = json.load(stock_json)
        data['time'] = list(map(str_to_dt, data['time']))
    return {symbol: data}


def reduce_dict(dict1, dict2):
    if dict1 is None:
        return dict2
    if dict2 is not None:
        dict1.update(dict2)
    return dict1


async def query_yahoo_data(symbol):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://finance.yahoo.com/quote/{0}?p={0}&.tsrc=fin-srch'.format(symbol)) as resp:
                text = await resp.text()
                soup = bs4.BeautifulSoup(text, 'html.parser')
                tables = soup.find("div", {"id": "quote-summary"}).find_all('table')
                data = {}
                for tr in tables[0].find_all('tr'):
                    if tr.find_all('td')[1]['data-test'] != 'DAYS_RANGE-value' and tr.find_all('td')[1][
                        'data-test'] != 'FIFTY_TWO_WK_RANGE-value':
                        table_val = tr.find_all('td')[1].next.next
                    else:
                        table_val = tr.find_all('td')[1].next
                    data[tr.find_all('td')[0].next.next] = table_val
                for tr in tables[1].find_all('tr'):
                    if tr.find_all('td')[1]['data-test'] != 'DIVIDEND_AND_YIELD-value':
                        table_val = tr.find_all('td')[1].next.next
                    else:
                        table_val = tr.find_all('td')[1].next
                    data[tr.find_all('td')[0].next.next] =  table_val
                keys = list(data.keys())
                values = list(map(lambda x: 'N/A' if type(x) is bs4.element.Tag else str(x), data.values()))
                return {symbol: dict(zip(keys, values))}
    except AttributeError as e:
        print(symbol + ": " + str(e))
        return {symbol: [['Not Available'],['N/A']]}


def call_async_data(symbols):
    responses = [query_yahoo_data(symbol) for symbol in symbols]
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    done, _ = loop.run_until_complete(asyncio.wait(responses))
    return reduce(reduce_dict,[fut.result() for fut in done])


def convert_to_float(string):
    try:
        return float(string)
    except ValueError as e:
        return 0.0

