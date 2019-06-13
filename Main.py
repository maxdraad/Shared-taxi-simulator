import itertools
from statistics import mean, stdev
import pandas as pd

import math
from joblib import Parallel, delayed
import multiprocessing
import numpy.random as npr

from Globals import *
from Passenger import Passenger
from Taxi import Taxi

class Simulation:
    def __init__(self, sim_time=SIM_TIME, n_taxi=N_TAXI, n_passengers=N_PASSENGERS, sharing_rate=SHARING_RATE,
                 nodes_limit=NODES_LIMIT):
        self.n_passengers = n_passengers
        self.n_taxi = n_taxi
        self.sharing_rate = sharing_rate
        self.n_public = round(self.n_taxi * self.sharing_rate)
        self.n_private = round(self.n_taxi * (1 - self.sharing_rate))
        self.nodes_limit = nodes_limit

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
        for x in range(self.n_public):
            taxis.append(Taxi(x, True, NODES_LIMIT))
        for x in range(self.n_private):
            taxis.append(Taxi(x, False, NODES_LIMIT))
        return taxis

    def print_statistics(self, commuting_times, total_distance_driven, earnings, average_taxi_occupancy):
        print("Simulation finished (Sharing rate: {})".format(self.sharing_rate))
        print("Agents delivered: {} / {}, distance driven: {}, earnings: {}".format(len(self.delivered_passengers),
            self.n_passengers, total_distance_driven, earnings))
        print("Driving time: average: {}, max: {}, std: {}".format(mean(commuting_times),
                                                                       max(commuting_times),
                                                                       stdev(commuting_times)))
        print("Average taxi occupancy = {}".format(mean(average_taxi_occupancy)))
        print("Debug count: " + str(DEBUG_COUNT))

    def results(self):
        for passenger in self.passengers:
            if passenger.status == "Delivered":
                self.delivered_passengers.append(passenger)
        commuting_times = []
        for agent in self.delivered_passengers:
            commuting_times.append(agent.driving_time)
        #     print("Passenger desired time: {}, actual waiting ({}) + driving ({}) time {}, delays : {}".format(
        #         agent.desired_travel_time, agent.driving_time, agent.waiting_time,
        #         agent.driving_time+agent.waiting_time, agent.delays))
        total_distance_driven = sum([taxi.distance_driven for taxi in self.taxis])
        earnings = sum([taxi.earnings for taxi in self.taxis])
        average_taxi_occupancy = [(taxi.occupancy_count/self.sim_time) for taxi in self.taxis]
        return commuting_times, total_distance_driven, earnings, average_taxi_occupancy



    def end_simulation(self):
        commuting_times, total_distance_driven, earnings, average_taxi_occupancy = self.results()
        self.print_statistics(commuting_times, total_distance_driven, earnings, average_taxi_occupancy)
        return len(self.delivered_passengers), mean(commuting_times), max(commuting_times), stdev(commuting_times), total_distance_driven, earnings, mean(average_taxi_occupancy)

    def iter(self, time):
        for agent in self.passengers + self.taxis:
            agent.step(time)

    def iter_parralel(self, time):
        num_cores = multiprocessing.cpu_count()
        Parallel(n_jobs=num_cores)(delayed(agent.step)(time) for agent in self.passengers + self.taxis)



    def run(self):
        mod = SIM_TIME / 100
        for time in range(SIM_TIME):
            if time % mod == 0:
                print("Current time: {}/{}".format(time, self.sim_time))
            self.iter(time)
            # if type(agent) == Passenger and agent.id == DEBUG_ID:
            #     print( 'Current time: {} Agent {} will request on time {} pos {} at {}, waiting time = {}'.format(
            #         time, agent.id, agent.request_time, agent.status, agent.orig, (agent.waiting_time+agent.driving_time)))
        # self.end_simulation()




def multi_sim(runs_per_setting = 5, sim_times=[SIM_TIME], n_taxis=[N_TAXI], n_passengers=[N_PASSENGERS], sharing_rates=[SHARING_RATE],
                 nodes_limits=[NODES_LIMIT]):
    for setting in itertools.product(sim_times, n_taxis, n_passengers, sharing_rates, nodes_limits):
        results = []
        for run in range(runs_per_setting):
            sim = Simulation(sim_time=setting[0], n_taxi=setting[1], n_passengers=setting[2], sharing_rate=setting[3],
                 nodes_limit=setting[4])
            sim.run()
            result = list(sim.end_simulation())
            results.append(result)


        results = pd.DataFrame(results, columns=['delivered_agents', 'commuting_mean', 'commuting_max', 'commuting_std', 'total_distance',
                     'earnings', 'taxi_occ_average'])
        agg_results = results.mean().tolist()

        f = open('results.csv', 'a')
        f.write('{},{},{},{},{},'.format(setting[0], setting[1], setting[2], setting[3], setting[4]))
        print(agg_results)
        f.write('{},{},{},{},{},{},{}\n'.format(*agg_results))
        f.close()






sim = Simulation()
sim.run()
sim.end_simulation()

# multi_sim(runs_per_setting=3, n_passengers=[50,100, 200], sharing_rates=[0, 0.5, 1])


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