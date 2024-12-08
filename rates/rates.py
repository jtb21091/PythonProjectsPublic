from flask import Flask, render_template, request
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)

# Load rates from an Excel file. Ensure the file exists.
rates_file = "/Users/joshuabrooks/Desktop/PythonProjectsPublic/rates/rates.xlsx"
if not os.path.exists(rates_file):
    raise FileNotFoundError(f"Rates file not found: {rates_file}")

rates_data = pd.read_excel(rates_file)

@app.route('/')
def index():
    return render_template('index.html', results=[])

@app.route('/search', methods=['POST'])
def search():
    # Extract search parameters from the form
    origin_city = request.form.get('origin_city', '').strip().lower()
    origin_state = request.form.get('origin_state', '').strip().lower()
    destination_city = request.form.get('destination_city', '').strip().lower()
    destination_state = request.form.get('destination_state', '').strip().lower()
    carrier = request.form.get('carrier', '').strip().lower()
    mode = request.form.get('mode', '').strip().lower()

    # Filter the data
    filtered_data = rates_data[
        (rates_data['Origin City'].str.lower().str.strip() == origin_city if origin_city else True) &
        (rates_data['Origin State'].str.lower().str.strip() == origin_state if origin_state else True) &
        (rates_data['Destination City'].str.lower().str.strip() == destination_city if destination_city else True) &
        (rates_data['Destination State'].str.lower().str.strip() == destination_state if destination_state else True) &
        (rates_data['Carrier'].str.lower().str.strip() == carrier if carrier else True) &
        (rates_data['Mode'].str.lower().str.strip() == mode if mode else True)
    ]

    # Format expiration date
    results = filtered_data.to_dict(orient='records')
    for result in results:
        if 'Expiration' in result and pd.notnull(result['Expiration']):
            try:
                result['Expiration'] = pd.to_datetime(result['Expiration']).strftime("%m-%d-%Y")
            except ValueError:
                result['Expiration'] = "Invalid Date"

    return render_template('index.html', results=results)

if __name__ == '__main__':
    PORT = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=PORT)
