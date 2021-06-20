import pandas as pd

# Загрузим необходимые пакеты
import dash
import dash_core_components as dcc
import dash_html_components as html

from apiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials



SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
KEY_FILE_LOCATION = 'C:\\Users\\gggun\\Downloads\\client_secrets.json'
VIEW_ID = '217283970'

credentials = ServiceAccountCredentials.from_json_keyfile_name(KEY_FILE_LOCATION, SCOPES)

# Build the service object.
analytics = build('analyticsreporting', 'v4', credentials=credentials)

response = analytics.reports().batchGet(body={
    'reportRequests': [{
        'viewId': VIEW_ID,
        'dateRanges': [{'startDate': '2020-04-21', 'endDate': 'today'}],
        'metrics': [
            {"expression": "ga:pageviews"},
            {"expression": "ga:avgSessionDuration"}
        ], "dimensions": [
            {"name": "ga:medium"}
        ]
    }]}).execute()
response


def ga_response_dataframe(response):
    row_list = []
    # Get each collected report
    for report in response.get('reports', []):
        # Set column headers
        column_header = report.get('columnHeader', {})
        dimension_headers = column_header.get('dimensions', [])
        metric_headers = column_header.get('metricHeader', {}).get('metricHeaderEntries', [])

        # Get each row in the report
        for row in report.get('data', {}).get('rows', []):
            # create dict for each row
            row_dict = {}
            dimensions = row.get('dimensions', [])
            date_range_values = row.get('metrics', [])

            # Fill dict with dimension header (key) and dimension value (value)
            for header, dimension in zip(dimension_headers, dimensions):
                row_dict[header] = dimension

            # Fill dict with metric header (key) and metric value (value)
            for i, values in enumerate(date_range_values):
                for metric, value in zip(metric_headers, values.get('values')):
                    # Set int as int, float a float
                    if ',' in value or '.' in value:
                        row_dict[metric.get('name')] = float(value)
                    else:
                        row_dict[metric.get('name')] = int(value)

            row_list.append(row_dict)
    return pd.DataFrame(row_list)


response = analytics.reports().batchGet(body={
    'reportRequests': [{
        'viewId': VIEW_ID,
        'dateRanges': [{'startDate': '2021-01-01', 'endDate': '2021-06-18'}],
        'metrics': [
            {"expression": "ga:sessions"},
        ], "dimensions": [
            {"name": "ga:date"},
            {"name": "ga:browser"}
        ], "samplingLevel": "LARGE",
        "pageSize": 10000
    }]}).execute()

df = ga_response_dataframe(response)
df['ga:date'] = pd.to_datetime(df['ga:date'])

# Переименовываем столбцы
df = df.rename(columns={'ga:date': 'date', 'ga:browser': 'browser', 'ga:sessions': 'session'})

# Pivot table to have browsers as columns
df_plot = df.pivot('date', 'browser', 'session').reset_index()


# Получаем ТОП-5 популярных браузеров
top_brouser_by_session = pd.DataFrame(df_plot.sum()).reset_index().sort_values(0, ascending=False).head(5)

# Получаем 5 отдельных списков для каждого популярного браузера
graf_list = []
column_name = []
for i in top_brouser_by_session.browser:
    one_browser_list = []
    column_name.append(i)
    one_list = df_plot[i]
    for j in one_list:
        j = int(j)
        one_browser_list.append(j)
    graf_list.append(one_browser_list)

# Получаем список из дат
data_list = []
for i in df_plot.date:
    data_list.append(i)


# Выводим в Dash
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),

    html.Col(),

    html.Div(children='''
        Dash: A web application framework for Python.
    '''),

    dcc.Graph(
        id='example-graph',
        figure={
            'data': [
                {'x': data_list, 'y': graf_list[0], 'name': column_name[0]},
                {'x': data_list, 'y': graf_list[1], 'name': column_name[1]},
                {'x': data_list, 'y': graf_list[2], 'name': column_name[2]},
                {'x': data_list, 'y': graf_list[3], 'name': column_name[3]},
                {'x': data_list, 'y': graf_list[4], 'name': column_name[4]},
            ],
            'layout': {
                'title': 'Dash Data Visualization',
            }
        },
        style={'float': 'left', 'width': '50%'})
])
if __name__ == '__main__':
    app.run_server(debug=True)