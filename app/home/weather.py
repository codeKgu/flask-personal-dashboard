import calendar
import datetime as dt
import json
import os
import pandas as pd
import requests
from app.home import blueprint


DIR_PATH = os.path.dirname(os.path.abspath(__file__))

WEATHER_API_URL = ' http://api.openweathermap.org/data/2.5/{}?{}&units=metric&APPID='

if 'WEATHER_API_KEY' in os.environ.keys():
    WEATHER_API_KEY = os.environ['WEATHER_API_KEY']
else:
    WEATHER_API_KEY = 'e1600e98c3db622543c7a808f5b01129'


cities = pd.read_json(DIR_PATH + '/resources/city.list.json')
countries = pd.read_csv(DIR_PATH + '/resources/country-iso-codes.csv')
cities['name'] = cities['name'].map(lambda x: str(x).lower())
countries['name'] = countries['name'].map(lambda x: str(x).lower())
weather_cache = {}
weekday = list(calendar.day_abbr)
today = dt.datetime.strftime(dt.datetime.today().date(), '%m-%d')
weekdate = calendar.day_name[dt.datetime.weekday(dt.datetime.today())]

def get_weather_city(city_name, country_name):
    city_name = city_name.lower()
    country_name = country_name.lower()
    country = countries[countries['name'] == country_name]
    city = cities[(cities['name'] == city_name) & (cities['country'] == country['alpha-2'].iloc[0])]
    city_id = city['id'].iloc[0]
    request_str = WEATHER_API_URL.format('weather', 'id=' + str(city_id)) + WEATHER_API_KEY
    resp = json.loads(requests.get(request_str).text)
    if city_name + country_name + today not in weather_cache.keys():
        request_url = WEATHER_API_URL.format('forecast', 'id=' + str(city_id)) + WEATHER_API_KEY
        weather_cache[city_name + country_name + today] = get_weather_from_url(request_url)
    return weather_cache[city_name + country_name + today], resp


def get_weather_from_url(request_str):
    resp = json.loads(requests.get(request_str).text)['list']
    resp_df = pd.DataFrame.from_dict(resp)
    resp_df = pd.concat([resp_df.drop(['main', 'weather'], axis=1),
                      resp_df['main'].apply(pd.Series),
                      resp_df['weather'].apply(lambda x: pd.Series(x[0]))], axis=1)
    grouped = resp_df.groupby(resp_df['dt_txt'].apply(lambda x: x[:10]))
    weather = grouped['temp_min', 'temp_max', 'main', 'id', 'description'].agg({
                         'temp_min':'min',
                         'temp_max':'max',
                         'main': lambda x: x.value_counts().idxmax(),
                         'id': lambda x: 'wi wi-owm-day-' + str(x.value_counts().idxmax()),
                         'description':lambda x: x.value_counts().idxmax().capitalize()})
    weather.reset_index(inplace=True)
    weather['weekday'] = weather['dt_txt'].apply(lambda x: weekday[dt.datetime.weekday(dt.datetime.strptime(x, '%Y-%m-%d'))])
    return weather, resp


@blueprint.before_app_first_request
def get_weather_ucla():
    request_str = WEATHER_API_URL.format('weather', 'lat=34.0689&lon=118.4452') + WEATHER_API_KEY
    resp = json.loads(requests.get(request_str).text)
    resp['icon'] = 'wi wi-owm-night-{}'.format(resp['weather'][0]['id'])
    resp['time'] = dt.datetime.now().time().strftime('%I:%M %p')
    if 'ucla' + today not in weather_cache.keys():
        weather_cache['ucla' + today] = get_weather_from_url(WEATHER_API_URL.format('forecast', 'lat=34.0689&lon=118.4452') + WEATHER_API_KEY)
    return weather_cache['ucla' + today][0], weather_cache['ucla' + today][1][:8], resp
