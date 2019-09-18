import queries

class Connection():
  _session = queries.TornadoSession() 
  def __init__(self):
    url = queries.uri("host", 5432, "db", "user", "password")
    self._session = queries.TornadoSession(url)

