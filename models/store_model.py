import queries
import models.db_connection 
from tornado import gen

class StoreModel(models.db_connection.Connection):
  def __init__(self):
    super(StoreModel,self).__init__()
  
  @gen.coroutine 
  def get_store_departments(self, store_id):
    sql = 'SELECT departamento,* FROM departamento, tienda WHERE departamento.fk_id_tienda = tienda.id_tienda AND tienda.id_tienda = %s ' % store_id
    departments = yield self._session.query(sql)
    departments_to_return = departments.items()
    departments.free()
    return departments_to_return
  @gen.coroutine
  def get_all_likes(self):
    sql = 'SELECT categoria.nombre FROM categoria WHERE fk_id_padre_cat IS NULL'
    likes = yield self._session.query(sql)
    likes_to_return = likes.items()
    likes.free()
    return likes_to_return