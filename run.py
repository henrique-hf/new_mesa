from model import DistributedModel
import json
import time

with open("conf.json") as f:
    conf = json.load(f)

model_name = conf["model_name"]
qos = conf["qos"]
num_steps = conf["num_steps"]

model = DistributedModel(model_name, qos)

for i in range(num_steps):
    model.step()
    time.sleep(5)

time.sleep(10)
model.stop()