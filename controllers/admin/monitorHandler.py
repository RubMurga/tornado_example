import tornado.web
import json
import http.client

from datetime import datetime
from controllers.util.UtilProject import UtilProject
from models import monitor_model
from tornado import gen
from controllers.admin.auth import AuthHandler # aqui hay un problema 
from models.user_model import UserModel

# -- beacons
class BeaconMonitor(AuthHandler):
  
  @gen.coroutine  
  def get(self,beacon):
    if beacon == 'all':
      __util = UtilProject()
      beacons = monitor_model.MonitorModel().get_beacons()
      result = yield beacons
      result = __util.cast_datetime_to_string(result,['fecha_sincronizacion'])
      return self.write({'beacons' : result})
    else: 
      conn = http.client.HTTPSConnection("cloud.estimote.com")
      payload = "{\n\t\"id_beacon\" : 2,\n\t\"x\"  : 19.4336249,\n\t\"y\"  : -99.1848619,\n\t\"fk_id_departamento\": 1\n}"
      headers = {
          'content-type': "application/json",
          'authorization': "Basic c2FwcGhpcmUtN3NjOjJiMzIzYzgyMWJjYTFhMzE3OTM3ZGJkZjk1ZmZhYzA2",
          'cache-control': "no-cache",
          'postman-token': "eda58ff2-7ee8-dd7e-5bf2-bfed18a69269"
          }
      conn.request("GET", "/v2/devices/"+beacon, payload, headers)

      res = conn.getresponse()
      beacon_data = json.loads(res.read().decode('utf-8'))
      beacon_data_db = monitor_model.MonitorModel.get_beacon_info
      beacon_data_db = yield beacon_data_db(monitor_model.MonitorModel(), beacon)
      beacon_data['store'] = beacon_data_db['tienda']
      beacon_data['department'] = beacon_data_db['departamento']
      return self.write(beacon_data)

    self.finish()
    
  @gen.coroutine
  def post(self,beacon): 
    data = json.loads(self.request.body.decode('utf-8'))
    insert_beacon = monitor_model.MonitorModel.insert_beacon
    objeto = monitor_model.MonitorModel()
    insert_beacon = yield insert_beacon(objeto,data)
    #print(insert_beacon)
    self.finish()

# -- stores
class StoreMonitor(AuthHandler):

  @gen.coroutine
  def get(self,store_id):
    if store_id == 'all': 
      stores = monitor_model.MonitorModel().get_stores()
      result = yield stores
      return self.write({'stores' : result})
    else: 
      store_object = monitor_model.MonitorModel().get_store_by_id(store_id)
      store_object = yield store_object
      self.write(store_object)
    self.finish()

class BeaconAttachments(AuthHandler):
  __util = UtilProject()
  
  def get(self):
    conn = http.client.HTTPSConnection("cloud.estimote.com")
    payload = "{\n\t\"id_beacon\" : 2,\n\t\"x\"  : 19.4336249,\n\t\"y\"  : -99.1848619,\n\t\"fk_id_departamento\": 1\n}"
    headers = {
        'content-type': "application/json",
        'authorization': "Basic c2FwcGhpcmUtN3NjOjJiMzIzYzgyMWJjYTFhMzE3OTM3ZGJkZjk1ZmZhYzA2",
        'cache-control': "no-cache",
        'postman-token': "eda58ff2-7ee8-dd7e-5bf2-bfed18a69269"
        }
    conn.request("GET", "/v3/attachments", payload, headers)
    res = conn.getresponse()
    data = res.read().decode('utf-8')
    data = json.loads(data)
    data = self.__util.create_proximity_zones(data['data'])
    self.write(data)
    
