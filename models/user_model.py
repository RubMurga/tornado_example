import queries
import models.db_connection
from tornado import gen
import datetime
from controllers.util.UtilProject import *
from models.product_model import ProductModel
import json

class UserModel(models.db_connection.Connection):
  def __init__(self):
    super(UserModel,self).__init__()
    self.__util = UtilProject()

  @gen.coroutine
  def get_client_id_by_person_id(self, id_persona):
    sql = 'SELECT cliente.id_cliente FROM cliente, persona WHERE cliente.fk_id_persona = persona.id_persona AND persona.id_persona = %s' % id_persona
    results = yield self._session.query(sql)
    if results:
      id_cliente = results.as_dict()
      results.free()
      return id_cliente['id_cliente']
    
    results.free()
    return False

  @gen.coroutine  
  def administrador_login(self, user, password): 
    sql = "SELECT empleado.nombre_usuario, persona.contrasena from empleado, persona where empleado.nombre_usuario = '%s' and persona.contrasena = '%s' and empleado.rol = 'a' LIMIT 1" % (user, password)
    results = yield self._session.query(sql)
    results_to_check = results.as_dict()
    results.free()
    if results_to_check == None or not results_to_check:
      return False
    return True
  
  @gen.coroutine  
  def vendedor_login(self, user, password): 
    sql = "SELECT empleado.nombre_usuario, persona.contrasena from empleado, persona where empleado.nombre_usuario = '%s' and persona.contrasena = '%s' and empleado.rol = 'v' LIMIT 1" % (user, password)
    results = yield self._session.query(sql)
    results_to_check = results.as_dict()
    results.free()
    if results_to_check == None or not results_to_check:
      return False
    return True

  @gen.coroutine
  def empleado_login_data(self, user):
    sql = """
      SELECT persona.id_persona, persona.token_fcm, empleado.id_empleado,empleado.nombre_usuario, persona.nombre, persona.apellido_paterno, persona.apellido_materno, persona.email, persona.imagen, departamento.id_departamento, departamento.nombre as nombre_departamento, tienda.id_tienda, tienda.nombre as nombre_tienda
      from persona, empleado, departamento, tienda
      WHERE persona.id_persona = empleado.fk_id_persona
      AND empleado.fk_id_departamento = departamento.id_departamento
      AND departamento.fk_id_tienda = tienda.id_tienda
      AND empleado.nombre_usuario = '%s'
    """ % user
    data = yield self._session.query(sql)
    data_to_return = data.as_dict()
    data.free()
    return data_to_return
  
  @gen.coroutine
  def vendedor_update_info(self, id_vendedor, vendedor):#@TODO: Actualizar el where porque id_persona ya se envia, ya no es id_empleado y agregar la contraseña 
    if vendedor['password'] != None:
      sql = """
        UPDATE persona set nombre = '%s', apellido_paterno = '%s', apellido_materno = '%s',contrasena = %s ,email = '%s' WHERE id_persona = (SELECT empleado.fk_id_persona from empleado WHERE id_empleado = %s)
      """ % (vendedor['name'], vendedor['pat_surname'], vendedor['mat_surname'], vendedor['password'], vendedor['email'], id_vendedor)
    else:
      sql = """
        UPDATE persona set nombre = '%s', apellido_paterno = '%s', apellido_materno = '%s',email = '%s' WHERE id_persona = (SELECT empleado.fk_id_persona from empleado WHERE id_empleado = %s)
      """ % (vendedor['name'], vendedor['pat_surname'], vendedor['mat_surname'], vendedor['email'], id_vendedor)
    results = yield self._session.query(sql)
    if results:
      results.free()
      return 200, 'Información actualizada correctamente'
    results.free()
    return 400, 'Hubo un problema al actualizar la información'

  ######################## CLIENTE
  @gen.coroutine
  def register_client_persona_table(self, client):
    
    sql = """
      INSERT INTO persona (nombre,apellido_paterno,apellido_materno,email,contrasena,estado_civil, fecha_nacimiento) 
      values('%s', '%s', '%s', '%s', '%s', '%s', '%s')
      """ % (client['nombre'], client['apellido_paterno'], client['apellido_materno'], client['email'], client['password'], client['estado_civil'], client['fecha_nacimiento'])

    register_client = yield self._session.query(sql)
    if not register_client:
      register_client.free()
      return 400, 'Ocurrió un error'
    register_client.free()
    client_information = yield self.register_client_cliente_table(client)
    if client_information == 200:
      return 200, 'Cliente creado correctamente'
    sql = "DELETE FROM persona where email = '%s'" % client['email']
    delete = yield self._session.query(sql)
    delete.free()
    return 400, 'Ocurrió un error'
    
  @gen.coroutine 
  def register_client_cliente_table(self, client):
    now = datetime.datetime.now()
    sql = """
      INSERT INTO CLIENTE (fk_id_persona,no_hijos, fk_id_nivel,ultima_actualizacion_nivel, fecha_registro, puntaje) 
      VALUES ((SELECT id_persona from persona where email = '%s'), %s, 1, '%s', '%s', 10)
    """  % (client['email'], client['no_hijos'], now, now)
    data = yield self._session.query(sql)
    if not data:
      data.free()
      return 400
    data.free()
    sql = """
    INSERT INTO logro_cliente (fk_id_cliente, fk_id_logro) VALUES 
    ((SELECT id_cliente FROM cliente, persona WHERE cliente.fk_id_persona = persona.id_persona AND persona.email = '%s'), 7)
    """ % client['email']
    data = yield self._session.query(sql)
    if not data: 
      return 400
    data.free()
    sql = """
    INSERT INTO logro_cliente (fk_id_cliente, fk_id_logro) VALUES 
    ((SELECT id_cliente FROM cliente, persona WHERE cliente.fk_id_persona = persona.id_persona AND persona.email = '%s'), 8)
    """ % client['email']
    data = yield self._session.query(sql)
    if not data: 
      data.free()
      return 400
    data.free()
    return 200
  
  @gen.coroutine
  def check_registered_client(self, email):
    sql = """
      SELECT persona.email from persona where email = '%s'
       """ % email
    registered_client = yield self._session.query(sql)
    if(registered_client):
      registered_client.free()
      return True
    registered_client.free()
    return False

  @gen.coroutine
  def get_client_location_by_id(self, id_person, id_beacon):
    sql = """
      SELECT cli.gustos, cli.puntaje, cli.fecha_registro, n.nombre AS nivel, per.estado_civil, per.imagen, per.sexo, d.id_departamento, d.nombre AS depto, d.planta, 
      dep_b.posicion_geografica, cli.no_hijos, EXTRACT(YEAR FROM age(per.fecha_nacimiento)) as edad, cli.permisos
      FROM cliente cli, persona per, nivel n, departamento d, departamento_beacon dep_b
      WHERE per.id_persona = cli.fk_id_persona  
      AND cli.fk_id_nivel = n.id_nivel
      AND dep_b.fk_id_departamento = d.id_departamento
      AND per.id_persona = {0}
      AND dep_b.id_beacon = '{1}'
       """.format(id_person, id_beacon)
    data = yield self._session.query(sql)
    data_return = data.as_dict()
    data.free()
    return data_return

  @gen.coroutine
  def get_client_permits(self, id_person):
    sql = """
      SELECT cli.permisos
      FROM cliente cli, persona per
      WHERE per.id_persona = cli.fk_id_persona 
      AND per.id_persona = {0}
       """.format(id_person)
    data = yield self._session.query(sql)
    permisos = (data.as_dict())['permisos']
    data.free()
    return permisos

  @gen.coroutine
  def get_client_favorite_products(self, id_person):
    sql = """
      SELECT pro.id_producto, pro.nombre as producto, pro.precio_venta, pro.stock, dep.nombre AS departamento,ti.nombre AS tienda, cat.nombre AS categoria, m.nombre AS marca, p.nombre AS promocion, fav.fecha_agregacion
      FROM favorito fav, cliente cli, persona per, producto pro, departamento dep, tienda ti, categoria cat, marca m, promocion p
      WHERE per.id_persona = cli.fk_id_persona 
      AND cli.id_cliente = fav.fk_id_cliente
      AND fav.fk_id_producto = pro.id_producto
      AND pro.fk_id_departamento = dep.id_departamento
      AND pro.fk_id_categoria = cat.id_categoria
      AND pro.fk_id_marca = m.id_marca
      AND pro.fk_id_promocion = p.id_promocion
      AND dep.fk_id_tienda = ti.id_tienda 
      AND per.id_persona = {0}
      ORDER BY fav.fecha_agregacion DESC
      LIMIT 5
       """.format(id_person)
    results = yield self._session.query(sql)
    results_to_return = results.items()
    results_to_return = self.__util.cast_numeric_to_string(results_to_return, 'precio_venta')
    results_to_return = self.__util.cast_datetime_to_string(results_to_return, ['fecha_agregacion'])
    results.free()
    return results_to_return

  @gen.coroutine
  def get_client_benefits(self, id_person):
    sql = """
      SELECT ben.descripcion as description, ben.porcentaje as percentage, ben.gratificacion as reward, ben.producto_gratis free_product
      FROM beneficio ben, nivel_beneficio nb, nivel n, cliente cli, persona per
      WHERE per.id_persona = cli.fk_id_persona 
      AND cli.fk_id_nivel = n.id_nivel
      AND n.id_nivel = nb.fk_id_nivel
      AND nb.fk_id_beneficio = ben.id_beneficio
      AND per.id_persona = {0}
       """.format(id_person)
    results = yield self._session.query(sql)
    results_to_return = results.items()
    results.free()
    return results_to_return

  @gen.coroutine
  def get_client_purchases_stats_year(self, id_person):
    sql = """
      SELECT EXTRACT(MONTH FROM com.fecha_compra) as month, EXTRACT(YEAR FROM com.fecha_compra) as year, COUNT(com) as total
      FROM compra com, cliente cli, persona per
      WHERE per.id_persona = cli.fk_id_persona 
      AND cli.id_cliente = com.fk_id_cliente
      AND per.id_persona = {0}
      AND com.fecha_compra > CURRENT_DATE - INTERVAL '6 months'
      GROUP BY EXTRACT(MONTH FROM com.fecha_compra), EXTRACT(YEAR FROM com.fecha_compra)
      ORDER BY EXTRACT(YEAR FROM com.fecha_compra)
       """.format(id_person)
    results = yield self._session.query(sql)
    results_to_return = results.items()
    results.free()
    return results_to_return

  @gen.coroutine
  def get_client_most_purchased_categories(self, id_person):
    sql = """
      SELECT cat.id_categoria, cat.nombre, COUNT(cat) as total, cat.fk_id_padre_cat
      FROM compra com, cliente cli, persona per, producto pro, categoria cat
      WHERE per.id_persona = cli.fk_id_persona 
      AND cli.id_cliente = com.fk_id_cliente
      AND com.fk_id_producto = pro.id_producto
      AND pro.fk_id_categoria = cat.id_categoria
      AND com.fecha_compra > CURRENT_DATE - INTERVAL '6 months'
      AND per.id_persona = {0}
      GROUP BY cat.id_categoria
       """.format(id_person)
    results = yield self._session.query(sql)
    results_to_return = results.items()
    results.free()
    return results_to_return

  @gen.coroutine
  def register_client_by_facebook(self, client):
    sql = """
      INSERT INTO persona(id_persona,nombre,apellido_paterno, apellido_materno, email, contrasena, estado_civil) 
      VALUES (%s, '%s', '%s', 'sinapellido', '%s', 'sincontrasena', 'S' )
    """ % (client['id'], client['nombre'], client['apellido_paterno'], client['email'])
    data = yield self._session.query(sql)
    if data: 
      data.free()
      client['no_hijos'] = 0
      client_information = yield self.register_client_cliente_table(client)
      if client_information:
        client_information.free()
        return True
  
  ############### CLUSTER
  @gen.coroutine
  def get_users_data_for_cluster(self):
    sql = 'SELECT persona.*, cliente.* from persona, cliente WHERE persona.id_persona = cliente.fk_id_persona'
    data = yield self._session.query(sql)
    data_to_return = data.items()
    data.free()
    return data_to_return
  @gen.coroutine
  def get_cliente_id_from_persona_id(self, id_persona):
    sql = 'SELECT cliente.id_cliente FROM persona, cliente WHERE persona.id_persona = cliente.fk_id_persona AND persona.id_persona = %s' % id_persona
    id = yield self._session.query(sql)
    id_cliente = id.as_dict()
    if id:
      id.free()
      return id_cliente['id_cliente']
    id.free()
    return None

  @gen.coroutine
  def insert_client_group(self, id_cliente, x, y , group):
    sql = 'UPDATE cliente set posicion = (point(%f, %f)), grupo = %s WHERE id_cliente = %s' % (x,y,group, id_cliente)
    result = yield self._session.query(sql)
    result.free()
    return True

  @gen.coroutine
  def get_client_cluster_info(self):
    sql = 'SELECT cliente.posicion, cliente.grupo from cliente'
    data = yield self._session.query(sql)
    people = data.items()
    data.free()
    for person in people:
      if person['posicion']:
        person['posicion_geografica'] = list(eval(person['posicion']))
    return people
  
  @gen.coroutine
  def get_cluster_info(self, num_custer):
    sql = 'SELECT persona.*, cliente.* from persona, cliente WHERE persona.id_persona = cliente.fk_id_persona AND cliente.grupo = %s' % num_custer
    data = yield self._session.query(sql)
    data_to_return = data.items()
    data.free()
    return data_to_return


  ### FAVORITOS
  @gen.coroutine
  def existent_favourite(self, id_cliente, id_producto):
    sql = 'SELECT * FROM favorito WHERE fk_id_cliente = %s AND fk_id_producto = %s' % (id_cliente, id_producto)
    registered = yield self._session.query(sql)
    if registered:
      registered.free()
      return True
    registered.free()
    return False

  @gen.coroutine
  def add_client_favourite(self, id_cliente, id_producto):
    sql = 'INSERT INTO favorito(fk_id_cliente, fk_id_producto, fecha_agregacion) VALUES (%s,%s, (SELECT current_timestamp))' % (id_cliente, id_producto)
    register = yield self._session.query(sql)
    if register:
      register.free()
      return True
    register.free()
    return False
  
  @gen.coroutine
  def remove_client_favourite(self, id_cliente, id_producto):
    sql = 'DELETE FROM favorito WHERE fk_id_cliente = %s AND fk_id_producto = %s' % (id_cliente, id_producto)
    deleted = yield self._session.query(sql)
    if deleted:
      deleted.free()
      return True
    deleted.free()
    return False
  
  @gen.coroutine
  def get_client_favourites_products(self, id_cliente):
    __product_model = ProductModel()
    sql = """
          SELECT producto.id_producto, producto.nombre as producto, producto.precio_venta, producto.stock,departamento.nombre AS departamento,tienda.nombre AS tienda, categoria.nombre AS categoria, marca.nombre AS marca,promocion.nombre AS promocion
          FROM producto,departamento,tienda,categoria,marca,promocion, favorito
          WHERE producto.fk_id_departamento = departamento.id_departamento
          AND producto.fk_id_categoria = categoria.id_categoria
          AND producto.fk_id_marca = marca.id_marca
          AND producto.fk_id_promocion = promocion.id_promocion
          AND departamento.fk_id_tienda = tienda.id_tienda 
          AND favorito.fk_id_producto = producto.id_producto
          AND favorito.fk_id_cliente = %s
        """ % id_cliente
    results = yield self._session.query(sql)
    favourites = results.items()
    favourites = yield __product_model.assign_image_to_product(favourites)
    results.free()
    return favourites
  

  ##### PERMISOS
  @gen.coroutine
  def update_client_permissions(self, id_cliente, permissions):
    permissions = json.dumps(permissions)
    sql = "UPDATE cliente SET permisos = '%s' WHERE id_cliente = %s" % (permissions, id_cliente)
    results = yield self._session.query(sql)
    if not results:
      results.free()
      return False
    results.free()
    return True
  
  @gen.coroutine
  def get_client_permissions(self, id_cliente):
    sql = 'SELECT cliente.permisos FROM cliente,persona WHERE cliente.fk_id_persona = persona.id_persona and persona.id_persona = %s ' % id_cliente
    result = yield self._session.query(sql)
    permissions = result.as_dict()
    result.free()
    return permissions
  
  ###### gustos 
  @gen.coroutine
  def update_client_likes(self, id_cliente, likes):
    likes_array = '{'
    for key, value in likes.items():
      if value: 
        likes_array = likes_array + '"' + key + '",'
    likes_array = likes_array[0:len(likes_array)-1] + '}'
    sql = """UPDATE cliente SET gustos = '%s' WHERE id_cliente = %s""" % (likes_array, id_cliente)
    results = yield self._session.query(sql)
    if not results:
      results.free()
      return False
    results.free()
    return True
  
  @gen.coroutine
  def get_client_likes(self, id_cliente):
    sql = 'SELECT nombre FROM categoria WHERE fk_id_padre_cat IS NULL'
    results = yield self._session.query(sql)
    likes = results.items()
    likes_dict = dict()
    for like in likes:
      likes_dict[like['nombre']] = False
    results.free()
    sql = 'SELECT cliente.gustos FROM cliente, persona WHERE cliente.fk_id_persona = persona.id_persona AND persona.id_persona = %s' % id_cliente
    results = yield self._session.query(sql)
    client_likes = results.as_dict()
    client_likes = client_likes['gustos']
    for key, value in likes_dict.items():
      if key in client_likes:
        likes_dict[key] = True
    results.free()
    return likes_dict
  
  # TOKEN FCM
  @gen.coroutine
  def persona_update_token_fcm(self, id_persona, token):
    sql = """
      UPDATE persona set token_fcm = '{1}' WHERE id_persona = {0}
    """.format(id_persona, token)
    results = yield self._session.query(sql)
    if results:
      results.free()
      return 200, 'Token de FCM actualizado'
    results.free()
    return 400, 'Hubo un problema al actualizar la información'
  
  @gen.coroutine
  def get_person_token_fcm(self, id_person):
    sql = """
      SELECT token_fcm FROM persona WHERE id_persona = {0}
       """.format(id_person)
    data = yield self._session.query(sql)
    token_fcm = [(data.as_dict())['token_fcm']]
    data.free()
    return token_fcm
  
  @gen.coroutine
  def get_all_person_token_fcm(self):
    sql = 'SELECT token_fcm FROM persona WHERE token_fcm IS NOT NULL'
    results = yield self._session.query(sql)
    results = results.items()
    tokens = []
    for token in results:
      tokens.append(token['token_fcm'])
    results.free()
    return tokens

    # sistema de recomendaciones

  @gen.coroutine
  def get_client_thetas(self, id_cliente):
    sql = 'SELECT thetas, id_cliente FROM cliente WHERE id_cliente = %s' %id_cliente
    results = yield self._session.query(sql)
    client = results.as_dict()
    results.free()
    return client

  @gen.coroutine
  def save_client_thetas(self,user):
    likes_array = '{'
    thetas = user['theta'].tolist()
    for value in thetas[0]:
      likes_array = likes_array + '' + str(value) + ','
    likes_array = likes_array[0:len(likes_array)-1] + '}'
    sql = """UPDATE cliente SET thetas = '%s' WHERE id_cliente = %s""" % (likes_array, user['id_cliente'])
    results = yield self._session.query(sql)
    results.free()
  
  @gen.coroutine
  def save_product_xs(self, products):
    for product in products:
      likes_array = '{'
      x = product['x'].tolist()
      for value in x[0]:
        likes_array = likes_array + '' + str(value) + ','
      likes_array = likes_array[0:len(likes_array)-1] + '}'
      sql = """UPDATE producto SET x = '%s' WHERE id_producto = %s""" % (likes_array, product['id_producto'])
      results = yield self._session.query(sql)
      results.free()

  @gen.coroutine
  def save_product_mu(self, id_producto, mean):
    sql = """UPDATE producto SET mu = %s WHERE id_producto = %s""" % (mean, id_producto)
    results = yield self._session.query(sql)
    results.free()
    return True
  @gen.coroutine
  def get_cluster_people_by_user(self, id_user):
    sql = 'SELECT cliente.id_cliente, cliente.gustos FROM cliente WHERE grupo = (SELECT cliente.grupo FROM cliente WHERE fk_id_persona = %s)' % id_user
    results = yield self._session.query(sql)
    people = results.items()
    results.free()
    return people
  
  @gen.coroutine
  def get_all_people(self):
    sql = 'SELECT cliente.id_cliente, cliente.gustos FROM cliente' 
    results = yield self._session.query(sql)
    people = results.items()
    results.free()
    return people

  @gen.coroutine
  def get_purchases_and_favs_by_people(self, people):
    for person in people:
      sql = 'SELECT compra.fk_id_producto, compra.calificacion_producto FROM compra WHERE fk_id_cliente = %s' % person['id_cliente']
      results = yield self._session.query(sql)
      purchases = results.items()
      person['purchases'] = purchases
      results.free()
      sql = 'SELECT fk_id_producto FROM favorito WHERE fk_id_cliente = %s' % person['id_cliente']
      results = yield self._session.query(sql)
      favs = results.items()
      person['favs'] = favs
      results.free()
    return people
  
  @gen.coroutine
  def get_purchases_and_favs_by_client(self, person):
    sql = 'SELECT compra.fk_id_producto, compra.calificacion_producto FROM compra WHERE fk_id_cliente = %s' % person['id_cliente']
    results = yield self._session.query(sql)
    purchases = results.items()
    person['purchases'] = purchases
    results.free()
    sql = 'SELECT fk_id_producto FROM favorito WHERE fk_id_cliente = %s' % person['id_cliente']
    results = yield self._session.query(sql)
    favs = results.items()
    person['favs'] = favs
    results.free()
    return person
  
  @gen.coroutine
  def get_favourites_by_people(self, people):
    for person in people:
      sql = 'SELECT fk_id_producto FROM favorito WHERE fk_id_cliente = %s' % person['id_cliente']
      results = yield self._session.query(sql)
      favs = results.items()
      person['favs'] = favs
      results.free()
    return people
  
  @gen.coroutine
  def get_password_by_email(self, email):
    sql = "SELECT contrasena from persona where email = '%s'" % email
    results = yield self._session.query(sql)
    if not results:
      return None
    result = results.as_dict()
    results.free()
    return result['contrasena']


############# inicio de sesión cliente
  @gen.coroutine
  def find_user_by_email_password(self, email, password):
    sql = "SELECT id_persona FROM persona where email = '%s' AND contrasena = '%s' " % (email, password)
    results = yield self._session.query(sql)
    if not results: 
      return None
    user = results.as_dict()['id_persona']
    results.free()
    return user
  @gen.coroutine
  def get_client_data_by_id(self, id_persona):
    sql = """
      SELECT persona.id_persona, persona.nombre, persona.apellido_paterno, persona.apellido_materno,
      persona.email, persona.fecha_nacimiento, persona.sexo, persona.imagen
      FROM persona, cliente
      WHERE persona.id_persona = cliente.fk_id_persona
      AND persona.id_persona = %s
    """ %id_persona
    results = yield self._session.query(sql)
    user_data = results.as_dict()
    if user_data['fecha_nacimiento']:
      user_data = self.__util.cast_datetime_to_string([user_data], ['fecha_nacimiento'])
    results.free()
    return user_data[0]

  ##### esto es para los beneficios
  @gen.coroutine
  def get_client_beneficts(self, id_cliente):
    sql = """
      SELECT beneficio.* 
      FROM beneficio, nivel_beneficio, nivel, cliente
      WHERE beneficio.id_beneficio = nivel_beneficio.fk_id_beneficio
      AND nivel_beneficio.fk_id_nivel = nivel.id_nivel
      AND cliente.fk_id_nivel = nivel.id_nivel
      AND cliente.id_cliente = %s
    """ % id_cliente
    results = yield self._session.query(sql)
    beneficts = results.items()
    results.free()
    return beneficts

####Para obtener logros
  @gen.coroutine
  def get_client_achievements(self, id_cliente):
    sql = """
      SELECT logro.*
      FROM logro, logro_cliente, cliente
      WHERE logro.id_logro = logro_cliente.fk_id_logro
      AND logro_cliente.fk_id_cliente = cliente.id_cliente
      AND cliente.id_cliente = %s
    """ % id_cliente
    results = yield self._session.query(sql)
    achievements = results.items()
    results.free()
    return achievements

  ###### informacion personal
  @gen.coroutine
  def update_client_information(self, id_cliente, data_profile):
    information_array = '{'
    for key, value in data_profile.items():
      if value: 
        information_array = information_array + '"' + key + '",'
    information_array = information_array[0:len(information_array)-1] + '}'
    sql = """UPDATE persona 
    SET sexo = %s,
    estado_civil = '%s',
    fecha_nacimiento = '%s'
    WHERE id_persona = %s""" % (data_profile['sexo'], data_profile['estado_civil'],data_profile['fecha_nacimiento'], id_cliente)
    results = yield self._session.query(sql)
    if not results:
      results.free()
      return False
    results.free()
    return True

    ###Informacion del cliente
  @gen.coroutine
  def get_client_information(self, id_cliente):
    sql = """
      SELECT persona.sexo, persona.estado_civil, persona.fecha_nacimiento, cliente.fk_id_nivel
      FROM persona, cliente 
      WHERE persona.id_persona = cliente.fk_id_persona
      AND id_persona = %s
    """ %id_cliente
    results = yield self._session.query(sql)
    user_data = results.as_dict()
    results1 = self.__util.cast_datetime_to_string([user_data], ['fecha_nacimiento'])
    results.free()
    return results1[0]
  
  @gen.coroutine 
  def get_client_feed_basic_info(self, id_cliente):
    sql = """
    SELECT persona.id_persona,persona.nombre, cliente.fk_id_nivel, cliente.fecha_registro, nivel.nombre as nombre_nivel
    FROM persona, cliente, nivel
    WHERE persona.id_persona = cliente.fk_id_persona 
    AND cliente.fk_id_nivel = nivel.id_nivel
    AND id_persona = %s
    """ % id_cliente
    results = yield self._session.query(sql)
    user_data = results.as_dict()
    results1 = self.__util.cast_datetime_to_string([user_data], ['fecha_registro'])
    results.free()
    return results1[0]
