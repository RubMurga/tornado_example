import datetime

class UtilProject():
  serverFCMKey = "FCM KEY"
  defualtImage = "https://webiconspng.com/wp-content/uploads/2017/09/Sapphire-PNG-Image-88999-300x300.png"
  notify = {
    "sendRecommendation": {
      "title" : "Nueva una recomendación personalizada",
      "body"  : "Tienes una recomendación esperandote en este departamento."
    },
    "help":{
      "title" : "Un cliente esta solicitando ayuda",
      "body"  : "Un cliente cercano en el departamento esta solicitando ayuda."
    }
  }

  def isInt(self,value):
    try: 
      int(value)
      return True
    except ValueError:
      return False
  
  def cast_numeric_to_string(self,item_list,key):
    for item in item_list:
      item[key] =  str(item[key]) 
    return item_list
  
  def cast_datetime_to_string(self,item_list,keys):
    for item in item_list:
      for key in keys:
        if key in item:
          item[key] =  item[key].strftime('%Y/%m/%d %H:%M')
    return item_list

  def create_proximity_zones(self,devices):
    attachment_returns = {'tags' : list() }
    for device in devices:
      for tag in device['shadow']['tags']:
        if tag not in attachment_returns['tags']: 
          attachment_returns['tags'].append(tag)

    return attachment_returns
  
  def get_years_from_now(self, list_dict, columns = []):
    now = datetime.datetime.now()
    for column in columns:
      for row in list_dict:
        if row[column]:
          row[column] = (now - row[column]).days
    return list_dict
  
  def days_to_years(self, list_dict, columns = []):
    for column in columns:
      for row in list_dict:
        if row[column]:
          row[column] = int(row[column]/365)
    return list_dict
  
  def days_to_months(self, list_dict, columns = []):
    for column in columns:
      for row in list_dict:
        row[column] = int(row[column]/30)
    return list_dict

  def split_ages_intervals(self, list_dict, columns = []):
    for column in columns:
      for row in list_dict:
        if row[column]:
          if row[column] <= 10:
            row[column] = 0
          elif row[column] > 10 and row[column] <= 18:
            row[column] = 1
          elif row[column] > 18 and row[column] <= 25:
            row[column] = 2
          elif row[column] > 25 and row[column] <= 35:
            row[column] = 3
          elif row[column] > 35 and row[column] <= 45:
            row[column] = 4
          else:
            row[column] = 5
    return list_dict 
  
  def int64_to_int(self, dictionary):
    for key,value in dictionary.items():
      dictionary[key] = int(value)
    return dictionary
