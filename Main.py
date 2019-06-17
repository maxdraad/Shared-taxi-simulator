import itertools
from statistics import mean, stdev
import pandas as pd
import numpy as np
import csv

import math
from joblib import Parallel, delayed
import multiprocessing

from Globals import *
from Passenger import Passenger
from Taxi import Taxi

class Simulation:
    def __init__(self, sim_time=SIM_TIME, n_taxi=N_TAXI, n_passengers=N_PASSENGERS, capacities=MAX_PASSENGERS):
        self.n_passengers = n_passengers
        self.n_taxi = n_taxi
        self.capacities = capacities
        self.sim_time = sim_time
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
            if time % mod == 0:
                print("Current time: {}/{}".format(time, self.sim_time))
            self.iter(time)
        self.delivered_passengers_count()

    def iter(self, time):
        for agent in self.passengers + self.taxis:
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
            self.n_passengers, self.get_total_distance_driven(), self.get_total_earnings()))
        commuting_times = self.get_commuting_times()
        print("Driving time: average: {}, max: {}, std: {}".format(mean(commuting_times),
                                                                       max(commuting_times),
                                                                       stdev(commuting_times)))
        print("Average taxi occupancy = {}".format(mean(self.get_taxi_occupancy())))

    def get_commuting_times(self):
        commuting_times = []
        for agent in self.delivered_passengers:
            commuting_times.append(agent.driving_time)
        return commuting_times

    def get_total_distance_driven(self):
        return sum([taxi.distance_driven for taxi in self.taxis])

    def get_total_earnings(self):
        return sum([taxi.earnings for taxi in self.taxis])

    def get_taxi_occupancy(self):
        return [(taxi.occupancy_count / self.sim_time) for taxi in self.taxis]


# Match results with csv
def get_results(sim):
    commuting_times = sim.get_commuting_times()
    total_distance = sim.get_total_distance_driven()
    total_earnings = sim.get_total_earnings()
    total_taxi_occupancy = sim.get_taxi_occupancy()
    return [len(sim.delivered_passengers), mean(commuting_times), max(commuting_times),
            stdev(commuting_times), total_distance, total_earnings, mean(total_taxi_occupancy)]

def multi_sim(runs_per_setting = 5, sim_times=[SIM_TIME], n_taxis=[N_TAXI], n_passengers=[N_PASSENGERS], capacities=[MAX_PASSENGERS]):
    with open('results.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        for setting in itertools.product(sim_times, n_taxis, n_passengers, capacities):
            results = []
            for run in range(runs_per_setting):
                sim = Simulation(sim_time=setting[0], n_taxi=setting[1], n_passengers=setting[2], capacities=setting[3])
                sim.run()
                result = get_results(sim)
                results.append(result)
            results = np.array(results)
            agg_results = np.average(results, axis=0)
            settings_results = list(setting) + agg_results.tolist()
            writer.writerow(settings_results)
    f.close()







# sim = Simulation()
# sim.run()
# sim.end_simulation()
#
# passenger_node_map = {1:2, 2:4, 3:4, 4:5, 5:6, 6:7, 7:8, 8:8}
# print(passenger_node_map[4])
multi_sim(runs_per_setting=3, n_passengers=[50,100], capacities=[[1], [1, 2]])


# norm_mean = X_SIZE/2
# norm_std = X_SIZE/10
#
# # mean = math.exp(norm_mean + 0.5 * norm_std ** 2)
# # std = math.exp(2*norm_mean + norm_std ** 2) * (math.exp(norm_std ** 2) - 1)
#
# for i in range(100):
#     print(npr.normal(norm_mean, norm_std))


# py -m kernprof -l Main.py
# py -m line_profiler Main.py.lprof