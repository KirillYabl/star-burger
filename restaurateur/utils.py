from geopy import distance
import requests


def fetch_coordinates(apikey, address):
    # https://dvmn.org/encyclopedia/api-docs/yandex-geocoder-api/
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


def fetch_coordinates_handled(apikey, address):
    """Handle fetch coordinates function to useful format"""
    try:
        coordinates = fetch_coordinates(apikey, address)
    except requests.exceptions.HTTPError:
        coordinates = None

    # coordinates is None and both cases: unknown address and HTTPError
    if coordinates is None:
        lon, lat = None, None
    else:
        lon, lat = coordinates
    return lat, lon


def get_distance(lat_lon_1, lat_lon_2):
    lat1, lon1 = lat_lon_1
    lat2, lon2 = lat_lon_2
    for coordinate in [lat1, lon1, lat2, lon2]:
        if coordinate is None:
            return 'неизвестно'
    return round(distance.distance(lat_lon_1, lat_lon_2).km, 1)


def sort_restaurants(restaurant_items):
    very_big_distance = 10 ** 9

    if not restaurant_items:
        return restaurant_items

    restaurant_items = sorted(
        restaurant_items,
        key=lambda x: x['distance'] if isinstance(x['distance'], float) else very_big_distance
    )
    for i, restaurant_item in enumerate(restaurant_items):
        if isinstance(restaurant_item['distance'], float):
            restaurant_items[i]['distance'] = f'{restaurant_item["distance"]} км'
    return restaurant_items
