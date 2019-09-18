import tornado.web 
import json
from controllers.util.UtilProject import UtilProject
import http.client
from base64 import b64encode


class BeaconAttachments(tornado.web.RequestHandler):
  __util = UtilProject()
  
  def get(self):
    __util = UtilProject()
  
    conn = http.client.HTTPSConnection("cloud.estimote.com")
    userAndPass = b64encode(b"key").decode("ascii")
    headers = {
        'content-type': "application/json",
        'authorization': "Basic %s " % userAndPass,
        }
    conn.request("GET", "/v3/devices", headers=headers)
    res = conn.getresponse()
    data = res.read().decode('utf-8')
    data = json.loads(data)
    data = self.__util.create_proximity_zones(data['data'])
    self.write(data)