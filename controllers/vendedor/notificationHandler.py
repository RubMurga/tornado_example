import tornado.web
import json
import http.client

from datetime import datetime
from controllers.util.UtilProject import UtilProject
from models import monitor_model
from tornado import gen
from controllers.vendedor.auth import AuthHandler # aqui hay un problema 
from models.user_model import UserModel
from pyfcm import FCMNotification
from controllers.util.UtilProject import UtilProject

# -- beacons
class NotificationHandler(AuthHandler):
  push_service = FCMNotification(api_key=UtilProject.serverFCMKey)

  def set_default_headers(self):
    self.set_header("Access-Control-Allow-Origin", "*")
    self.set_header("Access-Control-Allow-Headers", "x-requested-with")
    self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
  
  @gen.coroutine  
  def get(self):
    self.set_status(200)
    self.finish()