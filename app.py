import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# Load and prepare the data
csv_file_path = '/Users/alexemmons/Desktop/sales_data_sample.csv'
df = pd.read_csv(csv_file_path, encoding='ISO-8859-1')
df['ORDERDATE'] = pd.to_datetime(df['ORDERDATE'])
df['YEAR'] = df['ORDERDATE'].dt.year
df = df[df['COUNTRY'] == 'USA']

# Aggregate sales data by state and year
df_state_sales = df.groupby(['STATE', 'YEAR', 'PRODUCTLINE'])['SALES'].sum().reset_index()

# Calculate the percentage of each product line sold in each state
df_state_sales['TOTAL_SALES'] = df_state_sales.groupby(['STATE', 'YEAR'])['SALES'].transform('sum')
df_state_sales['PERCENTAGE'] = df_state_sales['SALES'] / df_state_sales['TOTAL_SALES'] * 100

# Initialize the Dash app
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("US Sales Data Heatmap"),
    
    dcc.Dropdown(
        id='year-dropdown',
        options=[{'label': str(year), 'value': year} for year in sorted(df['YEAR'].unique())],
        value=2003,
        clearable=False
    ),
    
    dcc.Slider(
        id='year-slider',
        min=df['YEAR'].min(),
        max=df['YEAR'].max(),
        value=df['YEAR'].min(),
        marks={str(year): str(year) for year in df['YEAR'].unique()},
        step=None
    ),
    
    dcc.Graph(id='sales-heatmap'),
    
    dcc.Graph(id='productline-pie')
])

# Single callback for syncing year-dropdown and year-slider
@app.callback(
    [Output('year-dropdown', 'value'),
     Output('year-slider', 'value')],
    [Input('year-dropdown', 'value'),
     Input('year-slider', 'value')]
)
def sync_year_components(dropdown_value, slider_value):
    ctx = dash.callback_context

    if not ctx.triggered:
        return dropdown_value, slider_value
    else:
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if triggered_id == 'year-dropdown':
            return dropdown_value, dropdown_value
        else:
            return slider_value, slider_value

@app.callback(
    Output('sales-heatmap', 'figure'),
    [Input('year-dropdown', 'value')]
)
def update_heatmap(selected_year):
    filtered_df = df_state_sales[df_state_sales['YEAR'] == selected_year]
    
    # Aggregate sales data by state
    df_state_total_sales = filtered_df.groupby('STATE')['SALES'].sum().reset_index()
    
    fig = px.choropleth(
        df_state_total_sales,
        locations='STATE',
        locationmode='USA-states',
        color='SALES',
        color_continuous_scale='Viridis',
        scope='usa',
        labels={'SALES': 'Total Sales ($)'}
    )
    
    fig.update_layout(
        title_text=f'Total Sales by State for {selected_year}',
        geo=dict(
            lakecolor='rgb(255, 255, 255)'
        )
    )
    
    return fig

@app.callback(
    Output('productline-pie', 'figure'),
    [Input('sales-heatmap', 'clickData'),
     Input('year-dropdown', 'value')]
)
def update_pie_chart(clickData, selected_year):
    if clickData is None:
        state = 'CA'  # Default state
    else:
        state = clickData['points'][0]['location']
    
    filtered_df = df_state_sales[(df_state_sales['STATE'] == state) & (df_state_sales['YEAR'] == selected_year)]
    
    fig = px.pie(
        filtered_df,
        names='PRODUCTLINE',
        values='PERCENTAGE',
        title=f'Percentage of Each Product Line Sold in {state} ({selected_year})',
        labels={'PERCENTAGE': 'Percentage of Sales'}
    )
    
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
