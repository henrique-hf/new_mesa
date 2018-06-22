import cherrypy
import json


class Catalog(object):
    exposed = True

    def __init__(self):
        with open("catalog.json") as file:
            self.catalog = json.load(file)

    def GET(self, *uri):
        if uri[0] == "catalog":
            return json.dumps(self.catalog)


if __name__ == "__main__":
    with open("conf_ws.json") as f:
        conf_ws = json.load(f)
    host = conf_ws["address"]
    port = int(conf_ws["port"])

    conf = {
        "/": {
            "request.dispatch": cherrypy.dispatch.MethodDispatcher(),
            "tools.sessions.on": True,
        }
    }
    cherrypy.tree.mount(Catalog(), "/", conf)
    cherrypy.config.update({
        "server.socket_host": host,
        "server.socket_port": port})
    cherrypy.engine.start()
    cherrypy.engine.block()