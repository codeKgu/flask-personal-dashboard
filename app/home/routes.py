from app.home import blueprint
from app.home import weather
from flask import render_template
from flask_login import login_required
from requests import get
import json


@blueprint.route('/index')
@login_required
def index():
    resp = json.loads(get('https://quotes.rest/qod?category=inspire').text)
    if 'contents'in resp.keys():
        quote_resp = 'https://quotes.rest/qod?category=inspire' ['contents']['quotes'][0]
    else:
        quote_resp = weather.quote_resp
    weather_df, forecast_weather, curr_weather = weather.get_weather_ucla()
    weekdays = weather_df['weekday'].tolist()
    description = weather_df['description'].tolist()
    temp_min = weather_df['temp_min'].tolist()
    temp_max = weather_df['temp_max'].tolist()
    id = weather_df['id']
    curr_weather['weekday'] = weather.weekdate
    return render_template('index.html', weekdays=weekdays, description=description, temp_min=temp_min,
                        temp_max=temp_max, id=id, items=len(weekdays), curr_weather=curr_weather, forecast_weather=forecast_weather,
                           quote_resp=quote_resp)


@blueprint.route('/<template>')
@login_required
def route_template(template):
    return render_template(template + '.html')
