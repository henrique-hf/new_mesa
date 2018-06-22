from mesa import Model
from mesa.time import RandomActivation
from commons.mqtt.mqtt_client import MqttClient
from agents.aggregator import Aggregator
from agents.prosumer import Prosumer
from agents.supplier import Supplier
import json
import time
import logging
import os
import requests
import random


class DistributedModel(Model):
    def __init__(self, model_name, qos=2):
        self.model_name = model_name
        self.qos = qos

        # schedule
        self.schedule = RandomActivation(self)

        # read conf
        with open("conf.json") as file:
            self.conf = json.load(file)
        self.topic = self.conf["topic"]
        self.catalog = self.conf["catalog_address"]
        self.broker = self.conf["broker_address"]
        self.log_level = logging.getLevelName(self.conf["log_level"])
        self.seed = self.conf["seed"]
        random.seed(self.seed)

        # read catalog
        response = requests.get(self.catalog + "catalog").content.decode("utf-8")
        # print(response)  # DEBUG
        dict_catalog = json.loads(response)
        self.num_neighbors = dict_catalog["neighbors"]["num_neighbors"]
        self.num_neighborhoods = dict_catalog["neighbors"]["num_neighborhoods"]
        self.num_circle = dict_catalog["neighbors"]["num_circle"]
        # discover all agents
        self.all_agents = []
        self.all_pros = []
        self.all_aggr = []
        for model_id in dict_catalog["model"].keys():
            for type_agent in dict_catalog["model"][model_id].keys():
                for i in range(dict_catalog["model"][model_id][type_agent]):
                    agent = "%s_%s_%d" % (type_agent, model_id, i)
                    self.all_agents.append(agent)
                    if type_agent == "prosumer":
                        self.all_pros.append(agent)
                    elif type_agent == "aggregator":
                        self.all_aggr.append(agent)
        # print(self.all_agents)  # DEBUG

        # Logger
        log_path = "./log/%s.log" % self.model_name
        formatter = logging.Formatter(
            self.model_name + ": " + "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")

        if not os.path.exists(log_path):
            try:
                os.makedirs(os.path.dirname(log_path))
            except Exception as e:
                pass

        self.logger = logging.getLogger(self.model_name)
        self.logger.setLevel(self.log_level)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        file_handler = logging.FileHandler(log_path, 'w')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # MQTT client
        self.mqtt = MqttClient(self.model_name, self.logger, self)
        self.mqtt.start(self.broker)
        time.sleep(2)

        # Extra topics to subscribe
        self.mqtt.subscribe(self.topic + "neighborhoods", self.qos)

        # neighborhoods (only local agents)
        self.dict_neighborhoods = {}
        for i in range(1, self.num_neighborhoods + 1):
            self.dict_neighborhoods[i] = []

        # create agents
        aggr = dict_catalog["model"][self.model_name]["aggregator"]
        pros = dict_catalog["model"][self.model_name]["prosumer"]
        supp = dict_catalog["model"][self.model_name]["supplier"]
        self.dict_aggr = {}
        self.dict_pros = {}
        self.dict_supp = {}
        for agent in range(aggr):
            name = "aggregator_%s_%d" % (self.model_name, agent)
            a = Aggregator(name, self)
            self.schedule.add(a)
            self.dict_aggr[name] = a
            self.mqtt.subscribe(self.topic + name, self.qos)
        for agent in range(pros):
            name = "prosumer_%s_%d" % (self.model_name, agent)
            a = Prosumer(name, self)
            # didn't add to the schedule
            self.dict_pros[name] = a
            self.mqtt.subscribe(self.topic + name, self.qos)
            a.neighborhood = random.randint(1, self.num_neighborhoods)  # associate neighborhood
            self.dict_neighborhoods[a.neighborhood].append(name)
            a.broadcast_neighborhood()
            a.social_circle.append(random.sample(self.all_pros, self.num_circle))  # create social circle
            a.my_aggregator = random.sample(self.all_aggr, 1)[0]   # associate aggregator
            a.add_to_aggr()
        for agent in range(supp):
            name = "supplier_%s_%d" % (self.model_name, agent)
            a = Supplier(name, self)
            # didn't add to schedule
            self.dict_supp[name] = a
            self.mqtt.subscribe(self.topic + name, self.qos)

        self.dict_local = {**self.dict_supp, **self.dict_pros, **self.dict_aggr}

    def step(self):
        self.schedule.step()

    def notify(self, topic, payload):
        msg = json.loads(payload.decode("utf-8"))
        print(msg)  # DEBUG
        if topic == self.topic + "neighborhoods":
            self.discover_neighborhoods(msg)
        else:
            # read recipient
            type_recipient = msg["recipient"]["type"]
            recipient = msg["recipient"]["id"]
            # read the function needed
            call_function = msg["call_function"]
            # call the recipients function
            if type_recipient == "aggregator":
                getattr(self.dict_aggr[recipient], call_function)(msg)
            elif type_recipient == "prosumer":
                getattr(self.dict_pros[recipient], call_function)(msg)
            elif type_recipient == "supplier":
                getattr(self.dict_supp[recipient], call_function)(msg)

    def discover_neighborhoods(self, msg):
        prosumer = msg["prosumer"]
        neighborhood = int(msg["neighborhood"])
        for a in self.dict_neighborhoods[neighborhood]:
            self.dict_pros[a].neighbors.append(prosumer)
        self.dict_neighborhoods[neighborhood].append(prosumer)

    def stop(self):
        self.mqtt.stop()


if __name__ == '__main__':
    model = DistributedModel("test_model")

    print(model.topic)