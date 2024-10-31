##FUNCIONANDOOOOO
# import random
# import time
# import redis

# class Cliente:
#     def __init__(self, id, redis_host, redis_port):
#         self.id = id
#         self.redis_host = redis_host
#         self.redis_port = redis_port
#         self.redis_client = redis.Redis(host=redis_host, port=redis_port)
#         self.pubsub = self.redis_client.pubsub()
#         self.pubsub.subscribe('R_topic')

#     def pedir_acesso(self):
#         timestamp = int(time.time())
#         self.redis_client.publish('R_topic', f'{self.id}:{timestamp}:ACQUIRE')

#     def receber_resposta(self):
#         for message in self.pubsub.listen():
#             if message['type'] == 'message':
#                 partes = message['data'].decode().split(':')
#                 if partes[0] == str(self.id) and partes[2] == 'COMMITTED':
#                     print(f'Cliente {self.id} recebeu COMMITTED')
#                     time.sleep(random.randint(1, 5))
#                     self.pedir_acesso()
#                     break

# # Criar 5 clientes
# clientes = []
# for i in range(5):
#     cliente = Cliente(i, 'redis', 6379)
#     clientes.append(cliente)

# # Iniciar os clientes (em threads separadas para receber mensagens)
# import threading
# for cliente in clientes:
#     threading.Thread(target=cliente.receber_resposta).start()

# # Iniciar os pedidos de acesso
# for cliente in clientes:
#     cliente.pedir_acesso()



# import random
# import time
# import redis

# class Cliente:
#     def __init__(self, id, redis_host, redis_port):
#         self.id = id
#         self.redis_host = redis_host
#         self.redis_port = redis_port
#         self.redis_client = redis.Redis(host=redis_host, port=redis_port)
#         self.pubsub = self.redis_client.pubsub()
#         self.pubsub.subscribe('R_topic')

#     def pedir_acesso(self):
#         timestamp = int(time.time())
#         self.redis_client.publish('R_topic', f'{self.id}:{timestamp}:ACQUIRE')

#     def receber_resposta(self):
#         for message in self.pubsub.listen():
#             if message['type'] == 'message':
#                 partes = message['data'].decode().split(':')
#                 if partes[0] == str(self.id) and partes[2] == 'COMMITTED':
#                     print(f'Cliente {self.id} recebeu COMMITTED')
#                     time.sleep(random.randint(1, 5))
#                     self.pedir_acesso()
#                     break

#     def executar(self):
#         num_acessos = random.randint(10, 50)
#         for _ in range(num_acessos):
#             self.pedir_acesso()
#             self.receber_resposta()
#             time.sleep(random.randint(1, 5))
    


# # # Criar 5 clientes
# clientes = []
# for i in range(5):
#     cliente = Cliente(i, 'redis', 6379)
#     clientes.append(cliente)

# # Iniciar os clientes (em threads separadas para receber mensagens)
# import threading
# for cliente in clientes:
#     threading.Thread(target=cliente.receber_resposta).start()

# # # Iniciar os pedidos de acesso
# for cliente in clientes:
#     cliente.executar()


import random
import time
import threading

from redis import Redis

# Constantes
REDIS_HOST = 'redis'  # Nome do serviço Redis no Docker Compose
REDIS_PORT = 6379
R_TOPIC = 'R_topic'
R_RESPONSE_CHANNEL = 'R_response_channel'  # Novo canal para respostas

class Cliente:
    def __init__(self, id, redis_client):
        self.id = id
        self.redis_client = redis_client

    def pedir_acesso(self):
        timestamp = int(time.time() * 1000)  # Timestamp em milissegundos
        mensagem = f"{self.id}:{timestamp}:ACQUIRE"
        self.redis_client.publish(R_TOPIC, mensagem)
        print(f"Cliente {self.id} solicitou acesso com mensagem: {mensagem}")

    # def aguardar_confirmacao(self):
    #     pubsub = self.redis_client.pubsub()
    #     pubsub.subscribe(R_RESPONSE_CHANNEL)  # Escutar o canal de respostas
    #     for mensagem in pubsub.listen():
    #         if mensagem['type'] == 'message':
    #             _, _, status = mensagem['data'].decode().split(':')
    #             if status == 'COMMITTED':
    #                 print(f"Cliente {self.id} recebeu COMMITTED")
    #                 pubsub.unsubscribe(R_RESPONSE_CHANNEL)
    #                 return
    def aguardar_confirmacao(self):
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(R_RESPONSE_CHANNEL)  # Escutar o canal de respostas
        for mensagem in pubsub.listen():
            if mensagem['type'] == 'message':
                _, _, status = mensagem['data'].decode().split(':')
                if status == 'COMMITTED':
                    print(f"Cliente {self.id} recebeu COMMITTED")
                    pubsub.unsubscribe(R_RESPONSE_CHANNEL)
                    return
                
    def escutar_respostas(self):
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(R_RESPONSE_CHANNEL)
        for mensagem in pubsub.listen():
            if mensagem['type'] == 'message':
                id_cliente, _, status = mensagem['data'].decode().split(':')
                if status == 'COMMITTED' and int(id_cliente) == self.id:
                    print(f"Cliente {self.id} recebeu COMMITTED")

    def executar(self):
        threading.Thread(target=self.escutar_respostas).start()  # Inicia thread para escutar respostas
        num_acessos = random.randint(10, 50)
        for _ in range(num_acessos):
            self.pedir_acesso()
            self.aguardar_confirmacao()
            time.sleep(random.randint(1, 5))

if __name__ == '__main__':
    # Configuração do Redis
    redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT)

    # Criação do cliente
    cliente = Cliente(1, redis_client)  # Adapte o ID do cliente se necessário
    cliente.executar()