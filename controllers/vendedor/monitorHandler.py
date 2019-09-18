import tornado.web
import json
import http.client

from datetime import datetime
from controllers.util.UtilProject import UtilProject
from models import monitor_model
from tornado import gen
from controllers.vendedor.auth import AuthHandler # aqui hay un problema 
from models.user_model import UserModel
from pyfcm import FCMNotification
from base64 import b64encode

# -- beacons
class BeaconMonitor(AuthHandler):
  push_service = FCMNotification(api_key=UtilProject.serverFCMKey)
  settings = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'mygroup',
    'client.id': 'client-1',
    'enable.auto.commit': True,
    'session.timeout.ms': 6000,
    'default.topic.config': {'auto.offset.reset': 'smallest'}
  }

  def unique_clients(self, clients):
    uniques = []
    for client in clients:
      add = True
      for cli in list(uniques):
        if client['id_person'] == cli['id_person']:
          add = False
          dtClient = datetime.strptime(client['time'], '%d/%m/%Y a las %H:%M:%S')
          dtCli = datetime.strptime(cli['time'], '%d/%m/%Y a las %H:%M:%S')
          if dtClient > dtCli:
            add = True
            uniques.remove(cli)
      if add:
        uniques.append(client)

    return uniques

  def sort_by_score(self, data):
    try:
      return int(data['score'])
    except KeyError:
      return 0

  def set_default_headers(self):
    self.set_header("Access-Control-Allow-Origin", "*")
    self.set_header("Access-Control-Allow-Headers", "x-requested-with")
    self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
  
  @gen.coroutine  
  def get(self,beacon):
    if beacon == 'all':
      beacons = monitor_model.MonitorModel().get_beacons()
      result = yield beacons
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
      beacon_data = json.loads(res.read())
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
    
