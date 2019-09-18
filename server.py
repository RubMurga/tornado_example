import tornado.ioloop
import tornado.web 
import tornado.options
import tornado.httpserver

from tornado.options import define,options
from controllers.admin import monitorHandler as AdminMonitor, logInHandler as AdminLogInHandler, BeaconHandler, DepartmentHandler, FlyerHandler, ClusterHandler
from controllers.cliente import dashBoardHandler, productHandler
from controllers.vendedor import logInHandler as VendedorLogInHandler, vendedorHandler, monitorHandler as VendedorMonitor
from controllers.cliente import clienteHandler, proximityHandler as clientProximityZones, favouriteHandler, recommendationsHandler
define('port', default=5000, help='corre el servidor con la bandera --port=puerto', type=int)
import os

class IndexHandler(tornado.web.RequestHandler):
  def get(self):
    return self.write({'hola': 'hola desde tornado'})

class App(tornado.web.Application):
  def __init__(self):
    Handlers = [
      (r'/', IndexHandler),
      (r'/administrador/login', AdminLogInHandler.LogInHandler), # ya 
      (r'/administrador/beacons/(\w+)', BeaconHandler.BeaconAdminHandler), #ya
      (r'/administrador/departments/(\w+)', DepartmentHandler.DepartmentAdminHandler), #ya
      (r'/administrador/store-monitor/(\w+)', AdminMonitor.StoreMonitor), #ya
      (r'/administrador/beacon-monitor/(\w+)', AdminMonitor.BeaconMonitor),  #ya
      (r'/administrador/flyers/(\w+)', FlyerHandler.FlyerHandler), #ya
      (r'/administrador/execute-cluster', ClusterHandler.ClusterHandler), #ya
      (r'/administrador/get-stored-cluster', ClusterHandler.InitialClusterHandler), #ya
      (r'/beacon-monitor/(\w+)', VendedorMonitor.BeaconMonitor), #ya 
      (r'/vendedor/login', VendedorLogInHandler.LogInHandler), #rf4
      (r'/products/(\w+)', productHandler.ProductHandler), # ya
      (r'/dashboard-client/', dashBoardHandler.DashBoardHandler), #ya
      (r'/proximity-zones', clientProximityZones.BeaconAttachments),  #ya
      (r'/vendedor', vendedorHandler.VendedorHandler),   # ya
      (r'/vendedor/departamento/(\w+)', vendedorHandler.VendedorClienteHandler), #ya
      (r'/vendedor/client-details/(\w+)', vendedorHandler.VendedorClienteDetailsHandler), #rya
      (r'/vendedor/recommend/(\w+)/(\w+)', vendedorHandler.VendedorSendNotificationHandler), #rya
      (r'/vendedor/update-token-fcm', vendedorHandler.VendedorTokenFCMHandler), #ya
      (r'/vendedor/get-client-basic-info', vendedorHandler.VendedorGetClientInfo),
      (r'/client', clienteHandler.ClienteHandlerNoFB), #ya 
      (r'/client/login', clienteHandler.ClienteLogInHandler),
      (r'/client/favourites', favouriteHandler.FavouriteHandler), #ya
      (r'/client/update-token-fcm', clienteHandler.TokenFCMHandler), #ya
      (r'/client/permissions/(\w+)', clienteHandler.PermissionsHandler), # ya
      (r'/client/likes/(\w+)', clienteHandler.LikesHandler), #ya
      (r'/client/retrieve-password', clienteHandler.PasswordHandler),
      (r'/client/get-beneficts/(\w+)', clienteHandler.BenefictsHandler),#ya
      (r'/client/get-achievements/(\w+)', clienteHandler.AchievementsHandler),#ya
      (r'/client/personal-info/(\w+)', clienteHandler.InformationHandler), #ya
      (r'/client/get-global-recom/(\w+)', recommendationsHandler.ClientRecomHandler),
      (r'/client/recommendations/department/(\w+)/(\w+)', recommendationsHandler.RecomHandlerDepartment),
      (r'/global-recommendations', recommendationsHandler.RecomHandler),
      (r'/client/(\w+)/request-help/(\w+)', clienteHandler.RequestHelpHandler)
    ]
    settings = {
      'debug' : True
    }
    tornado.web.Application.__init__(self,Handlers, **settings)
if __name__ == '__main__':
  tornado.options.parse_command_line()
  app = App()
  http_server = tornado.httpserver.HTTPServer(app)
  port = int(os.getenv('PORT', 4200))
  print(port)
  http_server.listen(port, address='0.0.0.0')
  print('Servidor corriendo en el puerto %i' % port)
  tornado.ioloop.IOLoop.instance().start()
