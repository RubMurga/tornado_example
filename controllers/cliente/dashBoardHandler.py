import tornado.web 
from controllers.util.UtilProject import UtilProject
from tornado import gen
from models.flyer_model import *
class DashBoardHandler(tornado.web.RequestHandler):
  def set_default_headers(self):
    self.set_header("Access-Control-Allow-Origin", "*")
    self.set_header("Access-Control-Allow-Headers", "x-requested-with")
    self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
  
  @gen.coroutine
  def get(self):
    __model = models.flyer_model.FlyerModel()
    flyers = yield __model.get_flyer_by_date()
    self.write({'flyers': flyers})
    self.finish()  
    
