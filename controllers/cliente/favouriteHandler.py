import tornado.web
import json

from controllers.util.UtilProject import UtilProject
from models.user_model import UserModel
from tornado import gen

class FavouriteHandler(tornado.web.RequestHandler):

  @gen.coroutine
  def post(self):
    try:
      self.__model = UserModel()
      data = json.loads(self.request.body.decode('UTF-8'))
      if not 'id_persona' in data and not 'id_producto' in data and not 'favorito' in data:
        raise Exception('No cumples con los datos necesarios.')
      id_cliente = yield self.__model.get_client_id_by_person_id(data['id_persona'])
      if not id_cliente:
        raise Exception('Ha ocurrido un error al buscar el cliente.')
      if data['favorito'] is 1:
        registered = yield self.__model.existent_favourite(id_cliente, data['id_producto'])
        if registered:
          raise Exception('Este producto ya estaba agregado a tus favoritos.')
        register = yield self.__model.add_client_favourite(id_cliente, data['id_producto'])
        if not register:
          raise Exception('Ha ocurrido un error.')    
        self.set_status(200)
        self.write({'message': 'Producto agregado a favoritos'})
      else:
        errased = yield self.__model.remove_client_favourite(id_cliente, data['id_producto'])
        if not errased:
          raise Exception('Ha habido un problema al remover de favoritos.')
        self.set_status(200)
        self.write({'message' : 'Se ha removido el producto de favoritos.'})
    except Exception as error:
      self.set_status(400)
      self.write({'message' : str(error)})
  
  @gen.coroutine
  def get(self):
    try:
      self.__model = UserModel()
      self.__util = UtilProject()
      id_cliente = yield self.__model.get_cliente_id_from_persona_id(self.get_argument('id_persona'))
      if not id_cliente:
        raise Exception('Ha ocurrido un error al buscar el cliente.')
      favourites = yield self.__model.get_client_favourites_products(id_cliente)
      if not favourites or len(favourites) == 0:
        raise Exception('No tienes ningún favorito registrado.')
      favourites = self.__util.cast_numeric_to_string(favourites, 'precio_venta')
      self.set_status(200)
      self.write({'products': favourites})
    except Exception as error:
      self.set_status(400)
      self.write({'message' : str(error)})