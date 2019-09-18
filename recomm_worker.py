import requests
import plotly
import plotly.plotly as py
import plotly.graph_objs as go
plotly.tools.set_credentials_file(username='ruben.murga.desarrollo', api_key='tIRU7450BTJaYmzgRADp')

r = requests.get('http://127.0.0.1:8000/global-recommendations')

print(r.status_code)
training = go.Scatter(x=r.json()['x'],y=r.json()['y'], name='Datos de entrenamiento')
validation = go.Scatter(x=r.json()['x'],y=r.json()['y_cross'], name= 'Validación')
data = [training, validation]
py.plot(data, filename = 'basic-line', auto_open=True)