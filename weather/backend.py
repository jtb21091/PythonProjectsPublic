from flask import Flask, send_from_directory, request, jsonify
from geopy.distance import geodesic
import requests

app = Flask(__name__)

# Sample ski resort data
ski_resorts = [
    {"name": "Seven Springs", "latitude": 40.0221, "longitude": -79.2896, "website": "https://www.7springs.com"},
    {"name": "Hidden Valley", "latitude": 40.0545, "longitude": -79.2513, "website": "https://www.hiddenvalleyresort.com"},
    {"name": "Laurel Mountain", "latitude": 40.1742, "longitude": -79.1647, "website": "https://www.laurelmountainski.com"},
]

def fetch_weather(lat, lon):
    api_key = "YOUR API KEY"  # Replace with your OpenWeatherMap API key
    base_url = "http://api.openweathermap.org/data/2.5/onecall"

    params = {
        "lat": lat,
        "lon": lon,
        "exclude": "minutely,hourly,alerts",
        "units": "imperial",
        "appid": api_key,
    }

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        current_weather = f"{data['current']['weather'][0]['description'].capitalize()}, {data['current']['temp']}°F"
        forecast = [
            f"{day['temp']['day']}°F {day['weather'][0]['main']}"
            for day in data["daily"][:5]
        ]
        return {"current": current_weather, "forecast": forecast}
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return {"current": "N/A", "forecast": ["N/A"] * 5}

@app.route("/")
def index():
    return send_from_directory(".", "frontend.html")

@app.route("/weather", methods=["POST"])
def get_weather():
    user_location = request.json.get("location")
    user_coords = (user_location["latitude"], user_location["longitude"])

    resorts_with_weather = []
    for resort in ski_resorts:
        resort_coords = (resort["latitude"], resort["longitude"])
        distance = geodesic(user_coords, resort_coords).miles
        weather = fetch_weather(resort["latitude"], resort["longitude"])
        resorts_with_weather.append({
            "name": resort["name"],
            "website": resort["website"],
            "current_weather": weather["current"],
            "forecast": weather["forecast"],
            "distance": round(distance, 2),
        })

    resorts_with_weather.sort(key=lambda x: x["distance"])
    return jsonify(resorts_with_weather)

if __name__ == "__main__":
    app.run(debug=True)
