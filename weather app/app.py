from flask import Flask, render_template, request, jsonify, session
import requests, sqlite3, geocoder
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"

API_KEY = "598e175bfcf945e581b192508253003"
DB_FILE = "favorites.db"

# Initialize database
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS favorites (id INTEGER PRIMARY KEY, city TEXT)")
        conn.commit()
init_db()

# Fetch weather data
def get_weather(city, days=5):
    url = f"https://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={city}&days={days}&aqi=yes&alerts=yes"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    weather, forecast, alerts, aqi, error = None, None, None, None, None
    city = ""
    
    if request.method == "POST":
        city = request.form.get("city").strip()
        if not "," in city:
            city += ", India"  # Default to India if country is missing
        
        data = get_weather(city)
        if data:
            weather = {
                "city": data["location"]["name"],
                "country": data["location"]["country"],
                "temperature": data["current"]["temp_c"],
                "description": data["current"]["condition"]["text"],
                "icon": data["current"]["condition"]["icon"],
                "humidity": data["current"]["humidity"],
                "wind": data["current"]["wind_kph"]
            }
            forecast = data["forecast"]["forecastday"]
            alerts = data.get("alerts", {}).get("alert", [])
            aqi = data["current"]["air_quality"]
        else:
            error = "Could not fetch weather data. Try again later."
    
    return render_template("index.html", weather=weather, forecast=forecast, alerts=alerts, aqi=aqi, error=error)

@app.route("/save_favorite", methods=["POST"])
def save_favorite():
    city = request.form.get("city")
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO favorites (city) VALUES (?)", (city,))
        conn.commit()
    return jsonify({"message": "City saved successfully!"})

@app.route("/favorites")
def get_favorites():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT city FROM favorites")
        cities = [row[0] for row in c.fetchall()]
    return jsonify(cities)

@app.route("/compare", methods=["POST"])
def compare_weather():
    cities = request.json.get("cities", [])
    weather_data = {}
    for city in cities:
        data = get_weather(city)
        if data:
            weather_data[city] = {
                "temperature": data["current"]["temp_c"],
                "humidity": data["current"]["humidity"],
                "wind": data["current"]["wind_kph"]
            }
    return jsonify(weather_data)

@app.route("/historical", methods=["POST"])
def historical_weather():
    city = request.form.get("city")
    date = request.form.get("date")  # YYYY-MM-DD
    url = f"https://api.weatherapi.com/v1/history.json?key={API_KEY}&q={city}&dt={date}"
    response = requests.get(url)
    data = response.json() if response.status_code == 200 else None
    return jsonify(data)

@app.route("/geolocation")
def geolocation():
    location = geocoder.ip("me").latlng
    return jsonify({"latitude": location[0], "longitude": location[1]})

if __name__ == "__main__":
    app.run(debug=True)