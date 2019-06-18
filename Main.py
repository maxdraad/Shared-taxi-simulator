import itertools
from statistics import mean, stdev
import pandas as pd
import numpy as np
import csv
from random import shuffle

import math
from joblib import Parallel, delayed
import multiprocessing

from Globals import *
from Passenger import Passenger
from Taxi import Taxi


class Simulation:
    def __init__(self, sim_time=SIM_TIME, n_taxi=N_TAXI, n_passengers=N_PASSENGERS, capacities=MAX_PASSENGERS,
                 routes_centered=ROUTES_CENTERED, time_centered=TIME_CENTERED, price_indep=PRICE_INDEP,
                 dist_indep=DIST_INDEP, print_sim_time = PRINT_SIM_TIME, discount_multiplier = 0.1):
        self.n_passengers = n_passengers
        self.n_taxi = n_taxi
        self.capacities = capacities
        self.sim_time = sim_time
        self.print_sim_time = print_sim_time
        self.routes_centered = routes_centered
        self.time_centered = time_centered
        self.price_indep = price_indep
        self.dist_indep = dist_indep
        self.discount_multiplier = discount_multiplier
        self.taxis = self.init_taxis()
        self.passengers = self.init_passengers()
        self.delivered_passengers = []

    def init_passengers(self):
        passengers = []
        for x in range(self.n_passengers):
            passengers.append(Passenger(x, self))
        return passengers

    def init_taxis(self):
        taxis = []
        taxi_types = len(self.capacities)
        for capacity in self.capacities:
            for x in range(round(self.n_taxi / taxi_types)):
                taxis.append(Taxi(x, capacity))
        return taxis

    def run(self):
        mod = SIM_TIME / 100
        for time in range(SIM_TIME):
            if time % mod == 0 and self.print_sim_time:
                print("Current time: {}/{}".format(time, self.sim_time))
            self.iter(time)
        self.delivered_passengers_count()

    def iter(self, time):
        agents = self.passengers + self.taxis
        shuffle(agents)
        for agent in agents:
            agent.step(time)

    def iter_parralel(self, time):
        num_cores = multiprocessing.cpu_count()
        Parallel(n_jobs=num_cores)(delayed(agent.step)(time) for agent in self.passengers + self.taxis)

    def delivered_passengers_count(self):
        for passenger in self.passengers:
            if passenger.status == "Delivered":
                self.delivered_passengers.append(passenger)

    def print_results(self):
        print("Simulation finished (Capacities: {})".format(self.capacities))
        print("Agents delivered: {} / {}, distance driven: {}, earnings: {}".format(len(self.delivered_passengers),
            self.n_passengers, self.get_average_distance_driven(), self.get_total_earnings()))
        commuting_times = self.get_commuting_times()
        print("Commuting time: average: {}, max: {}, std: {}".format(mean(commuting_times),
                                                                       max(commuting_times),
                                                                       stdev(commuting_times)))
        print("Average taxi occupancy = {}".format(mean(self.get_taxi_occupancy())))

    def get_commuting_times(self):
        return [x + y for x, y in zip(self.get_waiting_times() , self.get_driving_times())]

    def get_waiting_times(self):
        commuting_times = []
        for agent in self.delivered_passengers:
            commuting_times.append(agent.waiting_time)
        return commuting_times

    def get_driving_times(self):
        commuting_times = []
        for agent in self.delivered_passengers:
            commuting_times.append(agent.driving_time)
        return commuting_times

    def get_average_distance_driven(self):
        return sum([taxi.distance_driven for taxi in self.taxis])/self.n_taxi

    def get_total_earnings(self):
        return sum([taxi.earnings for taxi in self.taxis])

    def get_taxi_occupancy(self):
        return [(taxi.occupancy_count / self.sim_time) for taxi in self.taxis]

    # Match results with csv
    def get_results(self):
        commuting_times = self.get_commuting_times()
        total_distance = self.get_average_distance_driven()
        total_earnings = self.get_total_earnings()
        total_taxi_occupancy = self.get_taxi_occupancy()
        return [len(self.delivered_passengers), mean(commuting_times), max(commuting_times),
                stdev(commuting_times), total_distance, total_earnings, mean(total_taxi_occupancy)]

def multi_sim(runs_per_setting = 5, sim_times=[SIM_TIME], n_taxis=[N_TAXI], n_passengers=[N_PASSENGERS],
              capacities=[MAX_PASSENGERS], time_centered = [False], routes_centered = [False]):
    combinations = list(itertools.product(sim_times, n_taxis, n_passengers, capacities, time_centered, routes_centered))
    for idx, setting in enumerate(combinations):
        results, means = [], []
        for run in range(runs_per_setting):
            print("Setting {}/{} ({}/{}), Combination: {}.".format(idx+1, len(combinations), run+1, runs_per_setting, setting))
            sim = Simulation(sim_time=setting[0], n_taxi=setting[1], n_passengers=setting[2], capacities=setting[3],
                             time_centered=setting[4], routes_centered=setting[5], print_sim_time=False)
            sim.run()
            result = sim.get_results()
            results.append(result)
            means.append(result[0])
        print("The first outcome var for this combination had the following means: {}".format(means))

        results = np.array(results)
        agg_results = np.average(results, axis=0)
        settings_results = list(setting) + agg_results.tolist()
        with open('results.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(settings_results)
        f.close()

# Single test run
# sim = Simulation(print_sim_time=True)
# sim.run()
# sim.print_results()

# Simple multi run for testing
# multi_sim(runs_per_setting=3, n_passengers=[50, 30],  n_taxis=[100, 80], capacities=[[1]])

# Policy 1: Reduce cars and allow sharing
multi_sim(runs_per_setting=3, n_taxis=[100, 80, 60, 40], capacities=[[1], [4], [1,2,4,8]])


# py -m kernprof -l Main.py
# py -m line_profiler Main.py.lprof