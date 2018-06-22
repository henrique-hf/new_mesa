from mesa import Agent
import json
import time


class Prosumer(Agent):

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.logger = self.model.logger
        self.mqtt = self.model.mqtt
        self.topic = self.model.topic + self.unique_id
        self.logger.info("%s created (%s)" % (self.unique_id, self.topic))

        # behavior parameters
        self.green_param = None
        self.money_param = None

        # other prosumers that will influence the behavior
        self.neighborhood = None
        self.neighbors = []
        self.social_circle = []

        # associate to an aggregator
        self.my_aggregator = None

    def broadcast_neighborhood(self):
        payload = {
            "prosumer": self.unique_id,
            "neighborhood": self.neighborhood
        }
        self.model.mqtt.publish(self.model.topic + "neighborhood", json.dumps(payload), self.model.qos)

    def add_to_aggr(self):
        payload = {
            "sender": {
                "type": "prosumer",
                "id": self.unique_id
            },
            "recipient": {
                "type": "aggregator",
                "id": self.my_aggregator
            },
            "subject": "add_to_aggr",
            "call_function": "add_pros",
            "message": {},
            "timestamp_sent:": time.time()
        }
        if self.my_aggregator in self.model.dict_aggr.keys():
            # call function add_pros
            self.model.dict_aggr[self.my_aggregator].add_pros(payload)
        else:
            self.mqtt.publish(self.model.topic + self.my_aggregator, json.dumps(payload), self.model.qos)

    def update_behavior(self):
        pass

    def load_profile(self):
        pass

    def update_circle(self):
        pass

