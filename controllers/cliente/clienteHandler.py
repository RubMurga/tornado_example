import tornado.web
import json
import traceback

from datetime import datetime
from models.user_model import UserModel
from tornado import gen
from controllers.util.UtilProject import UtilProject
from pyfcm import FCMNotification
import smtplib
import collections
from mimesis import Person
from random import randint

class ClienteHandlerNoFB(tornado.web.RequestHandler):  
  def set_default_headers(self):
    self.set_header("Access-Control-Allow-Origin", "*")
    self.set_header("Access-Control-Allow-Headers", "x-requested-with")
    self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
  @gen.coroutine
  def post(self):
    # nombre, apellido_paterno, apellido_materno, email, contraseña, sexo, no_hijos, estado_civil, fecha_nacimiento, direccion? 
    client = json.loads(self.request.body.decode('utf-8'))
    __model = UserModel()
    try:
      if 'facebook' in client:
        # id, apellido paterno, email, nombre
        registered = yield __model.check_registered_client(client['email'])
        if registered:
          self.set_status(200)
          self.write({'message': True})
        else:
          register = yield __model.register_client_by_facebook(client)
          self.set_status(200)
          self.write({'message': False})
      else:
        registered = yield __model.check_registered_client(client['email'])
        if registered:
          raise Exception('Ese email ya está registrado.')
        status, message = yield __model.register_client_persona_table(client)
        if status == 400:
          raise Exception(message)        
        self.set_status(status)
        self.write({'message': message})
    except Exception as err:
      self.set_status(400)
      print(err)
      traceback.print_exc()
      self.write({'message' : str(err)}) 
    self.finish()

class ClienteLogInHandler(tornado.web.RequestHandler):
  def set_default_headers(self):
    self.set_header("Access-Control-Allow-Origin", "*")
    self.set_header("Access-Control-Allow-Headers", "x-requested-with")
    self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
  
  @gen.coroutine
  def post(self):
    try:
      user_model = UserModel()
      util = UtilProject()
      __mimesis_person = Person('es')
      data = json.loads(self.request.body.decode('utf-8'))
      found = yield user_model.find_user_by_email_password(data['email'], data['password'])
      if not found:
        raise Exception('Usuario y/o contrasena incorrectos.')
      user_data = yield user_model.get_client_data_by_id(found)
      if not user_data['imagen']:
        user_data['imagen'] = __mimesis_person.avatar(size=256) 
      self.write({'user': user_data})
      self.finish()
    except Exception as error:
      self.set_status(400)
      print(error)
      self.write({'message' : str(error)}) 

class ClienteLocationHandler(tornado.web.RequestHandler):
  push_service = FCMNotification(api_key=UtilProject.serverFCMKey)
  def set_default_headers(self):
    self.set_header("Access-Control-Allow-Origin", "*")
    self.set_header("Access-Control-Allow-Headers", "x-requested-with")
    self.set_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
  def acked(self, err, msg):
    if err is not None:
      print("Failed to deliver message: {0}: {1}".format(msg.value(), err.str()))
    else:
      print("Message produced: {0}".format(msg.value()))
  
  @gen.coroutine
  def post(self):#Recibe {id_person : 1, fk_id_departament: 1, id_beacon: "", in: 1/0}
    data = json.loads(self.request.body.decode('utf-8'))
    print(data)
    self.finish()

class PermissionsHandler(tornado.web.RequestHandler):
  def set_default_headers(self):
    self.set_header("Access-Control-Allow-Origin", "*")
    self.set_header("Access-Control-Allow-Headers", "x-requested-with")
    self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
  
  @gen.coroutine
  def get(self, id_persona):
    try: 
      __model = UserModel()
      permissions = yield __model.get_client_permissions(id_persona)
      self.write({'permisos': permissions['permisos']})
      self.set_status(200)
    except Exception as error:
      self.set_status(400)
      self.write({'message' : str(error)})
  @gen.coroutine
  def post(self, id_persona):
    try:
      data = json.loads(self.request.body.decode('utf-8'))
      __model = UserModel()
      id_cliente = yield __model.get_cliente_id_from_persona_id(id_persona)
      if not id_cliente: 
        raise Exception('Error al encontrar al cliente')
      permissions_updated = yield __model.update_client_permissions(id_cliente, data)
      if not permissions_updated:
        raise Exception('No se han podido actualizar tus permisos')
      self.set_status(200)
      self.write({'message': 'Permisos actualizados correctamente'})

    except Exception as error:
      self.set_status(400)
      self.write({'message' : str(error)})

class LikesHandler(tornado.web.RequestHandler):
  def set_default_headers(self):
    self.set_header("Access-Control-Allow-Origin", "*")
    self.set_header("Access-Control-Allow-Headers", "x-requested-with")
    self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
  
  @gen.coroutine
  def get(self, id_persona):
    try: 
      __model = UserModel()
      likes = yield __model.get_client_likes(id_persona)
      self.write({'likes' :likes })
      self.set_status(200)
    except Exception as error:
      self.set_status(400)
      self.write({'message' : str(error)})
  
  @gen.coroutine
  def post(self, id_persona):
    try:
      data = json.loads(self.request.body.decode('utf-8'))
      __model = UserModel()
      id_cliente = yield __model.get_cliente_id_from_persona_id(id_persona)
      if not id_cliente: 
        raise Exception('Error al encontrar al cliente')
      likes_updated = yield __model.update_client_likes(id_cliente, data)
      if not likes_updated:
        raise Exception('No se han podido actualizar tus gustos')
      self.set_status(200)
      self.write({'message': 'Gustos actualizados correctamente'})
    except Exception as error:
      self.set_status(400)
      print("Error :" + str(error))
      self.write({'message' : str(error)})

class PasswordHandler(tornado.web.RequestHandler):
  @gen.coroutine
  def post(self):
    gmail_user = 'ruben.murga.d@gmail.com'
    gmail_password = 'aqolqmlxpyvfzcpy'
    try:
      user = UserModel()
      data = json.loads(self.request.body.decode('utf-8'))
      password = yield user.get_password_by_email(data['email'])
      if not password:
        raise Exception('No se ha encontrado un usuario registrado con ese correo.')
      server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
      server.login(gmail_user, gmail_password)
      sent_from = gmail_user
      to = [data['email']]
      subject = 'Olvidaste tu contrasenia de Sapphire?'
      body = "Hola! \n Tu contrasenia es: %s \n Esperamos volver a verte pronto!" % password
      email_text = """\  
        From: %s  
        To: %s  
        Subject: %s

        %s
        """ % (sent_from, ", ".join(to), subject, body)
      server.sendmail(sent_from, to, email_text)
      server.close()
      self.set_status(200)
      self.write({'message' : 'Tu contraseña está en tu correo, esperamos verte pronto!'})
    except Exception as error:
      self.set_status(400)
      self.write({'message' : error})

class BenefictsHandler(tornado.web.RequestHandler):
  @gen.coroutine
  def get(self, id_persona):
    try:
      user_model = UserModel()
      id_cliente = yield user_model.get_cliente_id_from_persona_id(id_persona)
      if not id_cliente:
        raise Exception('Cliente no encontrado.')
      beneficts = yield user_model.get_client_beneficts(id_cliente)
      print(len(beneficts))
      if len(beneficts) is 0:
        raise Exception('No tienes ningun beneficio.')
      self.set_status(200)
      self.write({'beneficts' : beneficts})
    except Exception as error:
      self.set_status(400)
      self.write({'message' : str(error)})

class AchievementsHandler(tornado.web.RequestHandler):
  @gen.coroutine
  def get(self, id_persona):
    try:
      user_model = UserModel()
      id_cliente = yield user_model.get_client_id_by_person_id(id_persona)
      if not id_cliente:
        raise Exception('Cliente no encontrado.')
      achievements = yield user_model.get_client_achievements(id_cliente)
      if len(achievements) is 0:
        raise Exception('No tienes ningun logro.')
      self.set_status(200)
      self.write({'achievements' : achievements})
    except Exception as error:
      self.set_status(400)
      self.write({'message' : str(error)})

class InformationHandler(tornado.web.RequestHandler):
  def set_default_headers(self):
    self.set_header("Access-Control-Allow-Origin", "*")
    self.set_header("Access-Control-Allow-Headers", "x-requested-with")
    self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
  
  @gen.coroutine
  def get(self, id_persona):
    try: 
      __model = UserModel()
      client_information = yield __model.get_client_information(id_persona)
      self.write({'informacion' :client_information })
      self.set_status(200)
    except Exception as error:
      self.set_status(400)
      self.write({'message' : str(error)})
      
  @gen.coroutine
  def post(self, id_persona):
    try:
      data = json.loads(self.request.body.decode('utf-8'))
      __model = UserModel()
      id_cliente = yield __model.get_cliente_id_from_persona_id(id_persona)
      if not id_cliente: 
        raise Exception('Error al encontrar al cliente')
      information_updated = yield __model.update_client_information(id_persona, data)
      if not information_updated:
        raise Exception('No se ha podido actualizar tu información personal.')
      self.set_status(200)
      self.write({'message': 'Datos personales actualizados correctamente'})
    except Exception as error:
      import traceback
      traceback.print_exc()
      self.set_status(400)
      print("Error :" + str(error))
      self.write({'message' : str(error)})

class TokenFCMHandler(tornado.web.RequestHandler):
  def set_default_headers(self):
    self.set_header("Access-Control-Allow-Origin", "*")
    self.set_header("Access-Control-Allow-Headers", "x-requested-with")
    self.set_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
  
  @gen.coroutine
  def post(self):
    token = json.loads(self.request.body.decode('utf-8'))
    __model = UserModel()
    status, message = yield __model.persona_update_token_fcm(token['id_persona'], token['token']) 
    self.set_status(status)
    self.finish({'message' : message})

class RequestHelpHandler(tornado.web.RequestHandler):
  push_service = FCMNotification(api_key=UtilProject.serverFCMKey)
  def set_default_headers(self):
    self.set_header("Access-Control-Allow-Origin", "*")
    self.set_header("Access-Control-Allow-Headers", "x-requested-with")
    self.set_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
  
  @gen.coroutine
  def post(self, id_persona, id_beacon):
    __model = UserModel()
    user_data = yield __model.get_client_location_by_id(id_persona, id_beacon)
    data_message = {
      'id_person': id_persona,
      'likes': user_data['gustos'],
      'score': user_data['puntaje'],
      'since': user_data['fecha_registro'].strftime('%d/%m/%Y'),
      'level': user_data['nivel'],
      'image': user_data['imagen'] if user_data['imagen'] is not None else UtilProject.defualtImage,
      'sex': user_data['sexo'] if user_data['sexo'] is not None else "",
      'civil_status': user_data['estado_civil'] if user_data['permisos']['estado_civil'] else "",
      'department': user_data['depto'],
      'floor': user_data['planta'],
      'sons': int(user_data['no_hijos']) if user_data['permisos']['hijos'] else 0,
      'age': int(user_data['edad']) if user_data['permisos']['edad'] else 0,
      'position': user_data['posicion_geografica'],
      'id_beacon': id_beacon,
      'time': (datetime.now()).strftime('%d/%m/%Y a las %H:%M:%S'),
      'title' : UtilProject.notify['help']['title'],
      'body' : UtilProject.notify['help']['body'],
      'id' : randint(1, 9999999),
      'show' : 1
    }
    if "permisos" in data_message:
      del data_message["permisos"]
    result = self.push_service.notify_topic_subscribers(topic_name='department{0}'.format(user_data['id_departamento']),data_message=data_message)
    self.set_status(200)
    self.finish({'message' : "Notificación enviada correctamente."})