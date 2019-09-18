from controllers.admin.auth import AuthHandler
import json
import http.client
from models.beacons_model import BeaconModel
from tornado import gen
from controllers.util.UtilProject import UtilProject
from base64 import b64encode


class BeaconAdminHandler(AuthHandler):
  @gen.coroutine
  def get(self, filter):
    self.__util = UtilProject()
    if filter == 'all':
      conn = http.client.HTTPSConnection("")
      self.__model = BeaconModel()
      userAndPass = b64encode(b"key").decode("ascii")
      headers = {
          'content-type': "application/json",
          'authorization': "Basic %s" % userAndPass,
          }
      conn.request("GET", "/v2/devices",None, headers)
      res = conn.getresponse()
      data = res.read().decode('utf-8')
      data = json.loads(data)
      data = yield self.__model.get_beacons_data(data)
      self.__util.cast_datetime_to_string(data, ['fecha_sincronizacion'])
      self.write({'beacons': data})
  
  @gen.coroutine
  def put(self, id_beacon):
    data = json.loads(self.request.body.decode('utf-8'))
    try: 
      self.__model = BeaconModel()
      status, message = yield self.__model.update_beacon_department(id_beacon, data['department_id'])
      if not status:
        raise Exception(message)
      self.set_status(200)
      self.finish({'message' : message})
    except Exception as error: 
      self.set_status(400)
      self.finish({'message' : str(error)})
  
  def options(self, _):
    # no body
    self.set_status(200)
    self.finish()