import random
import numpy.random as npr
from random import randint
from Globals import *
from Taxi import Taxi


class Passenger:
    def __init__(self, id, simulation):
        self.id = id
        self.simulation = simulation
        self.orig, self.dest = self.generate_route()
        self.request_time = self.generate_time()
        self.ride = False
        self.ride_price = None
        self.status = "Idle"
        self.waiting_time = 0
        self.driving_time = 0
        self.time_out = 0
        self.time_outs_count = 0
        self.power = npr.normal(1, 0.05)
        self.desired_travel_time = self.determine_travel_time()
        self.desired_price = self.determine_price()
        self.delay_toleration = 0
        self.delays = []

    def step(self, time):
        if time == self.request_time:
            self.status = "Requesting"
            self.find_taxi()
        elif self.status == "Requesting" and self.time_outs_count < MAX_TIME_OUTS:
            if self.time_out == 0:
                self.find_taxi()
            else:
                self.time_out -= 1
        elif self.status == "Matched":
            self.waiting_time += 1
        elif self.status == "In Taxi":
            self.driving_time += 1
            self.ride.occupancy()

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
            self.ride_price = current_price
        else:
            self.time_out = TIME_OUT
            self.time_outs_count += 1

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

    def determine_travel_time(self):
        if self.simulation.dist_indep:
            return float('inf')
        else:
            distance = Taxi.distance(self.orig, self.dest)
            return ((MAX_DISTANCE * 0.1) + (1.2 * distance)) / self.power

    def determine_price(self):
        if self.simulation.price_indep:
            return float('inf')
        else:
            return Taxi.distance(self.orig, self.dest) * self.power

    def generate_time(self):
        if self.simulation.time_centered:
            mean = (SIM_TIME - MAX_DISTANCE)/2
            return round(npr.normal(mean, mean/4))
        else:
            return randint(0, SIM_TIME - MAX_DISTANCE)

    def generate_route(self):
        if self.simulation.routes_centered:
            center_x, center_y = X_SIZE/2, Y_SIZE/2
            centered_loc = (round(npr.normal(center_x, center_x/4)), round(npr.normal(center_y, center_y/4)))
            uniform_loc = (randint(0, X_SIZE), randint(0, Y_SIZE))
            if random.choice([True, False]):
                return centered_loc, uniform_loc
            else:
                return uniform_loc, centered_loc
        else:
            return (randint(0, X_SIZE), randint(0, Y_SIZE)), (randint(0, X_SIZE), randint(0, Y_SIZE))



