from datetime import datetime, timezone
from flask import Flask, Response, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import json
import paho.mqtt.client as mqtt
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ********************* CONEXÃO BANCO DE DADOS *********************************

app = Flask('registro')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:senai%40134@127.0.0.1/medidor'
app.config['SQLALCHEMY_ECHO'] = True  # Habilita o log de SQLAlchemy

mybd = SQLAlchemy(app)

# ********************** CONEXÃO GOOGLE API ***************************

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDENTIALS_PATH = "C:\\Users\\admin\\Desktop\\9. Projeto Integrador Completo\\credentials.json"
SAMPLE_SPREADSHEET_ID = '1sislbPFTs4cQXwE9a6Hemxj02yZ3ijDHTNrV_cXFCQU'  # Substitua pelo ID da sua planilha
SAMPLE_RANGE_NAME = 'Registro!A1'  # Substitua pelo intervalo da sua planilha

def get_google_sheets_service():
    """Obtemos o serviço de Google Sheets usando credenciais de conta de serviço."""
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH,
        scopes=SCOPES
    )
    return build('sheets', 'v4', credentials=creds)

def update_google_sheet(data):
    """Atualiza a planilha do Google Sheets com dados."""
    service = get_google_sheets_service()
    sheet = service.spreadsheets()

    values_novos = [["CO2", "Temperatura", "Pressão", "Altitude", "Umidade", "Tempo Registro"]]
    
    for registro in data:
        if registro['co2'] > 20:
            values_novos.append([
                registro['co2'],
                registro['temperatura'],
                registro['pressao'],
                registro['altitude'],
                registro['umidade'],
                registro['tempo_registro']
            ])
    
    if not values_novos:
        print("Nenhum dado para atualizar na planilha.")
        return
    
    try:
        result = sheet.values().update(
            spreadsheetId=SAMPLE_SPREADSHEET_ID,
            range=SAMPLE_RANGE_NAME,
            valueInputOption="USER_ENTERED",
            body={'values': values_novos}
        ).execute()
        print(f"Planilha atualizada com sucesso! Atualizados {result.get('updatedCells')} células.")
    
    except HttpError as err:
        print(f"Erro ao conectar com a API do Google Sheets: {err}")
# ********************* CONEXÃO SENSORES *********************************

mqtt_data = []

def on_connect(client, userdata, flags, rc, properties=None):
    print("Connected with result code " + str(rc))
    client.subscribe("projeto_integrado/SENAI134/Cienciadedados/GrupoX")

def on_message(client, userdata, msg):
    global mqtt_data
    payload = msg.payload.decode('utf-8')
    mqtt_data = json.loads(payload)
    print(f"Received message: {mqtt_data}")

    with app.app_context():
        try:
            temperatura = mqtt_data.get('temperature')
            pressao = mqtt_data.get('pressure')
            altitude = mqtt_data.get('altitude')
            umidade = mqtt_data.get('humidity')
            co2 = mqtt_data.get('CO2')
            timestamp_unix = mqtt_data.get('timestamp')

            if timestamp_unix is None:
                print("Timestamp não encontrado no payload")
                return

            try:
                timestamp = datetime.fromtimestamp(int(timestamp_unix), tz=timezone.utc)
            except (ValueError, TypeError) as e:
                print(f"Erro ao converter timestamp: {str(e)}")
                return

            new_data = Registro(
                temperatura=temperatura,
                pressao=pressao,
                altitude=altitude,
                umidade=umidade,
                co2=co2,
                tempo_registro=timestamp
            )

            mybd.session.add(new_data)
            mybd.session.commit()
            print("Dados inseridos no banco de dados com sucesso")

            # Atualiza o Google Sheets com os novos dados
            registros = Registro.query.all()
            registros_json = [registro.to_json() for registro in registros]
            update_google_sheet(registros_json)

        except Exception as e:
            print(f"Erro ao processar os dados do MQTT: {str(e)}")
            mybd.session.rollback()

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect("test.mosquitto.org", 1883, 60)

def start_mqtt():
    mqtt_client.loop_start()

# Cadastrar
@app.route('/data', methods=['POST'])
def post_data():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Nenhum dado fornecido"}), 400

        print(f"Dados recebidos: {data}")

        temperatura = data.get('temperatura')
        pressao = data.get('pressao')
        altitude = data.get('altitude')
        umidade = data.get('umidade')
        co2 = data.get('co2')
        timestamp_unix = data.get('tempo_registro')

        try:
            timestamp = datetime.fromtimestamp(int(timestamp_unix), tz=timezone.utc)
        except ValueError as e:
            print(f"Erro no timestamp: {str(e)}")
            return jsonify({"error": "Timestamp inválido"}), 400

        new_data = Registro(
            temperatura=temperatura,
            pressao=pressao,
            altitude=altitude,
            umidade=umidade,
            co2=co2,
            tempo_registro=timestamp
        )

        mybd.session.add(new_data)
        print("Adicionando o novo registro")
        mybd.session.commit()
        print("Dados inseridos no banco de dados com sucesso")

        return jsonify({"message": "Data received successfully"}), 201

    except Exception as e:
        print(f"Erro ao processar a solicitação: {str(e)}")
        mybd.session.rollback()
        return jsonify({"error": "Falha ao processar os dados"}), 500

@app.route('/data', methods=['GET'])
def get_data():
    return jsonify(mqtt_data)

class Registro(mybd.Model):
    __tablename__ = 'registro'
    id = mybd.Column(mybd.Integer, primary_key=True, autoincrement=True)
    temperatura = mybd.Column(mybd.Numeric(10, 2))
    pressao = mybd.Column(mybd.Numeric(10, 2))
    altitude = mybd.Column(mybd.Numeric(10, 2))
    umidade = mybd.Column(mybd.Numeric(10, 2))
    co2 = mybd.Column(mybd.Numeric(10, 2))
    tempo_registro = mybd.Column(mybd.DateTime)

    def to_json(self):
        return {
            "id": self.id,
            "temperatura": float(self.temperatura),
            "pressao": float(self.pressao),
            "altitude": float(self.altitude),
            "umidade": float(self.umidade),
            "co2": float(self.co2),
            "tempo_registro": self.tempo_registro.strftime('%Y-%m-%d %H:%M:%S') if self.tempo_registro else None
        }

@app.route("/registro", methods=["GET"])
def seleciona_registro():
    registro_objetos = Registro.query.all()
    registro_json = [registro.to_json() for registro in registro_objetos]
    return gera_response(200, "registro", registro_json)

@app.route("/registro/<id>", methods=["GET"])
def seleciona_registro_id(id):
    registro_objetos = Registro.query.filter_by(id=id).first()
    if registro_objetos:
        registro_json = registro_objetos.to_json()
        return gera_response(200, "registro", registro_json)
    else:
        return gera_response(404, "registro", {}, "Registro não encontrado")

@app.route("/registro/<id>", methods=["DELETE"])
def deleta_registro(id):
    registro_objetos = Registro.query.filter_by(id=id).first()
    if registro_objetos:
        try:
            mybd.session.delete(registro_objetos)
            mybd.session.commit()
            return gera_response(200, "registro", registro_objetos.to_json(), "Deletado com sucesso")
        except Exception as e:
            print('Erro', e)
            mybd.session.rollback()
            return gera_response(400, "registro", {}, "Erro ao deletar")
    else:
        return gera_response(404, "registro", {}, "Registro não encontrado")

def gera_response(status, nome_do_conteudo, conteudo, mensagem=False):
    body = {}
    body[nome_do_conteudo] = conteudo
    if mensagem:
        body["mensagem"] = mensagem
    return Response(json.dumps(body), status=status, mimetype="application/json")

if __name__ == '__main__':
    with app.app_context():
        mybd.create_all()  # Cria as tabelas no banco de dados
    
    start_mqtt()
    app.run(port=5000, host='localhost', debug=True)
