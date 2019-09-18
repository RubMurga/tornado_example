from controllers.vendedor.auth import AuthHandler
import tornado.web
import json
from models.user_model import UserModel
from models.product_model import ProductModel
from tornado import gen
from models.user_model import UserModel
from models import product_model
from datetime import datetime
from pyfcm import FCMNotification
from controllers.util.UtilProject import UtilProject
from random import randint
import traceback
from mimesis import Person


class VendedorHandler(AuthHandler):  
  @gen.coroutine
  def put(self):
    vendedor = json.loads(self.request.body.decode('utf-8'))
    __model = UserModel()
    status, message = yield __model.vendedor_update_info(self._user_id, vendedor) 
    self.set_status(status)
    self.finish({'message' : message})


# -- beacons
class VendedorClienteHandler(AuthHandler):
  settings = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'mygroup',
    'client.id': 'client-1',
    'enable.auto.commit': True,
    'session.timeout.ms': 6000,
    'default.topic.config': {'auto.offset.reset': 'smallest'}
  }
  def unique_clients(self, clients):
    uniques = []
    for client in clients:
      add = True
      for cli in list(uniques):
        if client['id_person'] == cli['id_person']:
          add = False
          dtClient = datetime.strptime(client['time'], '%d/%m/%Y a las %H:%M:%S')
          dtCli = datetime.strptime(cli['time'], '%d/%m/%Y a las %H:%M:%S')
          if dtClient > dtCli:
            add = True
            uniques.remove(cli)
      if add:
        uniques.append(client)
    return uniques

  def sort_by_score(self, data):
    try:
      return int(data['score'])
    except KeyError:
      return 0

  def set_default_headers(self):
    self.set_header("Access-Control-Allow-Origin", "*")
    self.set_header("Access-Control-Allow-Headers", "x-requested-with")
    self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
    
  @gen.coroutine
  def get(self, department): 
    self.finish()

# -- beacons
class VendedorClienteDetailsHandler(AuthHandler):
  def sort_by_total(self, data):
    try:
      return int(data['total'])
    except KeyError:
      return 0

  def set_default_headers(self):
    self.set_header("Access-Control-Allow-Origin", "*")
    self.set_header("Access-Control-Allow-Headers", "x-requested-with")
    self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
  
  @gen.coroutine
  def get(self, id_persona): 
    __model_user = UserModel()
    __model_product = ProductModel()
    categories = []
    purchases_stats = []
    favs = []
    permits =  yield __model_user.get_client_permits(id_persona)
    benefits =  yield __model_user.get_client_benefits(id_persona)
    if permits['compras']:
      purchases_stats = yield __model_user.get_client_purchases_stats_year(id_persona)
      cats = yield __model_user.get_client_most_purchased_categories(id_persona)
      for cat in cats:
        if cat['fk_id_padre_cat'] is not None:
          cat_pat = cat
          subcategories = []
          while cat_pat['fk_id_padre_cat'] is not None:
            cat_pat = yield __model_product.get_parent_categorie(cat_pat['id_categoria'])
            subcategories.append({
              'id_categorie': cat_pat['id_categoria'],
              'name': cat_pat['nombre']
            })
          if not any(d['id_categorie'] == cat_pat['id_categoria'] for d in categories):
            subcategories.remove({'id_categorie': cat_pat['id_categoria'],'name': cat_pat['nombre']})
            categories.append({
              'id_categorie': cat_pat['id_categoria'],
              'name': cat_pat['nombre'],
              'total': cat['total'],
              'subcategories': subcategories
            })
          else:
            for d in categories:
              if d['id_categorie'] == cat_pat['id_categoria']:
                d['total'] += cat['total']
                for sub in subcategories:
                  if not any(cat_sub['id_categorie'] == sub['id_categorie'] for cat_sub in d['subcategories']) and d['id_categorie'] != sub['id_categorie']:
                    d['subcategories'].append({
                      'id_categorie': sub['id_categorie'],
                      'name': sub['name']
                    })
        else: 
          categories.append({
            'id_categorie': cat['id_categoria'],
            'name': cat['nombre'],
            'total': cat['total'],
            'subcategories': []
          })
    if permits['favoritos']:
      favs = yield __model_user.get_client_favorite_products(id_persona)
    categories.sort(key=self.sort_by_total, reverse=True)
    print({'benefits' : benefits, 'categories': categories[:5], 'purchases_stats' : purchases_stats, 'favorites' : favs })
    self.write({'benefits' : benefits, 'categories': categories[:5], 'purchases_stats' : purchases_stats, 'favorites' : favs })
    self.finish()

class VendedorTokenFCMHandler(AuthHandler):  
  @gen.coroutine
  def post(self):
    token = json.loads(self.request.body.decode('utf-8'))
    __model = UserModel()
    status, message = yield __model.persona_update_token_fcm(token['id_persona'], token['token']) 
    self.set_status(status)
    self.finish({'message' : message})

class VendedorSendNotificationHandler(AuthHandler):  
  push_service = FCMNotification(api_key=UtilProject.serverFCMKey)

  @gen.coroutine
  def post(self, id_usuario, id_product):
    __model = UserModel()
    __model_product = product_model.ProductModel()
    tokens = yield __model.get_person_token_fcm(id_usuario)
    if tokens[0] is not None:
      data_message = yield __model_product.get_product_by_id(id_product)
      data_message['title'] = UtilProject.notify['sendRecommendation']['title']
      data_message['body']  = UtilProject.notify['sendRecommendation']['body']
      data_message['id']    = randint(1, 9999999)
      result = self.push_service.notify_single_device(registration_id=tokens[0], data_message=data_message)
      self.write({'message' : "Notificación enviada correctamente."})
    else:
      self.write({'message' : "No se ha podido enviar notificación al cliente por falta de token."})
    self.set_status(200)
    self.finish()

class VendedorGetClientInfo(AuthHandler):
  @gen.coroutine
  def post(self):
    users_data = []
    try:
      __user_model = UserModel()
      __mimesis_person = Person('es')
      users_ids = json.loads(self.request.body.decode('utf-8'))['users']
      print(users_ids)
      for user in users_ids:
        user_data = yield __user_model.get_client_feed_basic_info(user)
        user_data['imagen'] = __mimesis_person.avatar(size=256)
        users_data.append(user_data)
        self.set_status(200)
    except: 
      self.set_status(400)
    self.write({'payload' : users_data})
