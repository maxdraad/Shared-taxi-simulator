import random
import numpy.random as npr
from random import randint
from Globals import *
from Taxi import Taxi


class Passenger:
    def __init__(self, id, simulation):
        self.id = id
        self.simulation = simulation
        # self.orig = (randint(0, X_SIZE), randint(0, Y_SIZE))
        # self.dest = (randint(0, X_SIZE), randint(0, Y_SIZE))
        self.orig, self.dest = self.generate_route()
        self.request_time = randint(0, SIM_TIME - MAX_DISTANCE)
        self.ride = False
        self.status = "Idle"
        self.waiting_time = 0
        self.driving_time = 0
        self.time_out = 0
        self.time_out_count = 0
        self.power = npr.normal(1, 0.05)
        self.desired_travel_time = self.determine_travel_time()
        self.desired_price = self.determine_price()
        self.delay_toleration = 0
        self.delays = []

    def generate_route(self):
        origin_center = random.choice([True, False])
        center = (round(npr.normal(X_SIZE/2, X_SIZE/25)), round(npr.normal(Y_SIZE/2, Y_SIZE/25)))
        rand = (randint(0, X_SIZE), randint(0, Y_SIZE))
        if origin_center:
            return center, rand
        else:
            return rand, center





    def determine_travel_time(self):
        distance = Taxi.distance(self.orig, self.dest)
        return (MAX_DISTANCE/2) / self.power + distance / self.power

    def determine_price(self):
        return Taxi.distance(self.orig, self.dest) * self.power

    def step(self, time):
        if time == self.request_time and self.time_out_count < TIME_OUT_LIMIT:
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
            return "In Taxi"
        elif self.status == "In Taxi":
            if self.dest != (taxi.x_pos, taxi.y_pos):
                print("Dropoff: Taxi wrong location")
            self.status = "Delivered"
            return "Delivered"
        else:
            print("Passenger interaction not possible")
            return False

    def delay(self, time):
        self.delay_toleration -= time
        self.delays.append(time)

    def find_taxi(self):
        best_taxi, current_nodes, current_delays, current_price, current_time = None, None, None, float('inf'), float('Inf')
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
            self.time_out_count += 1
