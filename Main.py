from random import randint
import itertools
import Permute
from statistics import mean, stdev

taxis = []
passengers = []
delivered_passengers = []

SIM_TIME = 1000

X_SIZE = 100
Y_SIZE = 100
TAXI_CAP = 4
NODES_LIMIT = 5
N_PASSENGERS = 300
N_TAXI = 20
SHARING = False
ACCEPTABLE_TRIP_LENGTH = 300
DELAY_TOLERATION = 100
TIME_OUT_NO_MATCH = 20

DEBUG_ID = 505
DEBUG_COUNT = 0


class Passenger:
    def __init__(self, id):
        self.id = id
        self.orig = (randint(0, X_SIZE), randint(0, Y_SIZE))
        self.dest = (randint(0, X_SIZE), randint(0, Y_SIZE))
        self.request_time = randint(0, SIM_TIME)
        self.ride = None
        self.status = "Idle"
        self.waiting_time = 0
        self.driving_time = 0
        self.goal = None
        self.time_out = 0
        self.delay_toleration = self.determine_delay()

    def determine_delay(self):
        distance = Taxi.distance(self.orig, self.dest)
        return 20 + distance*1.5

    def step(self, time):
        if time == self.request_time:
            self.status = "Requesting"
            self.find_taxi()
            # print('Agent {} is requesting {}'.format(self.id, time))
        if self.status == "Requesting":
            self.waiting_time += 1
            if self.time_out == 0:
                self.find_taxi()
            else:
                self.time_out -= 1
        elif self.status == "Matched":
            self.waiting_time += 1
        elif self.status == "In Taxi":
            self.driving_time += 1

    def interact(self, taxi):
        if self.status == "Matched":
            if self.orig != (taxi.x_pos, taxi.y_pos):
                print("Pickup: Taxi wrong location")
            self.status = "In Taxi"
            self.goal = self.dest
            return True
        elif self.status == "In Taxi":
            if self.dest != (taxi.x_pos, taxi.y_pos):
                print("Dropoff: Taxi wrong location")
            self.status = "Delivered"
            delivered_passengers.append(self)
            return False
        else:
            print("Passenger interaction not possible")
            return False

    def delay(self, time):
        self.delay_toleration -= time


    def find_taxi(self):
        current_time = float('Inf')
        best_taxi, current_nodes, delays = None, None, None
        for taxi in taxis:
            expected_time, nodes, delays = taxi.expected_time(self, current_time)
            if expected_time < current_time and expected_time < ACCEPTABLE_TRIP_LENGTH:
                current_time, best_taxi, current_nodes = expected_time, taxi, nodes
        if best_taxi:
            best_taxi.request(self, current_nodes, delays)
            self.status = "Matched"
            self.delay_toleration = self.delay_toleration - current_time
        else:
            self.time_out = TIME_OUT_NO_MATCH


class Taxi:
    def __init__(self, id):
        self.id = id
        self.capacity = TAXI_CAP
        self.sharing = SHARING
        self.x_pos = randint(0, X_SIZE)
        self.y_pos = randint(0, Y_SIZE)
        self.status = "Idle"
        self.pairs = []

        self.nodes = []
        self.dest = None

    def step(self, _):
        if self.nodes:
            # if self.id == 1:
            #     print("Taxi 1 pos: [{}, {}]. Nodes: {}".format(self.x_pos, self.y_pos, self.nodes))
            self.drive()

    def request(self, passenger, nodes, delays):
        self.pairs.append(passenger)
        self.nodes = nodes
        if delays:
            self.apply_delays(delays)

    def apply_delays(self, delays):
        for passenger in delays:
            passenger[0].delay(passenger[1])

    def drive(self):
        if (self.x_pos, self.y_pos) == self.nodes[0][1]:
            pickup = self.nodes[0][0].interact(self)
            if pickup:
                self.pairs.remove(self.nodes[0][0])
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

    # Returns expected time and path
    def expected_time(self, passenger, current_cost):
        direct_distance = self.total_distance([(self.x_pos, self.y_pos), passenger.orig, passenger.dest])
        new_nodes = [(passenger, passenger.orig), (passenger, passenger.dest)]
        if len(self.nodes) == 0:
            return direct_distance, new_nodes, None
        elif len(self.nodes) <= 2 and not SHARING:
            route_after_passenger = self.total_distance(self.get_nodes_coordinates() + [(self.x_pos, self.y_pos)])
            return route_after_passenger, (self.nodes + new_nodes), None
        elif len(self.nodes) <= NODES_LIMIT and (direct_distance < current_cost) and SHARING:
            shortest_path = self.shortest_path(self.nodes, new_nodes)
            return shortest_path
        else:
            return float('inf'), None, None

    def get_pairs(self):
        pairs = []
        for passenger in self.pairs:
            pairs.append([(passenger, passenger.orig), (passenger, passenger.dest)])
        return pairs

    def get_nodes_coordinates(self, nodes=[]):
        if nodes:
            return [x[1] for x in nodes]
        else:
            return [x[1] for x in self.nodes]

    # Constraint by tolerable delay of agents
    def shortest_path(self, current_nodes, new_nodes):
        current_route, current_distance = None, float('inf')
        pairs = self.get_pairs()
        pairs.append(new_nodes)
        delay = None
        for new_route in Permute.permutations(current_nodes + new_nodes, pairs):
            destination_index = new_route.index(new_nodes[1])
            distance = self.total_distance(self.get_nodes_coordinates(new_route)[:destination_index])
            # distance = self.total_distance(self.get_nodes_coordinates(new_route)) #Old and incorrect version, better results
            delay = self.delay(current_nodes, new_route)
            # print(delay)
            if distance < current_distance and delay:
                current_distance = distance
                current_route = new_route
        return current_distance, current_route, delay

    def delay(self, current_nodes, new_nodes):
        delays = []
        for idx_current, node in enumerate(current_nodes):
            if node[1] == node[0].dest:
                idx_new = new_nodes.index(node)
                passenger_delay = (self.total_distance(self.get_nodes_coordinates(new_nodes[:idx_new])) -
                self.total_distance(self.get_nodes_coordinates(current_nodes[:idx_current])))
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

    @staticmethod
    def last_index(nodes, passenger):
        return len(nodes) - 1 - nodes[::-1].index((passenger, passenger.dest))

    @staticmethod
    def distance(point1, point2):
        return abs(point1[0] - point2[0]) + abs(point1[1] - point2[1])

    @staticmethod
    def between(point1, point2, point3):
        return point1[0] < point3[0] < point2[0] and point1[1] < point3[1] < point2[1]


class Simulation:
    def __init__(self):
        self.init_passengers()
        self.init_taxis()

    def init_passengers(self):
        for x in range(N_PASSENGERS):
            passengers.append(Passenger(x))

    def init_taxis(self):
        for x in range(N_TAXI):
            taxis.append(Taxi(x))

    def end_statements(self):
        print("Simulation finished")
        commuting_times = []
        for agent in delivered_passengers:
            commuting_times.append(agent.waiting_time + agent.driving_time)
        print("Agents delivered: {} / {}".format(len(delivered_passengers), N_PASSENGERS))
        print("Travel time: average: {}, max: {}, std: {}".format(mean(commuting_times),
                                                                       max(commuting_times),
                                                                       stdev(commuting_times)))

        print("Debug count: " + str(DEBUG_COUNT))

    def iter(self, time):
        for agent in passengers + taxis:
            agent.step(time)

    def run(self):
        for time in range(SIM_TIME):
            if time % 100 == 0:
                print("Current time: " + str(time))
            self.iter(time)
            # if type(agent) == Passenger and agent.id == DEBUG_ID:
            #     print( 'Current time: {} Agent {} will request on time {} pos {} at {}, waiting time = {}'.format(
            #         time, agent.id, agent.request_time, agent.status, agent.orig, (agent.waiting_time+agent.driving_time)))
        self.end_statements()


sim = Simulation()
sim.run()
# print(Permute.permutations([1,2,3,4,5],[[1,2,3],[4,5]]))
