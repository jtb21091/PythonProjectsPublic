from flask import Flask, render_template, request
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)

# Load rates from an Excel file
rates_file = "rates.xlsx"
rates_data = pd.read_excel(rates_file)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    # Extract search parameters from the form
    origin_city = request.form.get('origin_city', '').lower()
    origin_state = request.form.get('origin_state', '').lower()
    destination_city = request.form.get('destination_city', '').lower()
    destination_state = request.form.get('destination_state', '').lower()
    carrier = request.form.get('carrier', '').lower()
    mode = request.form.get('mode', '').lower()

    # Filter the data
    filtered_data = rates_data[
        (rates_data['Origin City'].str.lower() == origin_city if origin_city else True) &
        (rates_data['Origin State'].str.lower() == origin_state if origin_state else True) &
        (rates_data['Destination City'].str.lower() == destination_city if destination_city else True) &
        (rates_data['Destination State'].str.lower() == destination_state if destination_state else True) &
        (rates_data['Carrier'].str.lower() == carrier if carrier else True) &
        (rates_data['Mode'].str.lower() == mode if mode else True)
    ]

    # Format expiration date
    results = filtered_data.to_dict(orient='records')
    for result in results:
        if 'Expiration' in result:
            try:
                original_date = datetime.strptime(result['Expiration'], "%Y-%m-%d")
                result['Expiration'] = original_date.strftime("%m-%d-%Y")
            except ValueError:
                result['Expiration'] = "Invalid Date"

    return render_template('index.html', results=results)

if __name__ == '__main__':
    PORT = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=PORT)
