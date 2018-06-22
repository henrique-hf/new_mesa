from mesa import Agent
import xml.etree.cElementTree as et
import time
import json


class Supplier(Agent):

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.logger = self.model.logger
        self.mqtt = self.model.mqtt
        self.topic = self.model.topic + self.unique_id
        self.logger.info("%s created (%s)" % (self.unique_id, self.topic))

    def answer_price(self, msg):
        day = msg["message"]["day"]
        aggr = msg["sender"]["id"]
        list_price = []
        file_name = self.model.conf["supplier"]["folder"] + "/" + str(day) + self.model.conf["supplier"]["file_name"]
        # print(file_name)  # DEBUG
        parsed_xml = et.parse(file_name)
        for node in parsed_xml.getroot():
            price = node.find("PUN")
            if price is not None:
                value = price.text
                value = value.replace(",", ".")
                list_price.append(value)

        # build payload
        payload = {
            "sender": {
                "type": "supplier",
                "id": self.unique_id
            },
            "recipient": {
                "type": "aggregator",
                "id": aggr
            },
            "subject": "answer_price",
            "call_function": "load_price",
            "message": {
                "price": list_price
            },
            "timestamp_sent:": time.time()
        }
            
        if aggr in self.model.dict_aggr.keys():
            # call function from load_price
            self.model.dict_aggr[aggr].load_price(payload)
        else:
            self.mqtt.publish(self.model.topic + aggr, json.dumps(payload), self.model.qos)