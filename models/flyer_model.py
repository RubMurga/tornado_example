import sys
sys.path.append("..")
from controllers.util.UtilProject import *
import models.db_connection
from tornado import gen
import queries
from datetime import date, datetime

class FlyerModel(models.db_connection.Connection):
  def __init__(self):
    super(FlyerModel,self).__init__()
    self.__util = UtilProject()
  
  @gen.coroutine
  def get_all_flyers(self):
    today = datetime.now()
    flyers_sql = yield self._session.query('SELECT * FROM anuncio')
    flyers = [flyer for flyer in flyers_sql]
    for flyer in flyers:
      flyer['departments'] = yield self.get_flyer_departments(flyer['id_anuncio'])
      flyer['products'] = yield self.get_flyer_products(flyer['id_anuncio'])
      flyer['activo'] = False
      if today >= flyer['fecha_inicio'] and today <= flyer['fecha_fin']:
        flyer['activo'] = True
    flyers = self.__util.cast_datetime_to_string(flyers,['fecha_inicio', 'fecha_fin'])
    flyers_sql.free()
    return flyers
  @gen.coroutine
  def get_flyer_by_date(self):  
    today = date.today()
    flyers_sql = yield self._session.query("SELECT * FROM anuncio where '%s' BETWEEN fecha_inicio AND fecha_fin" % today)
    print("SELECT * FROM anuncio where '%s' BETWEEN fecha_inicio AND fecha_fin" % today)
    flyers = [flyer for flyer in flyers_sql]
    for flyer in flyers:
      flyer['departments'] = yield self.get_flyer_departments(flyer['id_anuncio'])
      flyer['products'] = yield self.get_flyer_products(flyer['id_anuncio'])
    flyers = self.__util.cast_datetime_to_string(flyers,['fecha_inicio', 'fecha_fin'])
    flyers_sql.free()
    return flyers

  
  @gen.coroutine
  def get_flyer_departments(self, flyer_id):
    sql = """SELECT departamento.*,tienda.nombre AS tienda 
      FROM tienda,departamento,departamento_anuncio,anuncio
      WHERE tienda.id_tienda = departamento.fk_id_tienda
      AND departamento.id_departamento = departamento_anuncio.fk_id_departamento
      AND departamento_anuncio.fk_id_anuncio = anuncio.id_anuncio
      AND anuncio.id_anuncio = %i
      """ % flyer_id
    departments = yield self._session.query(sql)
    departments_to_return = departments.items()
    departments.free()
    return departments_to_return
  
  @gen.coroutine
  def get_flyer_products(self,flyer_id):
    sql = """SELECT producto.nombre as producto, producto.precio_venta, producto.stock, marca.nombre as marca, promocion.nombre as promocion, tienda.nombre as tienda
          FROM producto,producto_anuncio,anuncio, marca, promocion, tienda, departamento
          WHERE producto.id_producto = producto_anuncio.fk_id_producto
          AND producto.fk_id_marca = marca.id_marca
          AND producto.fk_id_departamento = departamento.id_departamento
          AND departamento.fk_id_tienda = tienda.id_tienda
          AND producto.fk_id_promocion = promocion.id_promocion
          AND producto_anuncio.fk_id_anuncio = anuncio.id_anuncio
          AND anuncio.id_anuncio = %i
      """ % flyer_id
    products = yield self._session.query(sql)
    products_to_return = products.items()
    products_to_return = self.__util.cast_numeric_to_string(products_to_return, 'precio_venta')
    products.free()
    return products_to_return
  
  @gen.coroutine
  def register_flyer(self, flyer):
    sql = """
    INSERT INTO anuncio(titulo, descripcion, fecha_inicio, fecha_fin, ruta_imagen) 
    VALUES('%s', '%s', '%s', '%s', 'http://icons.iconarchive.com/icons/graphicloads/colorful-long-shadow/256/Announcement-icon.png')
    """ % (flyer['name'], flyer['description'], flyer['init_date'], flyer['end_date'])
    flyer_db = yield self._session.query(sql)
    if not flyer_db:
      flyer_db.free()
      return False
    sql = """
    SELECT id_anuncio from anuncio where titulo = '%s' AND descripcion = '%s'
    """ % (flyer['name'], flyer['description'])
    registered_flyer = yield self._session.query(sql)
    registered_flyer = registered_flyer.items()
    registered_flyer = registered_flyer[0]
    for product in flyer['products']:
      print(product)
      sql = """
        INSERT INTO producto_anuncio(fk_id_producto, fk_id_anuncio)
        VALUES(%s, %s)
      """ % (product['id'], registered_flyer['id_anuncio'])
      inserted_product = yield self._session.query(sql)

    for department in flyer['departments']:
      sql = """
        INSERT INTO departamento_anuncio(fk_id_departamento, fk_id_anuncio)
        VALUES(%s, %s)
      """ % (department['id'], registered_flyer['id_anuncio'])
      inserted_department = yield self._session.query(sql)
    flyer_db.free()
    registered_flyer.free()
    inserted_product.free()
    inserted_department.free()
    return True 

