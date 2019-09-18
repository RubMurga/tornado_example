import tornado.web
import json

from controllers.util.UtilProject import UtilProject
from models import product_model
from tornado import gen

class ProductHandler(tornado.web.RequestHandler): 
    __util = UtilProject()
    __model = product_model.ProductModel()
    def set_default_headers(self):
      self.set_header("Access-Control-Allow-Origin", "*")
      self.set_header("Access-Control-Allow-Headers", "x-requested-with")
      self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
    
    @gen.coroutine
    def get(self, product):
      if self.__util.isInt(product):
        __product = yield self.__model.get_product_by_id(product)
        self.write(__product)
      else:  
        if product == 'all':
          __products = yield self.__model.get_all_products()
          self.write({'products' : __products})
        else:
          if 'product' in self.request.arguments:
             __products = yield self.__model.get_product_by_name(self.get_argument('product'))
          else: 
            __products = yield self.__model.get_product_by_name(product)
          self.write({'products' : __products})
    
    def options(self, product):
      self.set_status(200)
      self.finish()
