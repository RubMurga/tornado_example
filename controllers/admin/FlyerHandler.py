from controllers.admin.auth import AuthHandler
from tornado import gen
from controllers.util.UtilProject import UtilProject
from models.flyer_model import FlyerModel
import json
class FlyerHandler(AuthHandler):
  @gen.coroutine
  def get(self, filter):
    self.__util = UtilProject()
    self.__model = FlyerModel()
    try:
      if self.__util.isInt(filter):
        pass
      elif filter == 'all':
        flyers = yield self.__model.get_all_flyers()
        if len(flyers) == 0:
          raise Exception('No hay ningún anuncio publicado')
        self.set_status(200)
        self.finish({'flyers': flyers})
    except Exception as error:
      self.set_status(400)
      self.finish({'message' : str(error)})

  @gen.coroutine
  def post(self, filter):
    data = json.loads(self.request.body.decode('utf-8'))
    self.__model = FlyerModel()
    try:
      result = yield self.__model.register_flyer(data)
      if not result:
        raise Exception('No se pudo publicar el folleto.')
      self.set_status(200)
      self.finish({'message': 'Anuncio publicado correctamente.'})
    except Exception as error:
      self.set_status(400)
      self.finish({'message' : str(error)})  
  def options(self, _):
    self.set_status(200)
    self.finish()