import dash
from dash.dependencies import Output, Event, Input
import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt
import plotly
import random
import plotly.graph_objs as go
import plotly.figure_factory as ff
import sqlite3
import pandas as pd
import os
import sys
sys.path.insert(0, os.path.realpath(os.path.dirname(__file__)))
os.chdir(os.path.realpath(os.path.dirname(__file__)))

connection = sqlite3.connect('twitter.db',  check_same_thread=False)

app = dash.Dash(__name__)

#NovaTec Image
app.layout = html.Div([
                html.Div([
                    html.Div([
                        html.Img(src="https://www.openpr.de/images/articles/8/6/86d9767926219cba246727cb81286271_g.jpg",
                                style={
                                         'height': '100px',
                                         'align': 'middle',
                                         'bottom': '145px',
                                         'left': '5px'
                                        }
                                 )
                            ], className="col s12 m6 l2"),

                    html.Div([
                        html.H2('Twitter Sentiment Analyzer with Machine Learning')
                            ], className="col s12 m6 l8")
                        ], className = "row"),



                #Keyword Input and Number Definition with Slider
                dcc.Input(id='keyword',placeholder='Enter Keyword', value='', type='text'),
                dcc.Slider(id='sliderid', value=300, min=10, max=1000, step=100,
                           marks={10: '10 Tweets ', 100:'100 ', 200:'200 ', 300:'300 ', 400:'400 ',
                                  500:'500 ', 600:'600 ', 700:'700 ', 800:'800 ',
                                  900:'900 ', 1000:'1000 '}),
                html.Div([html.P("                                                                                  "
                                 "                                                                                  ")]),
    
                #Pie Chart and Sentiment Line Diagram
                html.Div([
                    html.Div([
                        html.H4('  '),
                        html.H5('  '),
                        html.H5('Real Time Pie Chart'),
                        dcc.Graph(id='pie', animate=False),], className ='col s12 m8 l4'),

                    html.Div([
                        html.H4('  '),
                        html.H5('  '),
                        html.H5('Real Time Sentiment Line'),
                        dcc.Graph(id='live-graph', animate=True),], className = 'col s12 m8 l8')

                         ], className = 'row'),


                html.Div([html.H5('Last 5 Tweets'),
                          html.Div(id='datatable', style={'width': '200%','display': 'inline-block' }),
                        ], className = 'col s12'),
                dcc.Interval(
                    id='graph-update',
                    interval=1*1000)
            ], className = "container", style={'width':'96%','margin-left':30,'margin-right':30,'max-width':50000}
        )



def generate_table(dataframe, max_rows=5):
    return html.Table(
        [
            html.Tr([html.Th("Sentiment"), html.Th("Tweet")])
        ] +
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )

#Function to return the pie chart with the data
@app.callback(Output('pie', 'figure'),
              [Input(component_id='keyword', component_property='value'),
               Input('sliderid', 'value')],
              events=[Event('graph-update', 'interval')])
def update_pie_scatter(keyword, sliderid):
    #connect to Database

    c = connection.cursor()

    df = pd.read_sql("SELECT * FROM sentiment WHERE tweet LIKE ? ORDER BY unix DESC LIMIT 1000", connection,
                     params=('%' + keyword + '%',))
    df.sort_values('unix', inplace=True)
    df.dropna(inplace=True)

    X = 'positive','negative'
    numbers = df.sentiment.values[-sliderid:]
    positiv = 1
    negativ = -1
    negcount = 0
    poscount = 0
    for i in numbers:
        if i == positiv:
            poscount += 1
        if i == negativ:
            negcount += 1

    colors = [ '#2E64FE', '#D8D8D8']

    return {'data': [go.Pie(labels=X, values=[poscount,negcount],  hoverinfo='label+value+percent', textinfo='value',
                            textfont=dict(size=20),
                            marker=dict(colors=colors,
                                        line=dict(color='#000000', width=2))
                            )],
            'layout' : go.Layout(autosize=False, width=500, height=500,
                                 margin=go.Margin(
                                    l=50,
                                    r=50,
                                    b=100,
                                    t=100,
                                    pad=4
                                ), title='Keyword: {}'.format(keyword))
                                    }


#Function for the tweet table
@app.callback(Output('datatable', 'children'),
              [Input(component_id='keyword', component_property='value')],
              events=[Event('graph-update', 'interval')])
def update_table_scatter(keyword):
    #connect to Database

    c = connection.cursor()

    df = pd.read_sql("SELECT * FROM sentiment WHERE tweet LIKE ? ORDER BY unix DESC LIMIT 1000", connection,
                     params=('%' + keyword + '%',))

    sent = df.sentiment.values[-5:]
    pos = 1
    neg = -1
    val = []
    for i in sent:
        if i == pos:
            val.append('positive')
        if i == neg:
            val.append('negative')


    d = {'Tweet': df.tweet.values[-5:], 'Sentiment': val}
    dff= pd.DataFrame(data=d)

    #tweets = df.sentiment.values[-5:]


    return generate_table(dff)


#Function to return the sentiment line out of the given data
@app.callback(Output('live-graph', 'figure'),
              [Input(component_id='keyword', component_property='value')],
              events=[Event('graph-update', 'interval')])
def update_graph_scatter(keyword):

    c = connection.cursor()

    df = pd.read_sql("SELECT * FROM sentiment WHERE tweet LIKE ? ORDER BY unix DESC LIMIT 1000", connection,
                     params=('%' + keyword + '%',))
    df.sort_values('unix', inplace=True)
    df['sentiment_smoothed'] = df['sentiment'].rolling(int(len(df) /10)).mean()
    df['date'] = pd.to_datetime(df['unix'], unit='ms')
    df.set_index('date', inplace=True)



    df.dropna(inplace=True)

    X = df.unix.values[-100:]
    Y = df.sentiment_smoothed.values[-100:]

    data = plotly.graph_objs.Scatter(
            x=list(X),
            y=list(Y),
            name='Scatter',
            mode= 'lines+markers'
            )

    return {'data': [data],'layout' : go.Layout(xaxis=dict(range=[min(X),max(X)]),
                                                yaxis=dict(range=[min(Y),max(Y)]))}

external_css = ["https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/css/materialize.min.css"]
for css in external_css:
    app.css.append_css({"external_url": css})

external_js = ['https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/js/materialize.min.js']
for js in external_js:
    app.scripts.append_script({'external_url': js})

server = app.server
dev_server = app.run_server
