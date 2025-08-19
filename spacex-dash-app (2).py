# Import required libraries
import pandas as pd
import dash
from dash import html
from dash import dcc
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go

# Read the airline data into pandas dataframe
spacex_df = pd.read_csv("https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBM-DS0321EN-SkillsNetwork/datasets/spacex_launch_dash.csv")
max_payload = spacex_df['Payload Mass (kg)'].max()
min_payload = spacex_df['Payload Mass (kg)'].min()

# Create a dash application
app = dash.Dash(__name__)

# Get unique launch sites for dropdown options
launch_sites = spacex_df['Launch Site'].unique()

# Create an app layout
app.layout = html.Div(children=[
    html.H1('SpaceX Launch Records Dashboard',
            style={'textAlign': 'center', 'color': '#503D36', 'font-size': 40}),
    
    # TASK 1: Add a dropdown list to enable Launch Site selection
    # The default select value is for ALL sites
    dcc.Dropdown(id='site-dropdown',
                 options=[{'label': 'All Sites', 'value': 'ALL'}] + 
                        [{'label': site, 'value': site} for site in launch_sites],
                 value='ALL',
                 placeholder="Select a Launch Site here",
                 searchable=True),
    html.Br(),

    # TASK 2: Add a pie chart to show the total successful launches count for all sites
    # If a specific launch site was selected, show the Success vs. Failed counts for the site
    html.Div(dcc.Graph(id='success-pie-chart')),
    html.Br(),
    
    html.P("Payload range (Kg):"),
    # TASK 3: Add a slider to select payload range
    dcc.RangeSlider(id='payload-slider',
                   min=0,
                   max=10000,
                   step=1000,
                   marks={0: '0',
                          2500: '2500',
                          5000: '5000',
                          7500: '7500',
                          10000: '10000'},
                   value=[min_payload, max_payload]),
    html.Br(),

    # TASK 4: Add a scatter chart to show the correlation between payload and launch success
    html.Div(dcc.Graph(id='success-payload-scatter-chart')),
    html.Br(),
    
    # NEW: Add a categorical plot to show Flight Number vs Launch Site
    html.Div([
        html.H3('Flight Number vs Launch Site', 
                style={'textAlign': 'center', 'color': '#503D36'}),
        dcc.Graph(id='flight-launch-site-chart')
    ])
])

# Add a callback function for `site-dropdown` as input, `success-pie-chart` as output
@app.callback(Output(component_id='success-pie-chart', component_property='figure'),
              Input(component_id='site-dropdown', component_property='value'))
def get_pie_chart(entered_site):
    if entered_site == 'ALL':
        # Total success launches across all sites
        # Count successful launches (class=1) by launch site
        success_counts = spacex_df[spacex_df['class'] == 1].groupby('Launch Site').size().reset_index(name='count')
        fig = px.pie(success_counts, 
                     values='count', 
                     names='Launch Site',
                     title='Total Successful Launches by Site')
        return fig
    else:
        # Filter data for selected launch site
        filtered_df = spacex_df[spacex_df['Launch Site'] == entered_site]
        
        # Count success (1) and failure (0) for the selected site
        success_count = len(filtered_df[filtered_df['class'] == 1])
        failure_count = len(filtered_df[filtered_df['class'] == 0])
        
        # Create data for pie chart
        outcome_data = {
            'Outcome': ['Success', 'Failure'],
            'Count': [success_count, failure_count]
        }
        
        fig = px.pie(outcome_data, 
                     values='Count', 
                     names='Outcome',
                     title=f'Success vs Failure for {entered_site}')
        return fig

# TASK 4: Add a callback function for `site-dropdown` and `payload-slider` as inputs, `success-payload-scatter-chart` as output
@app.callback(Output(component_id='success-payload-scatter-chart', component_property='figure'),
              [Input(component_id='site-dropdown', component_property='value'),
               Input(component_id='payload-slider', component_property='value')])
def get_scatter_chart(entered_site, payload_range):
    # Filter data based on payload range
    filtered_df = spacex_df[
        (spacex_df['Payload Mass (kg)'] >= payload_range[0]) & 
        (spacex_df['Payload Mass (kg)'] <= payload_range[1])
    ]
    
    if entered_site == 'ALL':
        # Use all sites within payload range
        fig = px.scatter(filtered_df, 
                         x='Payload Mass (kg)', 
                         y='class',
                         color='Booster Version Category',
                         title='Correlation between Payload and Success for All Sites',
                         labels={'class': 'Launch Outcome (0=Failure, 1=Success)'})
        return fig
    else:
        # Filter for specific launch site within payload range
        site_filtered_df = filtered_df[filtered_df['Launch Site'] == entered_site]
        fig = px.scatter(site_filtered_df, 
                         x='Payload Mass (kg)', 
                         y='class',
                         color='Booster Version Category',
                         title=f'Correlation between Payload and Success for {entered_site}',
                         labels={'class': 'Launch Outcome (0=Failure, 1=Success)'})
        return fig

# NEW: Add callback for categorical plot showing Flight Number vs Launch Site
@app.callback(Output(component_id='flight-launch-site-chart', component_property='figure'),
              Input(component_id='site-dropdown', component_property='value'))
def get_flight_launch_site_chart(entered_site):
    # Use the correct column names from the dataset
    flight_col = 'Flight Number'
    launch_site_col = 'Launch Site'
    class_col = 'class'
    
    # Check if columns exist, if not try variations
    if flight_col not in spacex_df.columns:
        possible_flight_cols = ['FlightNumber', 'flight_number', 'Flight_Number', 'flight']
        for col in possible_flight_cols:
            if col in spacex_df.columns:
                flight_col = col
                break
    
    if entered_site == 'ALL':
        # Show all sites
        df_to_plot = spacex_df.copy()
        title = 'Flight Number vs Launch Site (All Sites)'
    else:
        # Filter for specific site
        df_to_plot = spacex_df[spacex_df[launch_site_col] == entered_site].copy()
        title = f'Flight Number vs Launch Site ({entered_site})'
    
    if len(df_to_plot) == 0:
        return px.scatter(x=[0], y=['No Data'], title='No data available')
    
    # Create the categorical plot equivalent using Plotly
    # Convert class to string for better legend
    df_to_plot['Class_Label'] = df_to_plot[class_col].map({0: 'Failure', 1: 'Success'})
    
    fig = px.strip(df_to_plot, 
                   x=flight_col, 
                   y=launch_site_col,
                   color='Class_Label',
                   title=title,
                   labels={
                       flight_col: 'Flight Number',
                       launch_site_col: 'Launch Site',
                       'Class_Label': 'Mission Outcome'
                   },
                   color_discrete_map={'Success': 'orange', 'Failure': 'blue'})
    
    # Customize the layout to match seaborn catplot appearance
    fig.update_layout(
        xaxis_title_font_size=20,
        yaxis_title_font_size=20,
        width=1200,  # Equivalent to aspect=4
        height=400,
        showlegend=True
    )
    
    # Update marker size for better visibility
    fig.update_traces(marker=dict(size=8))
    
    return fig

# Run the app
if __name__ == '__main__':
    app.run(debug=True)