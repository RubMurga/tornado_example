import tornado.web
import jwt
JWT_SECRET = 'resttornadosupersecretkey'
JWT_ALGORITHM = 'HS256'
import json

class AuthHandler(tornado.web.RequestHandler):
  def set_default_headers(self):
    self.set_header("Access-Control-Allow-Origin", "*")
    self.set_header("Access-Control-Allow-Headers", "Content-Type, authorization")
    self.set_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
  
  def prepare(self):
    if self.request.method == 'OPTIONS':
      if self.request.headers['Access-Control-Request-Headers'] == 'authorization':
        self.set_status(200)
        self.finish()
        return 
    if self.request.method != 'OPTIONS':
      try:
        jwt_token = self.request.headers.get('authorization', None)
        decoded = jwt.decode(jwt_token,JWT_SECRET,JWT_ALGORITHM)
        if decoded['key'] != 'token_admin_super_secreto':
          raise Exception('token invalido!')
      except Exception as err: 
        self.set_status(400)
        self.finish({'message': str(err)})
