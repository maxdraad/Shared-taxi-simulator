import random
from random import randint
import Permute
from Globals import *

class Taxi:
    def __init__(self, id, shared):
        self.id = id
        self.price_per_unit = random.uniform(0.8, 1.2)
        self.shared = shared
        self.nodes_limit = NODES_LIMIT
        self.x_pos = randint(0, X_SIZE)
        self.y_pos = randint(0, Y_SIZE)
        self.status = "Idle"
        self.occupance_count = 0
        self.distance_driven = 0
        self.pickups = []
        self.deliveries = []
        self.nodes = []
        self.dest = None
        self.earnings = 0


    def step(self, time):
        if time > SIM_TIME * 0.1:
            self.compute_price_per_unit(time)
        if self.nodes:
            # if self.id == 1:
            #     print("Taxi 1 pos: [{}, {}]. Nodes: {}".format(self.x_pos, self.y_pos, self.nodes))
            self.drive()
        else:
            self.move((randint(0, X_SIZE), randint(0, Y_SIZE)))

    def request(self, passenger, nodes, delays, price):
        self.pickups.append(passenger)
        self.nodes = nodes
        if delays:
            self.apply_delays(delays)
        self.earnings += price

    @staticmethod
    def apply_delays(delays):
        for passenger in delays:
            passenger[0].delay(passenger[1])

    def drive(self):
        if (self.x_pos, self.y_pos) == self.nodes[0][1]:
            pickup = self.nodes[0][0].interact(self)
            if pickup:
                self.pickups.remove(self.nodes[0][0])
            del self.nodes[0]
        else:
            self.move(self.nodes[0][1])

    def move(self, des):
        if abs(self.x_pos == des[0]):
            if abs(self.y_pos != des[1]):
                if self.y_pos < des[1]:
                    self.y_pos += 1
                else:
                    self.y_pos -= 1
        else:
            if self.x_pos < des[0]:
                self.x_pos += 1
            else:
                self.x_pos -= 1
        self.distance_driven += 1

    # Returns expected time and path
    def find_best_route(self, passenger, current_cost):
        direct_distance = self.total_distance([(self.x_pos, self.y_pos)] + self.get_nodes_coordinates(self.nodes) +
                                              [passenger.orig, passenger.dest])
        trip_distance = self.distance(passenger.orig, passenger.dest)
        price = self.compute_price(trip_distance)
        new_nodes = [(passenger, passenger.orig), (passenger, passenger.dest)]
        if not self.nodes:
            return direct_distance, new_nodes, None, price
        if not self.shared and len(self.nodes) <= 2:
            return direct_distance, (self.nodes + new_nodes), None, price
        elif self.shared and len(self.nodes) <= self.nodes_limit and (direct_distance < current_cost):
            shortest_path = self.shortest_path(self.nodes, new_nodes, current_cost)
            return (*shortest_path, price)
        else:
            return float('inf'), None, None, float('inf')

    def compute_price(self, distance):
        return distance * self.price_per_unit

    def compute_price_per_unit(self, time):
        average_occupance = (self.occupance_count/time)
        if average_occupance > 1:
            self.price_per_unit = (1 / average_occupance)

    def get_pairs(self):
        pairs = []
        for passenger in self.pickups:
            pairs.append([(passenger, passenger.orig), (passenger, passenger.dest)])
        return pairs

    def get_position(self):
        return self.x_pos, self.y_pos

    # Constraint by tolerable delay of agents
    # @profile
    def shortest_path(self, current_nodes, new_nodes, current_distance):
        current_route, current_delay = None, None
        pairs = self.get_pairs()
        pairs.append(new_nodes)
        for new_route in Permute.permutations(current_nodes + new_nodes, pairs):
            destination_index = new_route.index(new_nodes[1])
            route_to_destination = [(self.get_position())] + self.get_nodes_coordinates(new_route)[:destination_index + 1]
            distance = self.total_distance(route_to_destination)
            if distance < current_distance:
                delay = self.compute_delays(current_nodes, new_route)
                if delay:
                    current_distance, current_route, current_delay = distance, new_route, delay
        return current_distance, current_route, current_delay

    # @profile
    def compute_delays(self, current_nodes, new_nodes):
        delays = []
        for idx_current, node in enumerate(current_nodes):
            if node[1] == node[0].dest:
                idx_new = new_nodes.index(node)
                current_time = self.total_distance([(self.get_position())] +
                                                   self.get_nodes_coordinates(current_nodes[:idx_current+1]))
                new_time = self.total_distance([(self.get_position())] +
                                               self.get_nodes_coordinates(new_nodes[:idx_new+1]))
                passenger_delay = new_time - current_time
                if passenger_delay > node[0].delay_toleration:
                    return False
                else:
                    delays.append((node[0], passenger_delay))
        return delays


    # As tuples
    def total_distance(self, points):
        total = 0
        for x in range(len(points) - 1):
            total += self.distance(points[x], points[x + 1])
        return total

    def occupance(self):
        self.occupance_count += 1

    @staticmethod
    def get_nodes_coordinates(nodes):
        return [x[1] for x in nodes]

    @staticmethod
    def last_index(nodes, passenger):
        return len(nodes) - 1 - nodes[::-1].index((passenger, passenger.dest))

    @staticmethod
    def distance(point1, point2):
        return abs(point1[0] - point2[0]) + abs(point1[1] - point2[1])

    @staticmethod
    def between(point1, point2, point3):
        return point1[0] < point3[0] < point2[0] and point1[1] < point3[1] < point2[1]

