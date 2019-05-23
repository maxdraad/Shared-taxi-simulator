import random
from random import randint
import Permute
from statistics import mean, stdev
from joblib import Parallel, delayed
import multiprocessing

taxis = []
passengers = []
delivered_passengers = []

SIM_TIME = 1000

X_SIZE = 100
Y_SIZE = 100
TAXI_CAP = 4
NODES_LIMIT = 5
N_PASSENGERS = 1000
N_TAXI = 100
SHARING = False
DELAY_TOLERATION = 100
TIME_OUT_NO_MATCH = 1000

DEBUG_ID = 505
DEBUG_COUNT = 0


class Passenger:
    def __init__(self, id):
        self.id = id
        self.orig = (randint(0, X_SIZE), randint(0, Y_SIZE))
        self.dest = (randint(0, X_SIZE), randint(0, Y_SIZE))
        self.request_time = randint(0, SIM_TIME)
        self.ride = False
        self.status = "Idle"
        self.waiting_time = 0
        self.driving_time = 0
        self.time_out = 0
        self.power = random.uniform(0.8, 1.2)
        self.desired_travel_time = self.determine_travel_time()
        self.desired_price = self.determine_price()
        self.delay_toleration = 0

    def determine_travel_time(self):
        distance = Taxi.distance(self.orig, self.dest)
        return 20/self.power + distance*1.5/self.power

    def determine_price(self):
        return Taxi.distance(self.orig, self.dest) * self.power

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
            self.ride.occupance()

    def interact(self, taxi):
        if self.status == "Matched":
            if self.orig != (taxi.x_pos, taxi.y_pos):
                print("Pickup: Taxi wrong location")
            self.status = "In Taxi"
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
        if (self.delay_toleration < 0):
            print("Exceeding delay toleration!")


    def find_taxi(self):
        current_time = float('Inf')
        best_taxi, current_nodes, current_delays, current_price = None, None, None, float('inf')
        for taxi in taxis:
            expected_time, nodes, delays, price = taxi.expected_length_price(self, current_time)
            if expected_time < current_time and expected_time < self.desired_travel_time and price < self.desired_price:
                current_time, best_taxi, current_nodes, current_delays, current_price = expected_time, taxi, nodes, delays, price
        if best_taxi:
            best_taxi.request(self, current_nodes, current_delays, current_price)
            self.delay_toleration = self.desired_travel_time - current_time
            self.status = "Matched"
            self.ride = best_taxi
        else:
            self.time_out = TIME_OUT_NO_MATCH


class Taxi:
    def __init__(self, id):
        self.id = id
        self.price_per_unit = 1
        self.shared = SHARING
        self.capacity = TAXI_CAP
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

    def request(self, passenger, nodes, delays, price):
        self.pickups.append(passenger)
        self.nodes = nodes
        if delays:
            self.apply_delays(delays)
        self.earnings += price

    def apply_delays(self, delays):
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
    def expected_length_price(self, passenger, current_cost):
        direct_distance = self.total_distance([(self.x_pos, self.y_pos), passenger.orig, passenger.dest])
        trip_distance = self.distance(passenger.orig, passenger.dest)
        price = self.compute_price(trip_distance)
        new_nodes = [(passenger, passenger.orig), (passenger, passenger.dest)]
        if len(self.nodes) == 0:
            return direct_distance, new_nodes, None, price
        elif len(self.nodes) <= 2 and not self.shared:
            route_after_passenger = self.total_distance([(self.x_pos, self.y_pos)] + self.get_nodes_coordinates() +
                                                        [passenger.orig, passenger.dest])
            return route_after_passenger, (self.nodes + new_nodes), None, price
        elif len(self.nodes) <= NODES_LIMIT and (direct_distance < current_cost) and self.shared:
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

    def get_nodes_coordinates(self, nodes=[]):
        if nodes:
            return [x[1] for x in nodes]
        else:
            return [x[1] for x in self.nodes]

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
            route_to_destination = [(self.get_position())] + self.get_nodes_coordinates(new_route)[:destination_index]
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

                current_time = self.total_distance([(self.get_position())] + self.get_nodes_coordinates(current_nodes[:idx_current+1]))
                new_time = self.total_distance([(self.get_position())] + self.get_nodes_coordinates(new_nodes[:idx_new+1]))
                passenger_delay = new_time - current_time

                # print("entry")
                # print(self.get_position())
                # print(node)
                # print(current_nodes)
                # print(current_time)
                # print(new_nodes)
                # print(new_time)
                # print(passenger_delay)

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
        print("Simulation finished (Sharing: {})".format(SHARING))
        commuting_times = []
        for agent in delivered_passengers:
            commuting_times.append(agent.driving_time)
            print("Passenger desired time: {}, actual waiting + driving time {}".format(agent.desired_travel_time, agent.driving_time+agent.waiting_time))
        total_distance_driven = sum([taxi.distance_driven for taxi in taxis])
        earnings = sum([taxi.earnings for taxi in taxis])
        print("Agents delivered: {} / {}, distance driven: {}, earnings: {}".format(len(delivered_passengers),
                                                                                    N_PASSENGERS, total_distance_driven,
                                                                                    earnings))
        print("Driving time: average: {}, max: {}, std: {}".format(mean(commuting_times),
                                                                       max(commuting_times),
                                                                       stdev(commuting_times)))
        average_taxi_occupance = [(taxi.occupance_count/SIM_TIME) for taxi in taxis]
        print("Average taxi occupance = {}".format(mean(average_taxi_occupance)))


        print("Debug count: " + str(DEBUG_COUNT))

    def iter(self, time):
        for agent in passengers + taxis:
            agent.step(time)

    def iter_parralel(self, time):
        num_cores = multiprocessing.cpu_count()
        Parallel(n_jobs=num_cores)(delayed(agent.step)(time) for agent in passengers+taxis)



    def run(self):
        mod = SIM_TIME / 100
        for time in range(SIM_TIME):
            if time % mod == 0:
                print("Current time: {}/{}".format(time, SIM_TIME))
            self.iter(time)
            # if type(agent) == Passenger and agent.id == DEBUG_ID:
            #     print( 'Current time: {} Agent {} will request on time {} pos {} at {}, waiting time = {}'.format(
            #         time, agent.id, agent.request_time, agent.status, agent.orig, (agent.waiting_time+agent.driving_time)))
        self.end_statements()


sim = Simulation()
sim.run()

# print(Taxi.distance((1,1), (3,-3)))



# py -m kernprof -l Main.py
# py -m line_profiler Main.py.lprof