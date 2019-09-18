import sys
sys.path.append("..")

import models.db_connection
from tornado import gen
import queries
from controllers.util.UtilProject import *

class ProductModel(models.db_connection.Connection):
  def __init__(self):
    super(ProductModel,self).__init__()
    self.__util = UtilProject()
  
  @gen.coroutine
  def get_all_products(self):
    sql = """
      SELECT producto.id_producto, producto.nombre as producto, producto.precio_venta, producto.stock,departamento.nombre AS departamento,tienda.nombre AS tienda, categoria.nombre AS categoria, marca.nombre AS marca,promocion.nombre AS promocion
      FROM producto,departamento,tienda,categoria,marca,promocion 
      WHERE producto.fk_id_departamento = departamento.id_departamento
      AND producto.fk_id_categoria = categoria.id_categoria
      AND producto.fk_id_marca = marca.id_marca
      AND producto.fk_id_promocion = promocion.id_promocion
      AND departamento.fk_id_tienda = tienda.id_tienda 
    """
      
    results_sql = yield self._session.query(sql)
    results = results_sql.items()
    results = self.__util.cast_numeric_to_string(results, 'precio_venta')
    results = yield self.assign_image_to_product(results)
    results_sql.free()
    return results
  
  @gen.coroutine
  def get_product_by_name(self,name):
    sql = """
          SELECT producto.id_producto, producto.nombre as producto, producto.precio_venta, producto.stock,departamento.nombre AS departamento,tienda.nombre AS tienda, categoria.nombre AS categoria, marca.nombre AS marca,promocion.nombre AS promocion
          FROM producto,departamento,tienda,categoria,marca,promocion 
          WHERE producto.fk_id_departamento = departamento.id_departamento
          AND producto.fk_id_categoria = categoria.id_categoria
          AND producto.fk_id_marca = marca.id_marca
          AND producto.fk_id_promocion = promocion.id_promocion
          AND departamento.fk_id_tienda = tienda.id_tienda 
          AND producto.nombre like 
        """
    sql = sql + "'%" + name + "%'"
    results_sql = yield self._session.query(sql)
    results = results_sql.items()
    results = self.__util.cast_numeric_to_string(results, 'precio_venta')
    results = yield self.assign_image_to_product(results)
    results_sql.free()
    return results
  
  @gen.coroutine 
  def get_product_by_id(self, id_product):
    sql = """
      SELECT producto.id_producto ,producto.nombre as producto, producto.precio_venta, producto.stock,departamento.nombre AS departamento,tienda.nombre AS tienda,marca.nombre AS marca,promocion.nombre AS promocion
      from producto, departamento, tienda, marca, promocion
      WHERE producto.fk_id_departamento = departamento.id_departamento
          AND producto.fk_id_marca = marca.id_marca
          AND producto.fk_id_promocion = promocion.id_promocion
          AND departamento.fk_id_tienda = tienda.id_tienda 
          AND producto.id_producto = %s
    """ % id_product
    product_sql = yield self._session.query(sql)
    product = product_sql.as_dict()
    product_images = yield self.get_all_product_images(id_product)
    product['imagenes'] = product_images
    product = self.__util.cast_numeric_to_string([product], 'precio_venta')
    product_sql.free()
    return product[0]

  @gen.coroutine
  def get_all_product_images(self, id_product): 
    sql = """
      SELECT imagen_producto.ruta 
      FROM imagen_producto, producto_imagen
      WHERE   producto_imagen.fk_id_imagen = imagen_producto.id_imagen_producto
      AND   producto_imagen.fk_id_producto = %s
    """ % id_product
    images = yield self._session.query(sql) # TODO : CAMBIAR LO DE RUTA
    if (len(images) == 0 or images == None):
      no_images = []
      no_images.append('http://bestwork.com.ar/productos/KX-FAP107A.png')
      images.free()
      return no_images
    else:
      images_list = []
      for producto in images.items():
        if not producto['ruta'] in images_list:
          images_list.append(producto['ruta'])
      images.free()
      return images_list

  @gen.coroutine
  def assign_image_to_product(self,products):
    for product in products:
      sql = """
        SELECT imagen_producto.ruta 
        FROM imagen_producto, producto_imagen, producto
        WHERE imagen_producto.id_imagen_producto = producto_imagen.fk_id_imagen
        AND producto_imagen.fk_id_producto = producto.id_producto
        AND producto.id_producto = %i
      """ % product['id_producto']
      images = yield self._session.query(sql)
      images_list = images.items()
      product['image'] = images_list[0]['ruta'] if images_list else 'http://bestwork.com.ar/productos/KX-FAP107A.png'
      images.free()
    return products

  @gen.coroutine
  def get_parent_categorie(self, id_categoria):
    sql = """
      SELECT par.id_categoria, par.nombre, par.fk_id_padre_cat
      FROM categoria cat, categoria par
      WHERE cat.fk_id_padre_cat = par.id_categoria 
      AND cat.id_categoria = {0}
       """.format(id_categoria)
    data = yield self._session.query(sql)
    data_to_return = data.as_dict()
    data.free()
    return data_to_return
## sistema de recomendaciones
  
  @gen.coroutine
  def get_products_by_department(self, id_departamento):
    sql = 'SELECT producto.id_producto, producto.x, producto.mu FROM producto WHERE fk_id_departamento = %s' % id_departamento
    results = yield self._session.query(sql)
    products = results.items()
    results.free()
    return products
        
  @gen.coroutine
  def get_recommendations_specific_info(self, recommendations):
    for recom in recommendations:
      sql = """
        SELECT producto.nombre as producto, producto.precio_venta, producto.stock,departamento.nombre AS departamento,tienda.nombre AS tienda, categoria.nombre AS categoria, marca.nombre AS marca,promocion.nombre AS promocion
          FROM producto,departamento,tienda,categoria,marca,promocion 
          WHERE producto.fk_id_departamento = departamento.id_departamento
          AND producto.fk_id_categoria = categoria.id_categoria
          AND producto.fk_id_marca = marca.id_marca
          AND producto.fk_id_promocion = promocion.id_promocion
          AND departamento.fk_id_tienda = tienda.id_tienda 
          AND producto.id_producto = %s 
      """ %recom["id_producto"]
      result = yield self._session.query(sql)
      product = result.as_dict()
      recom["producto"] = product["producto"]
      recom["precio_venta"] = product["precio_venta"]
      recom["stock"] = product["stock"]
      recom["departamento"] = product["departamento"]
      recom["tienda"] = product["tienda"]
      recom["categoria"] = product["categoria"]
      recom["marca"] = product["marca"]
      recom["promocion"] = product["promocion"]
      result.free()
    recommendations = yield self.assign_image_to_product(recommendations)
    return recommendations

  @gen.coroutine
  def get_all_products_recom(self):
    sql = 'SELECT producto.id_producto FROM producto' 
    results = yield self._session.query(sql)
    products = results.items()
    results.free()
    return products
  
  @gen.coroutine
  def get_default_recommendations(self):
    sql = """
        SELECT producto.id_producto, producto.nombre as producto, producto.precio_venta, producto.mu AS score,producto.stock,departamento.nombre AS departamento,tienda.nombre AS tienda, categoria.nombre AS categoria, marca.nombre AS marca,promocion.nombre AS promocion
          FROM producto,departamento,tienda,categoria,marca,promocion 
          WHERE producto.fk_id_departamento = departamento.id_departamento
          AND producto.fk_id_categoria = categoria.id_categoria
          AND producto.fk_id_marca = marca.id_marca
          AND producto.fk_id_promocion = promocion.id_promocion
          AND departamento.fk_id_tienda = tienda.id_tienda 
          ORDER BY producto.mu DESC LIMIT 100
      """
    result = yield self._session.query(sql)
    products = result.items()
    recommendations = yield self.assign_image_to_product(products)
    result.free()
    return recommendations
  
  @gen.coroutine
  def get_default_recommendations_department(self, id_departamento):
    sql = """
        SELECT producto.id_producto, producto.nombre as producto, producto.precio_venta, producto.mu AS score,producto.stock,departamento.nombre AS departamento,tienda.nombre AS tienda, categoria.nombre AS categoria, marca.nombre AS marca,promocion.nombre AS promocion
          FROM producto,departamento,tienda,categoria,marca,promocion 
          WHERE producto.fk_id_departamento = departamento.id_departamento
          AND producto.fk_id_categoria = categoria.id_categoria
          AND producto.fk_id_marca = marca.id_marca
          AND producto.fk_id_promocion = promocion.id_promocion
          AND departamento.fk_id_tienda = tienda.id_tienda 
          AND departamento.id_departamento = %s
          ORDER BY producto.mu DESC LIMIT 15
      """ % id_departamento
    result = yield self._session.query(sql)
    products = result.items()
    recommendations = yield self.assign_image_to_product(products)
    result.free()
    return recommendations

    
