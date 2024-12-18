import requests, time
import os
from flask import Flask, request, make_response, jsonify, send_file
from requests.exceptions import ConnectionError, HTTPError
from werkzeug.exceptions import NotFound
from io import BytesIO



ALLOWED_GACHA_SYS_OP ={'add_gacha', 'delete_gacha', 'update_gacha', 'get_gacha_collection'}
ADD_URL = 'https://gachasystem:5004/add_gacha'
DELETE_GACHA_URL = 'https://gachasystem:5004/delete_gacha'
UPDATE_GACHA_URL = 'https://gachasystem:5004/update_gacha'
GET_GACHA_COLL_URL = 'https://gachasystem:5004/get_gacha_collection'
GACHA_IMAGE_URL = 'https://gachasystem:5004/uploads/'

ALLOWED_AUTH_OP ={'signup', 'login', 'logout', 'delete', 'newToken'}
SINGUP_URL = 'https://auth_service:5002/signup'
LOGIN_URL = 'https://auth_service:5002/login'
LOGOUT_URL = 'https://auth_service:5002/logout'
DELETE_URL = 'https://auth_service:5002/delete'
NEWTOKEN_URL = 'https://auth_service:5002/newToken'


ALLOWED_AUCTION_OP = {'see', 'create', 'modify', 'bid','gacha_receive', 'auction_lost', 'auction_terminated'} 
AUCTION_BASE_URL = 'https://auction_service:5008'
SEE_AUCTION_URL = f'{AUCTION_BASE_URL}/see'
MODIFY_AUCTION_URL = f'{AUCTION_BASE_URL}/modify'

PROFILE_IMAGE_URL = 'https://profile_setting:5003/uploads/'




import time
import requests
from flask import Flask, jsonify, make_response, request

class CircuitBreaker:
    def __init__(self, failure_threshold=3, recovery_timeout=5, reset_timeout=10):
        self.failure_threshold = failure_threshold  # Soglia di fallimento
        self.recovery_timeout = recovery_timeout      # Tempo di recupero tra i tentativi
        self.reset_timeout = reset_timeout          # Tempo massimo di attesa prima di ripristinare il circuito
        self.failure_count = 0                      # Numero di fallimenti consecutivi
        self.last_failure_time = 0                  # Ultimo tempo in cui si è verificato un fallimento
        self.state = 'CLOSED'                       # Stato iniziale del circuito (CLOSED)

    def call(self, method, url, params=None, headers=None, files=None, json=True):
        if self.state == 'OPEN':
            # Se il circuito è aperto, controlla se è il momento di provare di nuovo
            if time.time() - self.last_failure_time > self.reset_timeout:
                print("Closing the circuit")
                self.state = 'CLOSED'
                self._reset()
            else:
                return jsonify({'Error': 'Open circuit, try again later'}), 503  # ritorna un errore 503

        try:
            # Usa requests.request per specificare il metodo dinamicamente
            if json:
                response = requests.request(method, url, json=params, headers=headers, verify=False)
            else:
                response = requests.request(method, url, data=params, headers=headers, files=files, verify=False)
            
            response.raise_for_status()  # Solleva un'eccezione per errori HTTP (4xx, 5xx)

            # Verifica se la risposta è un'immagine
            if 'image' in response.headers.get('Content-Type', ''):
                return response.content, response.status_code  # Restituisce il contenuto dell'immagine

            return response.json(), response.status_code  # Restituisce il corpo della risposta come JSON
        
        except requests.exceptions.HTTPError as e:
            # In caso di errore HTTP, restituisci il contenuto della risposta (se disponibile)
            error_content = response.text if response else str(e)
            # self._fail()
            return {'Error': error_content}, response.status_code

        except requests.exceptions.ConnectionError as e:
            # Per errori di connessione o altri problemi
            self._fail()
            return {'Error': f'Error calling the service: {str(e)}'}, 503

    def _fail(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            print("Circuito aperto a causa di troppi errori consecutivi.")
            self.state = 'OPEN'

    def _reset(self):
        self.failure_count = 0
        self.state = 'CLOSED'
        

# Inizializzazione dei circuit breakers
auth_circuit_breaker = CircuitBreaker()
gacha_sys_circuit_breaker = CircuitBreaker()
auction_circuit_breaker = CircuitBreaker()
gacha_roll_circuit_breaker = CircuitBreaker()
profile_circuit_breaker = CircuitBreaker()
payment_circuit_breaker = CircuitBreaker()


# Per gestione immagini
def get_mime_type(extension):
    mime_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'bmp': 'image/bmp',
        'webp': 'image/webp',
    }
    return mime_types.get(extension.lower(), 'application/octet-stream')  # Tipo predefinito se non trovato


app = Flask(__name__, instance_relative_config=True)

def create_app():
    return app

@app.route('/auth_service/<op>', methods=['POST', 'DELETE', 'GET'])
def auth(op):
    if op not in ALLOWED_AUTH_OP:
        return make_response(f'Invalid operation {op}'), 400
    
    # Preparazione dei parametri in base all'operazione
    # FORSE SOLO USER NORMALE
    if op == 'signup':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        url = SINGUP_URL
        headers = {
            'Origin' : 'admin_gateway'
        }
        params = {'username': username, 'password': password, 'email': email}
    # ENTRAMBI
    elif op == 'login':
        username = request.form.get('username')
        password = request.form.get('password')
        url = LOGIN_URL
        headers={}
        params = {'username': username, 'password': password}
    # ENTRAMBI
    elif op == 'delete':
        username = request.form.get('username')
        password = request.form.get('password')
        jwt_token = request.headers.get('Authorization')
        headers = {
            'Authorization' : jwt_token
        }
        url = DELETE_URL
        params = {'username': username, 'password': password}
    # ENTRAMBI
    elif op == 'logout':
        url = LOGOUT_URL
        params = {}
        jwt_token = request.headers.get('Authorization')  # Supponiamo che il token JWT sia passato nei headers come 'Authorization'
        headers = {'Authorization': jwt_token}  # Usa il token JWT ricevuto nell'header della richiesta
    elif op == 'newToken':
        url = NEWTOKEN_URL
        params = {}
        jwt_token = request.headers.get('Authorization')  # Supponiamo che il token JWT sia passato nei headers come 'Authorization'
        headers = {
            'Authorization': jwt_token
        } 


    # Chiamata al servizio in base all'operazione
    if op in ['login', 'signup']:
        x, status_code = auth_circuit_breaker.call('POST', url, params, headers, {}, True)
    elif op == 'logout':
        x, status_code = auth_circuit_breaker.call('DELETE', url, {}, headers, {}, False)
    elif op == 'newToken':
        x, status_code = auth_circuit_breaker.call('GET', url, {}, headers, {}, False)
    else:
        x, status_code = auth_circuit_breaker.call('DELETE', url, params, headers, {}, True)

    if status_code == 200:
        # Restituisci la risposta del servizio con il codice di stato appropriato
        return make_response(jsonify(x), status_code)
    else:
        return jsonify({'Error' : f'Error during signup {x}'}), status_code


@app.route('/auction_service/<op>', methods=['GET', 'POST', 'PATCH'])
def auction_service(op):
    if op not in ALLOWED_AUCTION_OP:
        return jsonify({"error": f"Invalid operation '{op}'"}), 400
        # Operazione "see"
    # ENTRAMBI
    if op == 'see':
        auction_id = request.args.get('auction_id')  # Recupera auction_id dai parametri della query
        status = request.args.get('status', 'active')  # Status predefinito a 'active'
        jwt_token = request.headers.get('Authorization')
        headers = {
            'Authorization' : jwt_token
        }
        # Costruisce l'URL con i parametri corretti
        url = f'{SEE_AUCTION_URL}?status={status}'
        if auction_id:
            url += f'&auction_id={auction_id}'

        response, status_code = auction_circuit_breaker.call('get', url, {}, headers, {}, False)
        if status_code != 200:
            return jsonify({'Error' : f'Error during see op {response}'}), status_code

        return make_response(jsonify(response), status_code)

    # Operazione "modify"
    # SOLO ADMIN
    elif op == 'modify':
        data = request.get_json()
        auction_id = data.get('auction_id')
        seller_username = data.get('seller_username')
        gacha_name = data.get('gacha_name')
        base_price = data.get('basePrice')
        end_date = data.get('endDate')

        if not auction_id:
            return jsonify({"error": "Auction ID is required"}), 400
        jwt_token = request.headers.get('Authorization')
        headers = {
            'Authorization' : jwt_token
        }
        url = f'{MODIFY_AUCTION_URL}?auction_id={auction_id}'
        if seller_username:
            url += f'&seller_username={seller_username}'
        if gacha_name:
            url += f'&gacha_name={gacha_name}'
        if base_price:
            url += f'&basePrice={base_price}'
        if end_date:
            url += f'&endDate={end_date}'

        response, status_code = auction_circuit_breaker.call('patch', url, {}, headers, {}, False)
        if status_code != 200:
            return jsonify({'Error' : f'Error during modify op {response}'}), status_code
        return make_response(jsonify(response), status_code)

@app.route('/images_gacha/uploads/<name>', methods=['GET'])
# ENTRAMBI
def gacha_image(name):
    url = GACHA_IMAGE_URL + name
    file_extension = os.path.splitext(name)[1][1:]
    mime_type = get_mime_type(file_extension)
    jwt_token = request.headers.get('Authorization')
    headers = {
        'Authorization' : jwt_token
    }
    content, status = gacha_sys_circuit_breaker.call('get', url, {}, headers, {}, False)
    if status == 200:
        file = BytesIO(content)
        return send_file(file, mimetype=mime_type)
    else:
        return jsonify({'Error' : f'Error during gacha image op '}), status

@app.route('/gachasystem_service/<op>', methods=['POST', 'DELETE', 'PATCH', 'GET'])
def gachasystem(op):
    if op not in ALLOWED_GACHA_SYS_OP:
        return make_response(f'Invalid operation {op}', 400)
    # SOLO ADMIN
    if op == 'add_gacha':
        gacha_name = request.form.get('gacha_name')
        rarity = request.form.get('rarity')
        description = request.form.get('description')
        if 'image' not in request.files:
            files = {}
        else:
            file = request.files['image']
            files = {'image': (file.filename, file.stream, file.mimetype)}
        url = ADD_URL
        params = {
            'gacha_name': gacha_name,
            'rarity': rarity,
            'description': description
        }
        jwt_token = request.headers.get('Authorization')
        headers = {
            'Authorization' : jwt_token
        }
    # SOLO ADMIN
    elif op == 'delete_gacha':
        gacha_name = request.form.get('gacha_name')
        url = DELETE_GACHA_URL
        params = {'gacha_name': gacha_name}
        jwt_token = request.headers.get('Authorization')
        headers = {
            'Authorization' : jwt_token
        }
    # SOLO ADMIN
    elif op == 'update_gacha':
        gacha_name = request.form.get('gacha_name')
        rarity = request.form.get('rarity')
        description = request.form.get('description')
        url = UPDATE_GACHA_URL
        params = {
            'gacha_name': gacha_name,
            'rarity': rarity,
            'description': description
        }
        jwt_token = request.headers.get('Authorization')
        headers = {
            'Authorization' : jwt_token
        }
    # ENTRAMBI
    elif op == 'get_gacha_collection':
        gacha_name = request.form.getlist('gacha_name')
        # if gacha_name:
        #     gacha_name = gacha_name.split(',')  # Divide la stringa in una lista
        if gacha_name:
            params = {
                'gacha_name': gacha_name
            }
        else:
            params = {
                'gacha_name': {}
            }
        url = GET_GACHA_COLL_URL
        jwt_token = request.headers.get('Authorization')
        headers = {
            'Authorization' : jwt_token
        }

    if op == 'add_gacha':
        response, status = gacha_sys_circuit_breaker.call('post', url, params, headers, files, False)
    elif op == 'delete_gacha':
        response, status = gacha_sys_circuit_breaker.call('delete', url, params, headers, {}, True)
    elif op == 'update_gacha':
        response, status = gacha_sys_circuit_breaker.call('patch', url, params, headers, {}, True)
    elif op == 'get_gacha_collection':
        response, status = gacha_sys_circuit_breaker.call('get', url, params, headers, {}, True)
        if status != 200:
            return jsonify({'Error' : f'Error during get gacha collection op {response}'}), status
        return jsonify(response), status
    if status != 200:
        return jsonify({'Error' : f'Error in gacha system op {response}'}), status
    return jsonify(response), status
