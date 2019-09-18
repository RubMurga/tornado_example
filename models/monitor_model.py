import models.db_connection
from tornado import gen
import queries
import datetime
class MonitorModel(models.db_connection.Connection):
  def __init__(self):
    super(MonitorModel,self).__init__()
  
  @gen.coroutine
  def get_beacons(self):
    results = yield self._session.query('SELECT * FROM departamento_beacon')
    result_array = []
    for row in results:
      row['posicion_geografica'] = list(eval(row['posicion_geografica']))
      result_array.append(row)
    results.free()
    return result_array
  
  @gen.coroutine
  def insert_beacon(self,beacons):
    inserted = 0
    updated = 0
    for beacon in beacons:
      try:
        insert = yield self._session.query("INSERT INTO departamento_beacon values('%s',%i, (point(%f,%f)), (SELECT current_timestamp))" % (beacon['id_beacon'], beacon['fk_id_departamento'], beacon['x'], beacon['y']))
        inserted = inserted +1
      except:
        update = yield self._session.query("UPDATE departamento_beacon set fk_id_departamento = %i, posicion_geografica = (point(%f,%f)), fecha_sincronizacion = (SELECT current_timestamp) WHERE id_beacon = '%s'" % (beacon['fk_id_departamento'], beacon['x'], beacon['y'], beacon['id_beacon']))
        updated = updated +1
      try:
        insert.free()
        update.free()
      except:
        pass
    return {'inserted': inserted, 'updated':updated}  
  @gen.coroutine
  def get_stores(self):
    results = yield self._session.query('SELECT * FROM tienda')
    result_array = []
    for row in results:
      row['posicion_geografica'] = list(eval(row['posicion_geografica']))
      result_array.append(row)
    results.free()
    return result_array
  
  @gen.coroutine
  def get_beacon_info(self,beacon):
    result = yield self._session.query("SELECT tienda.nombre AS tienda, departamento.nombre AS departamento FROM tienda, departamento, departamento_beacon WHERE tienda.id_tienda = departamento.fk_id_tienda AND departamento.id_departamento = departamento_beacon.fk_id_departamento AND departamento_beacon.id_beacon = '%s' " % beacon)
    result_to_return = result.as_dict()
    result.free()
    return result_to_return

  @gen.coroutine
  def get_store_by_id(self,store_id):
    store = yield self._session.query("SELECT tienda.nombre, direccion.* FROM tienda,direccion WHERE tienda.fk_id_direccion = direccion.id_direccion AND tienda.id_tienda = %s" % store_id)
    store_to_return = store.as_dict()
    store.free()
    return store_to_return
    

    