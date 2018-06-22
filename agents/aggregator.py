from mesa import Agent
import time
import json


class Aggregator(Agent):

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.logger = self.model.logger
        self.mqtt = self.model.mqtt
        self.topic = self.model.topic + self.unique_id
        self.logger.info("%s created (%s)" % (self.unique_id, self.topic))

        # parameters
        self.price = []

        # list of clients (prosumers)
        self.my_clients = []

    def ask_price(self, day, supplier):
        payload = {
            "sender": {
                "type": "aggregator",
                "id": self.unique_id
            },
            "recipient": {
                "type": "supplier",
                "id": supplier
            },
            "subject": "ask_price",
            "call_function": "answer_price",
            "message": {
                "day": day
            },
            "timestamp_sent:": time.time()
        }
        if supplier in self.model.dict_supp.keys():
            # call function answer_price
            self.model.dict_supp[supplier].answer_price(payload)
        else:
            self.mqtt.publish(self.model.topic + supplier, json.dumps(payload), self.model.qos)

    def load_price(self, msg):
        self.price = msg["message"]["price"]
        self.price = [float(i) for i in self.price]

    def add_pros(self, msg):
        pros = msg["sender"]["id"]
        self.my_clients.append(pros)
        print(self.my_clients)  # DEBUG

    def step(self):
        self.ask_price("20170101", "supplier_model1_0")  # DEBUG
        print(self.price)  # DEBUG
