from statistics import mean, stdev
from joblib import Parallel, delayed
import multiprocessing

from Globals import *
from Passenger import Passenger
from Taxi import Taxi

class Simulation:
    def __init__(self):
        self.init_passengers()
        self.init_taxis()

    def init_passengers(self):
        for x in range(N_PASSENGERS):
            passengers.append(Passenger(x))

    def init_taxis(self):
        for x in range(N_PUBLIC):
            taxis.append(Taxi(x, True))
        for x in range(N_PRIVATE):
            taxis.append(Taxi(x, False))

    def end_statements(self):
        print("Simulation finished (Sharing rate: {})".format(SHARING_RATE))
        commuting_times = []
        for agent in delivered_passengers:
            commuting_times.append(agent.driving_time)
        #     print("Passenger desired time: {}, actual waiting ({}) + driving ({}) time {}, delays : {}".format(
        #         agent.desired_travel_time, agent.driving_time, agent.waiting_time,
        #         agent.driving_time+agent.waiting_time, agent.delays))
        total_distance_driven = sum([taxi.distance_driven for taxi in taxis])
        earnings = sum([taxi.earnings for taxi in taxis])
        print("Agents delivered: {} / {}, distance driven: {}, earnings: {}".format(len(delivered_passengers),
            N_PASSENGERS, total_distance_driven, earnings))
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