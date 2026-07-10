import geojson
import pygame
import shapely.geometry as sg
from shapely.geometry import MultiPolygon
from shapely.ops import transform

with open('data/bhutan_districts.geojson', 'r') as file:
    data = geojson.load(file)

district_list = data['features']

shapely_districts = [sg.shape(district['geometry']) for district in district_list]
