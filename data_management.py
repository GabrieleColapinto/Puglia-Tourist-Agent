from math import radians, cos, sin, sqrt, atan2
import pandas as pd


# Haversine formula for distance calculation
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in km
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2.0) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2.0) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance


# Function to generate Google Maps link
def generate_google_maps_link(lat, lon):
    return f"https://www.google.com/maps?q={lat},{lon}"


def get_resorts():
    resorts = pd.read_csv('data/stabilimenti_balneari.csv')
    resorts = resorts[resorts['latitudine'].notnull() & resorts['longitudine'].notnull()]
    resorts = resorts[['denominazione', 'latitudine', 'longitudine']]
    return resorts


def get_restaurants():
    df = pd.read_csv('data/servizi_turismo.csv')
    df = df[df['latitudine'].notnull() & df['longitudine'].notnull()]
    restaurants = df[df['tipologia'].str.contains('Ristorazione', regex=True, case=False, na=False)]
    restaurants = restaurants[['denominazione', 'latitudine', 'longitudine']]
    return restaurants
