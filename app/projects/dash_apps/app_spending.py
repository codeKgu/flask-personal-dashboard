import dash
import datetime as dt
import plotly.graph_objs as go
import pickle
import cmocean
import numpy as np
import dash_core_components as dcc
import dash_html_components as html
from app.projects.dash_apps.helpers import PROJECTS_DIR

def start_dash_spending(server):

    app = dash.Dash("app spending", server=server, url_base_pathname="/dummy1/")
    mapbox_access_token = 'pk.eyJ1Ijoia2VuZ3UxMyIsImEiOiJjamw5dzQwbjAweGZ0M2txaGg5MmM2NjR3In0.Ji0-R5KGO2yxqWuWcSgv1g'
    data_fnames = ['location_info.pickle', 'all_info.pickle', 'category_count.pickle']


    def load_data(data_fnames):
        dfs = []
        for file_name in data_fnames:
            pickle_in = open( PROJECTS_DIR + '/resources/' + file_name, 'rb')
            dfs.append(pickle.load(pickle_in))
            pickle_in.close()
        return dfs


    def cmocean_to_plotly(cmap, pl_entries):
        h = 1.0/(pl_entries-1)
        pl_colorscale = []
        for k in range(pl_entries):
            C = list(map(np.uint8, np.array(cmap(k*h)[:3])*255))
            pl_colorscale.append([k*h, 'rgb'+str((C[0], C[1], C[2]))])
        return pl_colorscale


    pickled_data = load_data(data_fnames)
    location_info_df = pickled_data[0]
    all_info_reversed = pickled_data[1].iloc[::-1]
    category_count = pickled_data[2]

    matter = cmocean_to_plotly(cmocean.cm.matter, max(abs(location_info_df['Amount'].map(lambda x: int(100*x)))))

    map_data = go.Scattermapbox(lat=location_info_df['lat'].tolist(),
                                lon=location_info_df['long'].tolist(),
                                text=["{} \n {}  {} ${}".format(v1,v2,v3,v4) for v1, v2, v3, v4 in
                                      zip(location_info_df['address'].tolist(),
                                          location_info_df['name'].tolist(),
                                          location_info_df['Posting Date'].tolist(),
                                          location_info_df['Amount'].tolist()
                                          )
                                      ],
                                mode='markers',
                                hoverinfo ='text',
                                marker=dict(
                                    size=14,
                                    #color='rgb(255, 150, 150)',
                                    colorscale=matter,
                                    cmin=0,
                                    color=abs(location_info_df['Amount'].map(lambda x: int(100*x))),
                                    cmax=max(abs(location_info_df['Amount'].map(lambda x: int(100*x)))),
                                    colorbar=dict(
                                        title="Spending"
                                    )
                                )
                            )


    map_layout = go.Layout(
                           autosize=True,
                           font=dict(family='overpass', size=18),
                           hovermode='closest',
                           mapbox=dict(
                           accesstoken=mapbox_access_token,
                           bearing=0,
                           center=dict(
                               lat=34.059300,
                               lon=-118.440454
                           ),
                           pitch=0,
                           zoom=10,
                           style='streets',
                            ),
                            margin=dict(
                                l=30,
                                r=30,
                                b=20,
                                t=20,
                            ),
                           height = 700
                           )

    map_figure = dict(data=[map_data], layout=map_layout)

    trace_spending = dict(type = 'scatter',
                          x = all_info_reversed['datetime'].tolist(),
                          y = all_info_reversed['Balance'].tolist(),
                          mode = 'lines',
                          name = 'lines',
                          text = ['{}\n ${}'.format(v2[:-5], v1)for v1, v2 in
                                  zip(all_info_reversed['Amount'], all_info_reversed['Description'])],
                          )
    layout_spending = dict(title ='Spending Since Start of College',
                           autosize=True,
                           font=dict(family='overpass'),
                           yaxis = dict(title = 'Balance'),
                            margin=dict(
                                l=45,
                                r=45,
                                b=30,
                                t=50,
                            ),
                           annotations=[
                               dict(x=dt.datetime(2017,3,27),
                                    y=622.24,
                                    ay = -80,
                                    text='Spring Break 2017',
                                    showarrow=True
                                    ),
                               dict(x=dt.datetime(2017,11,22),
                                    y=1200,
                                    ay = -20,
                                    text='Thanksgiving 2017',
                                    showarrow=True
                                    ),
                               dict(x=dt.datetime(2018,7,2),
                                    y=1145,
                                    ay = -50,
                                    ax = -70,
                                    text='Ticketmaster First Paycheck',
                                    showarrow=True
                                    )
                           ]
                           )
    figure_spending = dict(data=[trace_spending], layout=layout_spending)

    trace_bar = go.Bar(x= [key.replace("_"," ") for key in list(category_count.keys())],
                       y=[100 *val/sum(list(category_count.values())) for val in category_count.values()],
                       text=["{:.2f}%".format(100 *val/sum(list(category_count.values()))) for val in category_count.values()],
                       hoverinfo = 'text',
                       opacity=0.9,
                       marker=dict(color='rgba(219, 64, 82, 0.7)'),
                       )

    layout_bar = dict(
                autosize=True,
                margin=dict(
                                l=45,
                                r=30,
                                b=80,
                                t=50,
                            ),
                font=dict(family='overpass'),
                title='Spending by Category',
                yaxis=dict(title='Percent '),
    )

    figure_bar = dict(data=[trace_bar], layout=layout_bar)

    app.layout = html.Div(className='right_col', children=[
        html.Div(children=[
        html.Div([
            html.H1(
                #src="https://datashop.cboe.com/Themes/Livevol/Content/images/logo.png",
                className='two columns',
                # style={
                #     'height': '60',
                #     'width': '160',
                #     'float': 'left',
                #     'position': 'relative',
                # },
            ),
            html.H1(
                    'A Look at My Spending',
                className='eight columns',
                style={'text-align': 'center', 'font-family': 'overpass'}
            ),
            html.H1(
                #src="https://s3-us-west-1.amazonaws.com/plotly-tutorials/logo/new-branding/dash-logo-by-plotly-stripe.png",
                className='two columns',
                # style={
                #     'height': '60',
                #     'width': '135',
                #     'float': 'right',
                #     'position': 'relative',
                # },
            ),
        ],
            className='row'
        ),
        html.Hr(style={'margin': '0', 'margin-bottom': '25'}),
                    html.Div(
                        dcc.Graph(
                            id='map',
                            figure=map_figure
                        ),
                    ),
                    html.Br(),
                    html.Div(
                        children=[
                            html.Div(
                                dcc.Graph(
                                    id='line-graph',
                                    figure=figure_spending
                                ),
                                className="eight columns"
                            ),
                            html.Div(
                                dcc.Graph(
                                    id='bar-graph',
                                figure=figure_bar
                                ),
                                className='four columns'
                            )
                            ],
                        className='row')])
    ],
        style={
            'font-family': 'overpass',
            'background-color': '#F3F3F3',
            'overflow': 'auto',
            'height': '100vh',
        },

    )

    external_css = [PROJECTS_DIR + '/static/spending.css',
                    "https://fonts.googleapis.com/css?family=Overpass:300,300i",
                    "https://cdn.rawgit.com/plotly/dash-app-stylesheets/62f0eb4f1fadbefea64b2404493079bf848974e8/dash-uber-ride-demo.css",
                    "https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css"]


    for css in external_css:
        app.css.append_css({"external_url": css})

    return app
