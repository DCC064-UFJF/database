from flask import Flask, jsonify, request
from pymongo import MongoClient, ReadPreference
from bson import json_util
import json
import os

app = Flask(__name__)

# Configuração das URIs para cada réplica
replica_configs = {
    'primary': {
        'uri': 'mongodb://mongo1:27017/mydatabase?replicaSet=rs0',
        'read_preference': ReadPreference.PRIMARY
    },
    'secondary1': {
        'uri': 'mongodb://mongo2:27017/mydatabase?replicaSet=rs0',
        'read_preference': ReadPreference.SECONDARY_PREFERRED
    },
    'secondary2': {
        'uri': 'mongodb://mongo3:27017/mydatabase?replicaSet=rs0',
        'read_preference': ReadPreference.SECONDARY_PREFERRED
    }
}

def get_mongo_client(replica_name):
    """
    Cria uma conexão com uma réplica específica do MongoDB
    """
    if replica_name not in replica_configs:
        raise ValueError("Réplica não encontrada")
    
    config = replica_configs[replica_name]
    return MongoClient(
        config['uri'],
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=10000,
        retryWrites=True,
        w='majority',
        read_preference=config['read_preference']
    )

@app.route('/')
def index():
    return "Bem-vindo ao projeto com Docker e MongoDB Replica Set!"

@app.route('/data/<replica>', methods=['GET'])
def get_data(replica):
    try:
        client = get_mongo_client(replica)
        db = client.mydatabase
        data = list(db.mycollection.find({}, {"_id": 0}))
        client.close()
        return jsonify({
            'replica': replica,
            'data': data
        })
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/data/<replica>', methods=['POST'])
def insert_data(replica):
    try:
        client = get_mongo_client(replica)
        db = client.mydatabase
        
        # Pega dados do corpo da requisição
        data = request.get_json()
        if not data:
            return jsonify({"error": "Nenhum dado fornecido"}), 400
            
        result = db.mycollection.insert_one(data)
        client.close()
        
        return jsonify({
            'replica': replica,
            'message': 'Dados inseridos com sucesso',
            'inserted_id': str(result.inserted_id)
        })
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def get_replica_status():
    try:
        # Conecta na primária para verificar status do replica set
        client = get_mongo_client('primary')
        status = client.admin.command('replSetGetStatus')
        client.close()
        
        # Converte o status para um formato JSON serializável
        json_status = json.loads(json_util.dumps(status))
        
        return jsonify({
            'replica_set': 'rs0',
            'status': json_status
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/replica-status')
def check_replica_status():
    try:
        # Tenta conectar em qualquer uma das réplicas
        client = MongoClient(
            "mongodb://mongo1:27017,mongo2:27017,mongo3:27017/?replicaSet=rs0",
            serverSelectionTimeoutMS=5000
        )
        
        # Obtém o status do replica set
        status = client.admin.command('replSetGetStatus')
        
        # Encontra o membro primary
        primary = None
        members_status = []
        
        for member in status['members']:
            member_info = {
                'host': member['name'],
                'state': member['stateStr'],
                'health': member['health']
            }
            
            if member['stateStr'] == 'PRIMARY':
                primary = member['name']
                
            members_status.append(member_info)
        
        return jsonify({
            'primary': primary,
            'members': members_status,
            'set': status['set'],
            'ok': status['ok']
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'Error getting replica set status'
        }), 500

@app.route('/is-primary/<host>')
def check_if_primary(host):
    try:
        # Conecta diretamente ao host especificado
        client = MongoClient(
            f"mongodb://{host}:27017/?replicaSet=rs0",
            serverSelectionTimeoutMS=2000
        )
        
        # Tenta executar comando que só funciona no primary
        is_master = client.admin.command('isMaster')
        
        return jsonify({
            'host': host,
            'is_primary': is_master.get('ismaster', False),
            'replica_set': is_master.get('setName'),
            'primary': is_master.get('primary'),
            'secondaries': is_master.get('hosts', [])
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': f'Error checking {host} status'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)