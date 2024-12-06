import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import plotly.express as px

# Load the Excel file and specify the relevant columns
excel_file_path = 'ebay-all-orders-report-2024-11-18-11195110727.xlsx'
data_excel = pd.read_excel(excel_file_path, usecols=["Buyer State", "Total Price"])

# Convert 'Total Price' to numeric, ignoring errors
data_excel['Total Price'] = pd.to_numeric(data_excel['Total Price'], errors='coerce')

# Aggregate sales by state
total_sales_by_state = (
    data_excel.groupby('Buyer State', as_index=False)['Total Price']
    .sum()
    .rename(columns={'Buyer State': 'state', 'Total Price': 'total_sales'})
)

# Sort by total sales in descending order and reset index
total_sales_by_state = total_sales_by_state.sort_values(by='total_sales', ascending=False).reset_index(drop=True)

# Display the sorted table
print(total_sales_by_state)

# Bar Plot of Total Sales by State
plt.figure(figsize=(12, 8))
plt.bar(total_sales_by_state['state'], total_sales_by_state['total_sales'], color='skyblue')
plt.xticks(rotation=90)
plt.title("Total Sales by State (Descending Order)")
plt.xlabel("State")
plt.ylabel("Total Sales ($)")
plt.show()

# Load the U.S. state boundaries shapefile from Natural Earth
us_map = gpd.read_file("ne_110m_admin_1_states_provinces.shp")

# Filter to only include U.S. states (exclude territories)
us_states = us_map[us_map['iso_a2'] == 'US']

# Mapping state names to postal codes
state_abbreviations = {
    'Alabama': 'AL', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA', 'Colorado': 'CO',
    'Connecticut': 'CT', 'Delaware': 'DE', 'District of Columbia': 'DC', 'Florida': 'FL',
    'Georgia': 'GA', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
    'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD', 'Massachusetts': 'MA',
    'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT',
    'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM',
    'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK',
    'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
    'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT',
    'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY'
}
us_states['state'] = us_states['name'].map(state_abbreviations)

# Merge the sales data with the U.S. states map data
us_sales_map = us_states.merge(total_sales_by_state, on='state', how='left')

# Plotting the choropleth map
plt.figure(figsize=(15, 10))
us_sales_map.plot(column='total_sales', cmap='OrRd', linewidth=0.8, edgecolor='0.8', legend=True,
                  legend_kwds={'label': "Total Sales by State", 'orientation': "horizontal"},
                  missing_kwds={'color': 'lightgrey'})
plt.title('Total Sales by State in the U.S. (Choropleth Map)')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.show()

# Interactive choropleth map with Plotly
fig = px.choropleth(
    total_sales_by_state,
    locations='state',
    locationmode="USA-states",  # tells Plotly to look for state abbreviations
    color='total_sales',
    color_continuous_scale="OrRd",
    scope="usa",
    title="Total Sales by State in the U.S.",
    labels={'total_sales': 'Total Sales ($)'}
)

fig.update_layout(
    geo=dict(bgcolor='rgba(0,0,0,0)'),  # Transparent background
    title_font_size=24,
    title_x=0.5
)
fig.show()
