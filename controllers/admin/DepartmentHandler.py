from controllers.admin.auth import AuthHandler
from tornado import gen
from controllers.util import UtilProject
from models.store_model import StoreModel
class DepartmentAdminHandler(AuthHandler):
  __util = UtilProject.UtilProject()
  @gen.coroutine
  def get(self, filter):
    self.__model = StoreModel()
    try:
      if self.__util.isInt(filter):
        departments = yield self.__model.get_store_departments(filter)
        if len(departments) == 0:
          raise Exception('No existen departamentos en esta tienda.')
        
        self.set_status(200)
        self.finish({'departments' : departments})
      elif filter == 'all':
        pass
    except Exception as error:
      self.set_status(400)
      self.finish({'message' : str(error)})
    
  def options(self):
    self.set_status(200)
    self.finish()