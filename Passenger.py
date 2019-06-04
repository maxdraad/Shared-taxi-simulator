import random
from random import randint
from Globals import *
from Taxi import Taxi

class Passenger:
    def __init__(self, id, simulation):
        self.id = id
        self.simulation = simulation
        self.orig = (randint(0, X_SIZE), randint(0, Y_SIZE))
        self.dest = (randint(0, X_SIZE), randint(0, Y_SIZE))
        self.request_time = randint(0, SIM_TIME - MAX_DISTANCE)
        self.ride = False
        self.status = "Idle"
        self.waiting_time = 0
        self.driving_time = 0
        self.time_out = 0
        self.power = random.uniform(0.7, 1.1)
        self.desired_travel_time = self.determine_travel_time()
        self.desired_price = self.determine_price()
        self.delay_toleration = 0
        self.delays = []

    def determine_travel_time(self):
        distance = Taxi.distance(self.orig, self.dest)
        return 10/self.power + distance*1.2/self.power

    def determine_price(self):
        return Taxi.distance(self.orig, self.dest) * 1.2 * self.power

    def step(self, time):
        if time == self.request_time:
            self.status = "Requesting"
            self.find_taxi()
            # print('Agent {} is requesting {}'.format(self.id, time))
        if self.status == "Requesting":
            # self.waiting_time += 1
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
            return False
        else:
            print("Passenger interaction not possible")
            return False

    def delay(self, time):
        self.delay_toleration -= time
        self.delays.append(time)

    def find_taxi(self):
        current_time = float('Inf')
        best_taxi, current_nodes, current_delays, current_price = None, None, None, float('inf')
        for taxi in self.simulation.taxis:
            expected_time, nodes, delays, price = taxi.find_best_route(self, current_time)
            if expected_time < current_time and expected_time < self.desired_travel_time and price < self.desired_price:
                current_time, best_taxi, current_nodes, current_delays, current_price = expected_time, taxi, nodes, delays, price
        if best_taxi:
            best_taxi.request(self, current_nodes, current_delays, current_price)
            self.delay_toleration = self.desired_travel_time - current_time
            self.status = "Matched"
            self.ride = best_taxi
        else:
            self.time_out = TIME_OUT_NO_MATCH