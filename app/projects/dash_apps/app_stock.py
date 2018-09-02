import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import datetime as dt
from app.projects.dash_apps import helpers
import json
import requests
import pandas as pd
pd.core.common.is_list_like = pd.api.types.is_list_like
import pandas_datareader.data as web
import plotly.graph_objs as go
import sys


def start_dash_stock(server):
    app = dash.Dash("app stock", server=server, url_base_pathname="/dummy/")


    sys.setrecursionlimit(10000)
    company_stats = {}
    company_stock_prices = {}
    peers = {}

    external_css = ["https://fonts.googleapis.com/css?family=Overpass:300,300i"]
    for css in external_css:
        app.css.append_css({"external_url": css})
    external_js = ['https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/js/materialize.min.js',
                   "https://codepen.io/chriddyp/pen/brPBPO.css"]
    for js in external_js:
        app.scripts.append_script({'external_url': js})

    TODAY = dt.datetime.today()
    DURATIONS = ['1m', '3m', '6m', 'y2d', '1y', '2y', '5y']
    DURATIONS_MAP = [TODAY - dt.timedelta(30),
                     TODAY - dt.timedelta(91),
                     TODAY - dt.timedelta(182),
                     dt.datetime(TODAY.year, 1, 1),
                     TODAY - dt.timedelta(365),
                     TODAY - dt.timedelta(365 * 2),
                     TODAY - dt.timedelta(365 * 5)]
    IEX_API_URL = 'https://api.iextrading.com/1.0/'
    DROPDOWN_OPTS, _ = helpers.get_dropdown_and_symbols()

    app.layout = html.Div(className='right_col', children=[
        html.Div([
            html.H1(children='Stocks Dashboard'),
            dcc.Dropdown(
                id='input', options=DROPDOWN_OPTS,
                value=['FTNT', 'AAPL'], multi=True
            ),
        ], style={'margin': 10}
        ),
        html.P('Moving average past n days',
               style={
                   'display': 'inline-block',
                   'verticalAlign': 'top',
                   'margin-left': 10,
               }
               ),
        html.Div([
            dcc.Slider(
                id='moving-average',
                min=0, max=100, step=1, value=20,
                marks={str(step): str(step) for step in range(0, 101, 10)}
            )
        ], style={'width': 500, 'display': 'inline-block', 'margin-top': '22px', 'margin-left': '15px'}
        ),
        html.Br(),
        html.P('Graph duration:',
               style={
                   'display': 'inline-block',
                   'verticalAlign': 'top',
                   'margin-left': 10,
               }
               ),
        html.Div([
            dcc.Slider(
                id='start-date',
                min=0, max=6, step=1, value=3,
                marks={step: duration for step, duration in enumerate(DURATIONS)}
            )
        ], style={'width': 500, 'display': 'inline-block', 'margin-top': '22px', 'margin-left': '15px',
                  'margin-bottom': '15px'}
        ),
        html.Div(children=html.Div(id='output-graphs'), className='row'),
        html.Br(),
        html.Br(),
        html.Div(children=html.Div(id='comparison-graph'), className='row'),

    ], style={
        'font-family': 'overpass',
        'overflow': 'auto',
        'background-color': '#F3F3F3',
        'height': '100vh',
    }, )


    @app.callback(
        Output(component_id='output-graphs', component_property='children'),
        [Input(component_id='input', component_property='value'),
         Input('moving-average', 'value'),
         Input('start-date', 'value')])
    def update_graph(input_tickers, moving_average, start_date):
        company_stats
        print(input_tickers)
        output_graphs = []
        comparisons_traces = []
        peers_added = []
        traces_scatter_pe_vs_eps = []
        start_datetime = DURATIONS_MAP[start_date]
        end_datetime = dt.datetime.now()

        if not all(company in list(company_stats.keys()) for company in input_tickers):
            company_stats.update(helpers.call_async_data(input_tickers))

        if len(input_tickers) > 2:
            class_choice = 'col s12 m12 l6'
        elif len(input_tickers) == 2:
            class_choice = 'col s12 m12 l6'
        else:
            class_choice = 'col s12'

        beta_values = list(map(helpers.convert_to_float, [company_stats[stock]['Beta'] for stock in input_tickers]))
        for stock in input_tickers:
            if stock not in peers.keys():
                peers[stock] = json.loads(requests.get(IEX_API_URL + '/stock/{}/peers'.format(stock)).text)
                if len(peers[stock]) > 3:
                    peers[stock] = peers[stock][:3]
                print(peers[stock])
            if stock not in company_stock_prices.keys():
                company_stock_prices[stock] = {}
            if start_date not in company_stock_prices[stock].keys():
                company_stock_prices[stock][start_date] = web.DataReader(stock, 'iex', start_datetime, end_datetime)
            if not all(peer in company_stats.keys() for peer in peers[stock]):
                company_stats.update(helpers.call_async_data(peers[stock]))

            for peer in peers[stock]:
                if peer not in company_stock_prices.keys():
                    company_stock_prices[peer] = {}
                if start_date not in company_stock_prices[peer].keys():
                    company_stock_prices[peer][start_date] = web.DataReader(peer, 'iex', start_datetime, end_datetime)

                if peer not in input_tickers and peer not in peers_added:
                    df_peer = company_stock_prices[peer][start_date]
                    df_peer['normalized'] = df_peer['close'] / df_peer['close'][0] - 1
                    comparisons_traces.append(go.Scatter(
                        x=df_peer.index,
                        y=df_peer['normalized'],
                        name=peer + ', peer of ' + stock,
                        line=dict(width=1),  # color='#a3a5a8'),
                        opacity=0.2,
                        showlegend=False,
                        xaxis='x1',
                        yaxis='y1')
                    )

            peer_scatter_plot_markers = [(company['EPS (TTM)'], company['PE Ratio (TTM)'], company['Beta'], key)
                                         for key, company in company_stats.items()
                                         if key in peers[stock]
                                         and 'EPS (TTM)' in company.keys()
                                         and 'PE Ratio (TTM)' in company.keys()
                                         and key not in peers_added
                                         and key not in input_tickers
                                         ]

            traces_scatter_pe_vs_eps.append(go.Scatter(
                x=list(map(helpers.convert_to_float, [marker[0] for marker in peer_scatter_plot_markers])),
                y=list(map(helpers.convert_to_float, [marker[1] for marker in peer_scatter_plot_markers])),
                mode='markers',
                name='Peer of ' + stock,
                text=[marker[3] for marker in peer_scatter_plot_markers],
                opacity=0.5,
                xaxis='x1',
                yaxis='y1',
                marker=dict(
                    size=10,
                    cmax=max(beta_values),
                    cmin=min(beta_values),
                    colorscale='Viridis',
                    color=list(map(helpers.convert_to_float, [marker[2] for marker in peer_scatter_plot_markers]))
                )
            )
            )
            peers_added.extend(peers[stock])

            df_searched = company_stock_prices[stock][start_date]
            df_searched['ma'] = df_searched['close'].rolling(window=moving_average, min_periods=0).mean()
            df_searched['normalized'] = df_searched['close'] / df_searched['close'][0] - 1

            trace_ohlc = go.Ohlc(
                x=df_searched.index,
                open=df_searched['open'],
                high=df_searched['high'],
                low=df_searched['low'],
                close=df_searched['close'],
                increasing=dict(line=dict(color='#17BECF')),
                decreasing=dict(line=dict(color='#7F7F7F')),
                name="ohlc",
                xaxis='x1',
                yaxis='y1'
            )

            trace_ma = go.Scatter(
                x=df_searched.index,
                y=df_searched['ma'],
                name=(str(moving_average) + ' days moving average'),
                line=dict(color='#ff0000', width=1),
                xaxis='x1',
                yaxis='y1'
            )

            trace_volume = go.Scatter(
                x=df_searched.index,
                y=df_searched['volume'],
                name='volume',
                line=dict(color='#f45c42', width=1),
                xaxis='x1',
                yaxis='y2',
                fill='tozeroy',
            )

            trace_table = go.Table(
                header=dict(
                    values=[['<b>Info</b> <br>'], ['<b>Value</b>']]
                ),
                cells=dict(
                    values=[list(company_stats[stock].keys()), list(company_stats[stock].values())]
                ),
                domain={'x': [0.65, 1], 'y': [0, 1]}
            )

            layout = go.Layout(
                legend=dict(x=0, y=0.9),
                title=stock,
                font=dict(family='overpass'),
                xaxis1=dict(
                    domain=[0, 0.6],
                    anchor='y1',
                    rangeslider=dict(visible=False)
                ),
                yaxis1=dict(
                    domain=[0.3, 1],
                    anchor='x1'
                ),
                yaxis2=dict(
                    domain=[0, 0.2],
                    anchor='y2'
                ),
                margin=dict(
                    l=30,
                    r=30,
                    b=10,
                    t=60,
                ),
            )

            comparisons_traces.append(
                go.Scatter(
                    x=df_searched.index,
                    y=df_searched['normalized'],
                    name=stock,
                    line=dict(width=3),
                    xaxis='x1',
                    yaxis='y1'
                )
            )

            figure_price_graphs = dict(data=[trace_ohlc, trace_ma, trace_volume, trace_table], layout=layout)
            output_graphs.append(html.Div(dcc.Graph(id=stock, figure=figure_price_graphs), className=class_choice,
                                          style={
                                              'margin-left': 'auto',
                                              'margin-right': 'auto',
                                              'font-family': 'overpass',
                                              'padding': '10',
                                              'padding-top': '20',
                                              'padding-bottom': '40',
                                          }
                                          )
                                 )

        output_graphs.append(html.Br())
        comparisons_figure = dict(
            data=comparisons_traces,
            layout=go.Layout(
                title='Performance of Searched Stocks Against Their Peers',
                font=dict(family='overpass'),

                yaxis=dict(title='Percent change'),
                margin=dict(
                    l=80,
                    r=80,
                    b=30,
                )
            )
        )

        print(json.dumps(company_stats, indent=2))

        searched_pe_vs_eps = go.Scatter(
            x=list(map(helpers.convert_to_float, [company_stats[stock]['EPS (TTM)']
                                                  for stock in input_tickers])),
            y=list(map(helpers.convert_to_float, [company_stats[stock]['PE Ratio (TTM)']
                                                  for stock in input_tickers])),
            mode='markers',
            name='seached stock',
            text=input_tickers,
            marker=dict(
                size=35,
                cmax=max(beta_values),
                cmin=min(beta_values),
                color=beta_values,
                colorscale='Viridis',
                colorbar=dict(title='beta'),
                showscale=True
            ),
            xaxis='x1',
            yaxis='y1'
        )
        traces_scatter_pe_vs_eps.append(searched_pe_vs_eps)

        figure_pe_vs_eps = dict(
            data=traces_scatter_pe_vs_eps,
            layout=go.Layout(
                title='P/E vs EPS of Searched Stocks and Their Peers',
                font=dict(family='overpass'),
                yaxis=dict(title='PE Ratio'),
                xaxis=dict(title='EPS'),
                showlegend=False
            )
        )
        output_graphs.append(html.Div(dcc.Graph(id='comparison', figure=comparisons_figure), className='col s12 m12 l12',
                                      style={
                                          'margin-left': 'auto',
                                          'margin-right': 'auto',
                                          'font-family': 'overpass',
                                          'padding': '10',
                                          'padding-top': '20',
                                          'padding-bottom': '40',
                                      }
                                      )
                             )
        output_graphs.append(html.Div(dcc.Graph(id='pe-vs-eps', figure=figure_pe_vs_eps), className='col s12 m12 l6'))

        return output_graphs
    return app
