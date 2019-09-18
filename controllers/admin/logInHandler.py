from controllers.util.UtilProject import UtilProject
from models.user_model import UserModel
import tornado.web 
import json 
from tornado import gen
import jwt
JWT_SECRET = 'resttornadosupersecretkey'
JWT_ALGORITHM = 'HS256'

class LogInHandler(tornado.web.RequestHandler):
  
  def set_default_headers(self):
    print("setting headers!!!")
    self.set_header("Access-Control-Allow-Origin", "*")
    self.set_header("Access-Control-Allow-Headers", "x-requested-with, Content-Type")
    self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

  @gen.coroutine  
  def post(self):
    data = json.loads(self.request.body.decode('utf-8'))
    try:
      if 'user' in data and 'password' in data:
        __model = UserModel()
        correct_credentials = yield __model.administrador_login(data['user'], data['password'])
        if not correct_credentials:
          raise Exception('Usuario o contraseña incorrectos')
        user_data = yield __model.empleado_login_data(data['user'])
        payload = {'key' : 'token_admin_super_secreto', 'id_user' : user_data['id_empleado']}
        jwt_token = jwt.encode(payload,JWT_SECRET,JWT_ALGORITHM)
        json_response = {
          'token': jwt_token.decode('utf-8'),
          'name': user_data['nombre'],
          'shop_name': user_data['nombre_tienda'],
          'shop_id': user_data['id_tienda'],
          'department_name': user_data['nombre_departamento'],
          'departament_id': user_data['id_departamento'],
          'pat_surname': user_data['apellido_paterno'],
          'mat_surname': user_data['apellido_materno'],
          'image' : user_data['imagen'],
          'email': user_data['email'],
          'id_administrador': user_data['id_empleado']
        }
        self.set_status(200)
        self.finish(json_response)
      else: 
        raise Exception('Favor de cumplir los campos necesarios')
    except Exception as err:   
      self.set_status(400)
      self.finish(json.dumps({'message': str(err)}))
  
  def options(self):
    # no body
    self.set_status(200)
    self.finish()

