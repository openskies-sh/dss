# A file to generate Flight Records from KML.
import json
import math
import s2sphere
from shapely.geometry import LineString, Point
from monitoring.rid_qualifier.utils import QueryBoundingBox, FlightPoint, GridCellFlight, FlightDetails, FullFlightRecord
from monitoring.monitorlib.rid import RIDHeight, RIDAircraftState, RIDAircraftPosition, RIDFlightDetails
from monitoring.rid_qualifier import operator_flight_details_generator as details_generator
from monitoring.monitorlib.geo import flatten, unflatten
from monitoring.rid_qualifier.test_data.test_input_coordinates import input_coordinates

def get_flight_details():
    # TODO: To be fetched from KML.
    pass


def get_flight_coordinates():
    # TODO: To be fetched from KML.
    # Hardcoded for now.
    # Reverse the Lng,Lat from KML to Lat,Lng for processing.
    return [(p[1], p[0], p[2]) for p in input_coordinates]


def get_distance_travelled():
    # TODO: should be calculated based on speed m/s, hardcoding to 2m/s for now.
    return 2


def get_distance_between_two_points(flatten_point1, flatten_point2):
    x1, y1 = flatten_point1
    x2, y2 = flatten_point2
    return ((((x2 - x1 )**2) + ((y2-y1)**2) )**0.5)


def check_if_vertex_is_correct(point1, point2, point3, flight_distance):
    x1, y1 = point1
    x2, y2 = point2
    x3, y3 = point3
    points_distance_difference = math.sqrt(
        (x2-x1)*(x2-x1) + (y2-y1)*(y2-y1)) - math.sqrt((x2-x3)*(x2-x3) + (y2-y3)*(y2-y3))
    assert abs(
        points_distance_difference - flight_distance
        ) < 0.2, f'Generated vertex is not correct. {point1}, {point2}, {point3}, {flight_distance}'


def test_distance_bw_two_points(last_flight_state, state_vertex):
    distance_bw_last_two_states = get_distance_between_two_points(last_flight_state, state_vertex)
    assert distance_bw_last_two_states < 1.9, f'Points are not equally positioned.{last_flight_state}, {state_vertex}'


def get_flight_state_vertices(flatten_points):
    """Get flight state vertices at flight distance's m/s interval.
    Args:
        flatten_points: A list of x,y coordinates on flattening KML's Lat,Lng points.
    Returns:
        A list of vertices found at every interval of flight state.
    """
    points = iter(flatten_points)
    point1 = next(points)
    point2 = next(points)
    flight_distance = get_distance_travelled()
    flight_state_vertices = []
    while True:
        input_coord_gap = get_distance_between_two_points(point1, point2)
        if input_coord_gap <= 0:
            # points are overlapping
            point1 = point2
            point2 = next(points, None)
            if not point2:
                break
            continue
        if input_coord_gap == flight_distance:
            flight_state_vertices.append(point2)
            point1 = point2
            point2 = next(points, None)
            if not point2:
                break
        if flight_distance < input_coord_gap:
            remaining_flight_distance = input_coord_gap
            while remaining_flight_distance > flight_distance:
                state_vertex = get_vertex_between_points(point1, point2, flight_distance)
                if state_vertex:
                    state_vertex = state_vertex.coords[:][0]
                    # TODO: move it to unit tests.
                    check_if_vertex_is_correct(point1, point2, state_vertex, flight_distance)
                    flight_state_vertices.append(state_vertex)
                    point1 = state_vertex
                    remaining_flight_distance -= flight_distance
            if remaining_flight_distance > 0:
                input_coord_gap = remaining_flight_distance
        if flight_distance > input_coord_gap:
            remaining_flight_distance = flight_distance - input_coord_gap
            point1 = point2
            point2 = next(points, None)
            if not point2:
                flight_state_vertices.append(point1)
                break
            state_vertex = get_vertex_between_points(point1, point2, remaining_flight_distance)
            if state_vertex:
                state_vertex = state_vertex.coords[:][0]
                flight_state_vertices.append(state_vertex)
                if state_vertex == point2:  # This is the special case when remaining_distance is very close to flight_distance
                    point2 = next(points, None)
                    if not point2:
                        flight_state_vertices.append(point1)
                        break
                point1 = state_vertex
        
    return flight_state_vertices


def get_vertex_between_points(point1, point2, at_distance):
    """Returns vertex between point1 and point2 at a distance from point1.
    Args:
        point1: First vertex having tuple (x,y) co-ordinates.
        point2: Second vertex having tuple (x,y) co-ordinates.
        at_distance: A distance at which to locate the vertex on the line joining point1 and point2.
    Returns:
        A Point object.
    """
    line = LineString([point1, point2])
    new_point = line.interpolate(at_distance)
    return new_point


def main():
    coordinates = get_flight_coordinates()
    reference_point = coordinates[0] # TODO: Check `if coordinates:`.
    alt = reference_point[2] # TODO: Get alt from coordinates.
    alt = 140
    flatten_points = []
    for point in coordinates:
        flatten_points.append(flatten(
            s2sphere.LatLng.from_degrees(*reference_point[:2]),
            s2sphere.LatLng.from_degrees(*point[:2])
        ))
    
    flight_state_vertices = get_flight_state_vertices(flatten_points)
    flight_state_vertices_unflatten = [unflatten(s2sphere.LatLng.from_degrees(*reference_point[:2]), v) for v in flight_state_vertices]

    # TODO: Fetch Lat,Lng values from s2sphere.LatLng object without converting it to string.
    # Position Lat, Lng to Lng, Lat order for KML representation.
    flight_state_vertices_unflatten = [(str(p.lng().degrees), str(p.lat().degrees), str(alt)) for p in flight_state_vertices_unflatten]
    flight_state_vertices_unflatten = [','.join(p) for p in flight_state_vertices_unflatten]
    flight_state_vertices_str = '\n'.join(flight_state_vertices_unflatten)
    with open("monitoring/rid_qualifier/test_data/flight_state_coordinates.txt", "w") as text_file:
        text_file.write(flight_state_vertices_str)


if __name__ == '__main__':
    main()
