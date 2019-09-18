import models.db_connection
from tornado import gen
import queries

class BeaconModel(models.db_connection.Connection):
  def __init__(self):
    super(BeaconModel,self).__init__()
  
  @gen.coroutine
  def get_beacons_data(self, beacons):
    for beacon in beacons:
      __sql = """
        SELECT departamento_beacon.fecha_sincronizacion, departamento.nombre as department, departamento.planta as floor, tienda.nombre as store, direccion.* 
        FROM departamento_beacon, departamento, tienda, direccion
        WHERE departamento_beacon.fk_id_departamento = departamento.id_departamento
        AND departamento.fk_id_tienda = tienda.id_tienda
        AND tienda.fk_id_direccion = direccion.id_direccion
        AND departamento_beacon.id_beacon = '%s'
      """ % beacon['identifier']
      __beacon_sql_data = yield self._session.query(__sql)
      __beacon_sql_data_dict = __beacon_sql_data.as_dict()
      if __beacon_sql_data_dict:
        beacon['fecha_sincronizacion'] = __beacon_sql_data_dict['fecha_sincronizacion']
        beacon['department'] = __beacon_sql_data_dict['department']
        beacon['floor'] = __beacon_sql_data_dict['floor']
        beacon['store'] = __beacon_sql_data_dict['store']
        beacon['address'] = {
          'street' : __beacon_sql_data_dict['calle'],
          'colony' : __beacon_sql_data_dict['colonia'],
          'delegacion_municipio' : __beacon_sql_data_dict['delegacion_municipio'],
          'city' : __beacon_sql_data_dict['ciudad_estado'],
          'cp' : __beacon_sql_data_dict['codigo_postal']
        }
    __beacon_sql_data.free()
    return beacons
  
  @gen.coroutine
  def update_beacon_department(self, beacon, department):
    __sql = "UPDATE departamento_beacon SET fk_id_departamento = %s WHERE id_beacon = '%s'" % (department, beacon)
    __response = yield self._session.query(__sql)
    if not __response:
      __response.free()
      return False, 'Ha ocurrido un error actualizando la información.'  
    __response.free()
    return True, 'La información del Beacon se ha actualizado correctamente.'
    