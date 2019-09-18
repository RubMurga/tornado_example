import json
from tornado import gen
from controllers.util.UtilProject import UtilProject
from models.user_model import UserModel
from models.product_model import ProductModel
from models.store_model import StoreModel
import pandas as pd
import tornado.web
import traceback
import numpy as np
from controllers.admin.ClusterHandler import number_of_clusters
import os
from controllers.vendedor.auth import AuthHandler
import random
import math

class CollaborativeFiltering():
  def __init__(self, iterations, lamb):
    self.__iterations = iterations
    self.__current_it = 0
    self.__alpha = 0.01
    self.__lambda = lamb
    self.__mu = {}
    self.__params = 0
  
  @gen.coroutine
  def predict(self, client, product_user_matix):
    predictions = []
    for product in product_user_matix:
      try:
        if not product[str(client['id_cliente'])]['rated']: #agregamos solo productos que no han sido comprados
          predictions.append({'id_producto': product['id_producto'], 'score' : np.matmul(client['theta'].T, product['x'])[0][0] + self.__mu[str(product['id_producto'])]})
      except:
        pass
    return predictions
  @gen.coroutine
  def CF_algorithm(self, people, product_user_matrix):
    x = []
    y = []
    people, product_user_matrix = yield self.initialize_thetas_and_features(people,product_user_matrix) #inicializamos thetas y xs
    product_user_matrix = yield self.mean_normalization(people,product_user_matrix) #agregamos la mean normalización
    for self.__current_it in range(1, self.__iterations):
      J = yield self.compute_error_function(people, product_user_matrix) #calculamos la funcion de error
      people_2 = yield self.thetas_gradient(people, product_user_matrix) #actualizamos thetas
      product_user_matrix_2 = yield self.xs_gradient(people,product_user_matrix) #actualizamos x's
      #graficacion
      x.append(self.__current_it)
      y.append(float(J))
      people = people_2
      product_user_matrix = product_user_matrix_2
    return people, product_user_matrix, x,y
  
  @gen.coroutine
  def mean_normalization(self, people, product_user_matix):
    user_model = UserModel()
    for product in product_user_matix:
      rated = 0
      rated_sum = 0
      for person in people:
        person_score = product[str(person['id_cliente'])]
        if person_score['rated']:
          rated = rated +1
          rated_sum = rated_sum + person_score['score']
      
      if rated > 0:
        mean = rated_sum/rated
        #self.__mu.append({'id_producto' : product['id_producto'], 'mean' : mean})
        self.__mu[str(product['id_producto'])] = mean
        saved = yield user_model.save_product_mu(product['id_producto'], mean)
        for person in people:
          person_score = product[str(person['id_cliente'])]
          if person_score['rated']:
            person_score['score'] = person_score['score']- mean
            product[str(person['id_cliente'])] = person_score    
    return product_user_matix

  @gen.coroutine
  def thetas_gradient(self, people, product_user_matix):
    people2 = people
    for person in people2:
      for product in product_user_matix:
        person_score = product[str(person['id_cliente'])]
        if person_score['rated']:
          person['theta'] = person['theta'] - (self.__alpha)*((np.matmul(person['theta'],product['x'].T)[0][0]  - person_score['score']))* product['x'] #+ self.__lambda*person['theta']
    return people2
  
  @gen.coroutine
  def xs_gradient(self, people, product_user_matix):
    product_user_matrix_2 = product_user_matix
    for person in people:
      for product in product_user_matrix_2:
        person_score = product[str(person['id_cliente'])]
        if person_score['rated']:
          product['x'] = product['x'] - (self.__alpha)*((np.matmul(person['theta'],product['x'].T)[0][0] - person_score['score']))* person['theta'] #+ self.__lambda*product['x']
    return product_user_matrix_2
  
  @gen.coroutine
  def compute_error_function(self, people, product_user_matix):
    error = 0
    for person in people:
      for product in product_user_matix:
        person_score = product[str(person['id_cliente'])]
        if person_score['rated']:
          error = error + 1/(len(people) * len(product_user_matix))*( (np.matmul(person['theta'],product['x'].T) - person_score['score'])[0][0])**2  + (self.__lambda/len(product_user_matix))*(product['x']*product['x'].T)[0][0] +(self.__lambda/len(people))*(person['theta']*person['theta'].T)[0][0] 
    return error
  @gen.coroutine
  def initialize_thetas_and_features(self,people, product_user_matix):
    store_model = StoreModel()
    likes = yield store_model.get_all_likes()
    likes_len = len(likes) + self.__params
    for person in people:
      person['theta'] = list()
      for like in likes:
        if like['nombre'] in person['gustos']:
          person['theta'].append(0.4)
        else:
          person['theta'].append(random.random())
      for theta in range(0,self.__params):
        person['theta'].append(random.random())
      person['theta'] = np.array([person['theta']], dtype=np.float)
    for product in product_user_matix:
      product['x'] = np.random.rand(1, likes_len)
      product['x'] = product['x'].astype(np.float)
    return people, product_user_matix
  
  @gen.coroutine
  def CF_algorithm_cross(self, people, product_user_matrix_original):
    x = []
    y = []
    y_cross = []
    data_points = [10,20,40,80,100, 500, 1000, 2000, 3000, 5000, 8000, 10000]
    for num_data in data_points:
      product_user_matrix = product_user_matrix_original[:num_data]

      train_cota = int(len(product_user_matrix) * .70)
      product_user_matrix_cross = product_user_matrix[train_cota:]
      product_user_matrix = product_user_matrix[:train_cota]

      people, product_user_matrix_cross = yield self.initialize_thetas_and_features(people,product_user_matrix_cross) #inicializamos thetas y xs
      product_user_matrix_cross = yield self.mean_normalization(people,product_user_matrix_cross) #agregamos la mean normalización

      people, product_user_matrix = yield self.initialize_thetas_and_features(people,product_user_matrix) #inicializamos thetas y xs
      product_user_matrix = yield self.mean_normalization(people,product_user_matrix) #agregamos la mean normalización
      
      for self.__current_it in range(1, self.__iterations):
        product_user_matrix_2 = yield self.xs_gradient(people,product_user_matrix) #actualizamos x's
        people_2 = yield self.thetas_gradient(people, product_user_matrix) #actualizamos thetas
        J = yield self.compute_error_function(people, product_user_matrix) #calculamos la funcion de error

        # cross validation
        people = people_2
        product_user_matrix = product_user_matrix_2
      x.append(num_data)
      y.append(float(J))
      for self.__current_it in range(1, self.__iterations):
        J_cross = yield self.compute_error_function(people, product_user_matrix_cross) #calculamos la funcion de error
      y_cross.append(float(J_cross))
    return people, product_user_matrix, x,y, y_cross

class RecomAuxClass():
  def get_product_score(self, id_producto, person_products):
    for product in person_products:
      if product['fk_id_producto'] == id_producto:
        return {'score': product['calificacion_producto'], 'rated' : True}
    return {'score': 0, 'rated' : False}
  
  def get_favourite_score(self, id_producto, persona_favourites):
    for product in persona_favourites:
      if product['fk_id_producto'] == id_producto:
        return {'score': 5, 'rated' : True}
    return None
  
  def create_user_article_matrix(self, people, products):
    for product in products:
      for person in people:
        product_purchase_score = self.get_product_score(product['id_producto'], person['purchases'])
        favourite_score_product = self.get_favourite_score(product['id_producto'], person['favs'])
        product[str(person['id_cliente'])] = favourite_score_product if favourite_score_product else product_purchase_score
        
    for person in people:
      del person['purchases']
      del person['favs']
  
  def get_user(self, people, id_cliente):
    for person in people:
      if id_cliente == person['id_cliente']:
        return person

#predicciones todos
class RecomHandler(tornado.web.RequestHandler):
  @gen.coroutine
  def get(self):
    try: 
      CF = CollaborativeFiltering(10,0.0000000005)
      recom_class = RecomAuxClass()
      user_model = UserModel()
      product_model = ProductModel()
      util = UtilProject()
      people = yield user_model.get_all_people() # obtenemos personas con mismo cluster
      people = yield user_model.get_purchases_and_favs_by_people(people) # obtenemos compras y favoritos hechas por los clientes
      products = yield product_model.get_all_products_recom() # obtenemos los productos del departamento
      #products = yield product_model.get_products_by_department(1)
      recom_class.create_user_article_matrix(people, products) # creamos matriz usuario articulo
      print('Matrices creadas...\n')
      print('ejecutando algoritmo...')
      #people, products,x,y = yield CF.CF_algorithm_cross(people, products) #obtenemos todos los usuarios con sus pesos y los productos con sus xs
      people, products,x,y, y_cross = yield CF.CF_algorithm_cross(people, products) #obtenemos todos los usuarios con sus pesos y los productos con sus xs
      dirname = os.path.dirname(__file__)
      for person in people:
        client_obj = recom_class.get_user(people, person['id_cliente']) #obtenemos el usuario
        recommendations = yield CF.predict(client_obj, products) #obtenemos las prediccions
        recommendations = sorted(recommendations, key=lambda k: k['score'], reverse=True)  #ordenamos de mayor a menor
        recommendations = recommendations[:100] #seleccionamos sólo 10
        recommendations = yield product_model.get_recommendations_specific_info(recommendations) #obtenemos los datos de cada recomendacion
        recommendations = util.cast_numeric_to_string(recommendations, 'precio_venta')          
        recommendations = util.cast_numeric_to_string(recommendations, 'score')
        filename = os.path.join(dirname, 'recoms/'+str(person['id_cliente'])+'.json')
        file = open(filename,'w')
        json.dump(recommendations, file)
        file.close()
        save_client = yield user_model.save_client_thetas(client_obj)
      save_xs = yield user_model.save_product_xs(products)
      self.write({'x': x, 'y': y, 'y_cross': y_cross})
    except Exception as error:
      traceback.print_tb(error)
      self.set_status(400)
      self.write({'message' : str(error)})
    

#preddciones globales por usuario

class ClientRecomHandler(tornado.web.RequestHandler):
  @gen.coroutine
  def get(self, id_persona):
    try:
      dirname = os.path.dirname(__file__)
      user_model = UserModel()
      id_cliente = yield user_model.get_client_id_by_person_id(id_persona)
      if not id_cliente:
        raise Exception('Cliente no encontrado')
      try:
        filename = os.path.join(dirname, 'recoms/'+str(id_cliente)+'.json')
        file = open(filename,'r')
        file = file.read()
        recom = json.loads(file)
      except:
        product_model = ProductModel()
        util = UtilProject()
        recom = yield product_model.get_default_recommendations()
        recom = util.cast_numeric_to_string(recom, 'precio_venta')          
        recom = util.cast_numeric_to_string(recom, 'score')
      self.set_status(200)
      self.write({'recommendations': recom})
    except Exception as error:
      self.set_status(400)
      self.write({'message' : str(error)})
    

#predicciones por deparartamento
class RecomHandlerDepartment(AuthHandler):
  @gen.coroutine
  def get(self, id_usuario, id_departamento):
    try:
      util = UtilProject()
      user_model = UserModel()
      product_model = ProductModel()
      products = yield product_model.get_products_by_department(id_departamento)
      id_cliente = yield user_model.get_client_id_by_person_id(id_usuario)
      if not id_cliente:
        raise Exception('Cliente no encontrado')
      client = yield user_model.get_client_thetas(id_cliente)
      if client['thetas']:
        client['theta'] = np.array([client['thetas']], dtype=np.longdouble)
        del client['thetas']
        for product in products:
          product['x'] = np.array([product['x']], dtype=np.longdouble)
        client = yield user_model.get_purchases_and_favs_by_client(client)
        favs = client['favs']
        purchases = client['purchases']
        recommendations = []
        for product in products:
          if not any(d['fk_id_producto'] == product['id_producto'] for d in favs) or not any(d['fk_id_producto'] == product['id_producto'] for d in purchases):
            recommendations.append({'id_producto': product['id_producto'], 'score' : np.matmul(client['theta'].T, product['x'])[0][0] + product['mu']})
        recommendations = yield product_model.get_recommendations_specific_info(recommendations) #obtenemos los datos de cada recomendacion
        recommendations = sorted(recommendations, key=lambda k: k['score'], reverse=True)  #ordenamos de mayor a menor
        recommendations = recommendations[:15]
      else: 
        recommendations = yield product_model.get_default_recommendations_department(id_departamento)
      recommendations = util.cast_numeric_to_string(recommendations, 'precio_venta')          
      recommendations = util.cast_numeric_to_string(recommendations, 'score')
      self.set_status(200)
      self.write({'recommendations': recommendations})
    except Exception as error: 
      import traceback
      traceback.print_exc()
      self.set_status(400)
      self.write({'message' : str(error)})
    """
    try: 
      CF = CollaborativeFiltering(30,0.029)
      recom_class = RecomAuxClass()
      user_model = UserModel()
      product_model = ProductModel()
      util = UtilProject()
      id_cliente = yield user_model.get_cliente_id_from_persona_id(id_usuario) # obtenemos el id cliente
      people = yield user_model.get_cluster_people_by_user(id_usuario) # obtenemos personas con mismo cluster
      people = yield user_model.get_purchases_and_favs_by_people(people) # obtenemos compras y favoritos hechas por los clientes
      if util.isInt(id_departamento):
        products = yield product_model.get_products_by_department(id_departamento) # obtenemos los productos del departamento
      else: 
        products = yield product_model.get_all_products_recom() # obtenemos los productos del departamento
      recom_class.create_user_article_matrix(people, products) # creamos matriz usuario articulo
      people, products,x,y = yield CF.CF_algorithm(people, products) #obtenemos todos los usuarios con sus pesos y los productos con sus xs
      client_obj = recom_class.get_user(people, id_cliente) #obtenemos el usuario
      #save_client = yield user_model.save_client_thetas(client_obj)
      save_xs = yield user_model.save_product_xs(products)
      recommendations = yield CF.predict(client_obj, products) #obtenemos las prediccions
      recommendations = sorted(recommendations, key=lambda k: k['score'], reverse=True)  #ordenamos de mayor a menor
      recommendations = recommendations[:10] #seleccionamos sólo 10
      recommendations = yield product_model.get_recommendations_specific_info(recommendations) #obtenemos los datos de cada recomendacion
      recommendations = util.cast_numeric_to_string(recommendations, 'precio_venta')
      recommendations = util.cast_numeric_to_string(recommendations, 'score')
      self.write({'recommendations': recommendations})
    except Exception as error:
      traceback.print_tb(error)
      self.set_status(400)
      self.write({'message' : str(error)})
    """
    
