from statistics import mean, stdev
from joblib import Parallel, delayed
import multiprocessing

from Globals import *
from Passenger import Passenger
from Taxi import Taxi

class Simulation:
    def __init__(self, sim_time = SIM_TIME, n_taxi=N_TAXI, n_passengers=N_PASSENGERS, sharing_rate=SHARING_RATE, nodes_limit = NODES_LIMIT):
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
            taxis.append(Taxi(x, True))
        for x in range(self.n_private):
            taxis.append(Taxi(x, False))
        return taxis

    def print_statistics(self, commuting_times, total_distance_driven, earnings, average_taxi_occupance):
        print("Simulation finished (Sharing rate: {})".format(self.sharing_rate))
        print("Agents delivered: {} / {}, distance driven: {}, earnings: {}".format(len(self.delivered_passengers),
            self.n_passengers, total_distance_driven, earnings))
        print("Driving time: average: {}, max: {}, std: {}".format(mean(commuting_times),
                                                                       max(commuting_times),
                                                                       stdev(commuting_times)))
        print("Average taxi occupance = {}".format(mean(average_taxi_occupance)))
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
        average_taxi_occupance = [(taxi.occupance_count/self.sim_time) for taxi in self.taxis]
        return commuting_times, total_distance_driven, earnings, average_taxi_occupance



    def end_simulation(self):

        commuting_times, total_distance_driven, earnings, average_taxi_occupance = self.results()
        self.print_statistics(commuting_times, total_distance_driven, earnings, average_taxi_occupance)

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
        self.end_simulation()



sim = Simulation()
sim.run()

# print(Taxi.distance((1,1), (3,-3)))



# py -m kernprof -l Main.py
# py -m line_profiler Main.py.lprof