from controllers.admin.auth import AuthHandler
import json
from tornado import gen
from controllers.util.UtilProject import UtilProject
from models.user_model import UserModel
from models.store_model import StoreModel
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
number_of_clusters = 3
useless_colums = [
      'nombre', 
      'apellido_paterno',
      'apellido_materno',
      'email',
      'contrasena',
      'fk_id_direccion',
      'telefono',
      'imagen',
      'id_cliente',
      'fk_id_persona',
      'gustos',
      'grupo',
      'posicion',
      'permisos', 
    ]
categorical_colums = [
  'sexo',
  'estado_civil'
]

important_features = [
  'fecha_nacimiento', 'fecha_registro', 'fk_id_nivel', 'Computadoras', 'Celulares y tablets',
  'TV y video', 'Cámaras', 'Audio', 'Videojuegos', 'Drones y radio control', 'Wearables',
  'Instrumentos musicales', 'Hogar inteligente', 'Películas y series', 'Autos y motos',
  'sexo_M', 'estado_civil_S', 'estado_civil_c', 'ultima_actualizacion_nivel'
  ]


class ClusterAux():
  def fill_na_numeric(self, dataframe, keys):
    for key in keys:
      dataframe[key] = dataframe[key].fillna(dataframe[key].mean())
    
    return dataframe
  
  def create_likes_matrix(self, likes):
    like_matrix = dict()
    for like in likes:
      like_matrix[like['nombre']] = []
    return like_matrix
  
  def fill_likes_matrix(self, users, like_matrix, likes):
    for like in likes:
      for user in users:
        if not user['gustos']:
          like_matrix[like['nombre']].append(0)
        else:
          if like['nombre'] in user['gustos']:
            like_matrix[like['nombre']].append(1)
          else:
            like_matrix[like['nombre']].append(0)
    return like_matrix
  
  def add_like_matrix_to_dataframe(self, dataframe, like_matrix, likes):
    for like in likes:
      dataframe[like['nombre']] = like_matrix[like['nombre']]
    return dataframe
  
  @gen.coroutine
  def get_stored_cluster_info(self):
    model = UserModel()
    users = yield model.get_client_cluster_info()
    return users
  
  @gen.coroutine
  def get_stats_cluster(self):
    model = UserModel()
    self.__util = UtilProject()
    self.__store_model = StoreModel()
    cluster_info_list = []
    for cluster in range(0,number_of_clusters):
      data = yield model.get_cluster_info(cluster)
      data = self.__util.get_years_from_now(data,['fecha_nacimiento', 'fecha_registro', 'ultima_actualizacion_nivel'])
      data = self.__util.days_to_years(data, ['fecha_nacimiento'])
      data = self.__util.days_to_months(data, ['fecha_registro'])
      data = self.__util.days_to_months(data, ['ultima_actualizacion_nivel'])
      likes = yield self.__store_model.get_all_likes()
      like_matrix = self.create_likes_matrix(likes)
      like_matrix_filled = self.fill_likes_matrix(data, like_matrix, likes)
      dataframe = pd.DataFrame(data)
      dataframe = self.add_like_matrix_to_dataframe(dataframe, like_matrix_filled, likes)

      dataframe = self.fill_na_numeric(dataframe, ['fecha_nacimiento', 'fecha_registro', 'ultima_actualizacion_nivel'])
      dataframe = dataframe.drop(columns = useless_colums)
      cluster_info = dict()
      cluster_info['label'] = str(cluster)
      cluster_info['edad_promedio'] = str(dataframe['fecha_nacimiento'].mean())
      cluster_info['meses_registro'] = str(dataframe['fecha_registro'].mean())
      cluster_info['estado_civil'] = dict(dataframe['estado_civil'].value_counts())
      cluster_info['sexo'] = dict(dataframe['sexo'].value_counts())
      self.__util.int64_to_int(cluster_info['estado_civil'])
      self.__util.int64_to_int(cluster_info['sexo'])
      for like in likes:
        cluster_info[like['nombre']] = dict(dataframe[like['nombre']].value_counts())
        cluster_info[like['nombre']] = self.__util.int64_to_int(cluster_info[like['nombre']])        
      cluster_info_list.append(cluster_info)      
    return cluster_info_list

class ClusterHandler(AuthHandler):
  @gen.coroutine
  def get(self):
    self.__cluster_class = ClusterAux()
    self.__util = UtilProject()
    self.__model = UserModel()
    self.__store_model = StoreModel()
    data = yield self.__model.get_users_data_for_cluster()
    data = self.__util.get_years_from_now(data,['fecha_nacimiento', 'fecha_registro', 'ultima_actualizacion_nivel'])
    data = self.__util.days_to_years(data, ['fecha_nacimiento'])
    data = self.__util.days_to_months(data, ['fecha_registro', 'ultima_actualizacion_nivel'])
    data = self.__util.split_ages_intervals(data, ['fecha_nacimiento'])
    likes = yield self.__store_model.get_all_likes()
    like_matrix = self.__cluster_class.create_likes_matrix(likes)
    like_matrix_filled = self.__cluster_class.fill_likes_matrix(data, like_matrix, likes)
    dataframe = pd.DataFrame(data)
    dataframe = self.__cluster_class.add_like_matrix_to_dataframe(dataframe, like_matrix_filled, likes)
    
    dataframe = self.__cluster_class.fill_na_numeric(dataframe, ['fecha_nacimiento', 'fecha_registro', 'ultima_actualizacion_nivel'])
    dataframe = pd.get_dummies(dataframe, columns= categorical_colums, drop_first= True)
    dataframe = dataframe.drop(columns=useless_colums)
    cluster = KMeans(n_clusters=number_of_clusters)
    dataframe['cluster'] = cluster.fit_predict(dataframe[important_features])
    pca = PCA(n_components=2) #2 dimensiones
    dataframe['x'] = pca.fit_transform(dataframe[important_features])[:,0]
    dataframe['y'] = pca.fit_transform(dataframe[important_features])[:,1]
    for index, row in dataframe.iterrows():
      id_cliente = yield self.__model.get_cliente_id_from_persona_id(int(row['id_persona']))
      if id_cliente:
        yield self.__model.insert_client_group(id_cliente, row['x'], row['y'], int(row['cluster']))
    users = yield self.__cluster_class.get_stored_cluster_info()
    cluster_stats = yield self.__cluster_class.get_stats_cluster()
    self.write({'users': users, 'number_of_clusters': number_of_clusters, 'info_clusters': cluster_stats})

class InitialClusterHandler(AuthHandler):
  @gen.coroutine
  def get(self):
    self.__cluster_class = ClusterAux()
    users = yield self.__cluster_class.get_stored_cluster_info()
    cluster_stats = yield self.__cluster_class.get_stats_cluster()
    self.write({'users': users, 'number_of_clusters': number_of_clusters, 'info_clusters': cluster_stats})
    