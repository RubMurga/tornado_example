import tornado.web
import jwt
JWT_SECRET = 'resttornadosupersecretkey'
JWT_ALGORITHM = 'HS256'
import json

class AuthHandler(tornado.web.RequestHandler):
  def set_default_headers(self):
    self.set_header("Access-Control-Allow-Origin", "*")
    self.set_header("Access-Control-Allow-Headers", "x-requested-with, authorization")
    self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
  
  def prepare(self):
    try:
      jwt_token = self.request.headers.get('authorization', None)
      decoded = jwt.decode(jwt_token,JWT_SECRET,JWT_ALGORITHM)
      if decoded['key'] != 'token_vendedor_super_secreto':
        raise Exception('token invalido!')
      self._user_id = decoded['empleado_id']
    except Exception as err: 
      import traceback
      traceback.print_exc()
      self.set_status(400)
      self.finish({'message': str(err)})
