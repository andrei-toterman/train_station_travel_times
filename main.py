import math
from datetime import datetime, timedelta
import pickle

import folium
import googlemaps
import pandas as pd


def haversine(lat1, lon1, lat2, lon2):
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    return 6371.0 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def map_range(value, from_min, from_max, to_min, to_max):
    normalized_value = (value - from_min) / (from_max - from_min)
    return to_min + (normalized_value * (to_max - to_min))


def main():
    ri = folium.Icon(color='red')
    today = datetime.now()
    days_until_monday = (0 - today.weekday() + 7) % 7
    next_monday = today + timedelta(days=days_until_monday)
    departure_time = next_monday.replace(hour=8, minute=0, second=0, microsecond=0)

    f = open('times.pkl', 'rb')
    times_map = pickle.load(f)
    f.close()

    gmaps = googlemaps.Client(key='GOOGLE_CLOUD_MAPS_KEY')
    stations = pd.read_csv('stations.csv').itertuples()
    stations = [s for s in stations if s.country == 'NL']
    ams = next(s for s in stations if s.slug == 'amsterdam-centraal')
    stations.remove(ams)
    my_map = folium.Map(location=(ams.geo_lat, ams.geo_lng), zoom_start=9)
    folium.Marker(location=(ams.geo_lat, ams.geo_lng), tooltip=folium.Tooltip(ams.name_long), icon=ri).add_to(my_map)
    stations = [s for s in stations if haversine(ams.geo_lat, ams.geo_lng, s.geo_lat, s.geo_lng) < 45]

    for s in stations:
        if s.id not in times_map:
            print(f'api call for {s.name_long}')
            times_map[s.id] = gmaps.directions(
                (s.geo_lat, s.geo_lng),
                (ams.geo_lat, ams.geo_lng),
                mode='transit',
                departure_time=departure_time,
            )

        duration = times_map[s.id][0]['legs'][0]['duration']['value'] // 60
        folium.CircleMarker(
            location=(s.geo_lat, s.geo_lng),
            radius=10,
            stroke=False,
            fill_color=f'hsl({map_range(duration, 10, 80, 200, 360)} 100% 50%)',
            fill_opacity=0.9,
            tooltip=folium.Tooltip(f'{s.name_long}: {duration} mins'),
        ).add_to(my_map)

    f = open('times.pkl', 'wb')
    pickle.dump(times_map, f)
    f.close()
    my_map.save("map.html")


if __name__ == '__main__':
    main()
