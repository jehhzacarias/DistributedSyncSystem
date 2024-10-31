# import random
# import time
# import redis
# import threading

# class ElementoClusterSync:
#     def __init__(self, id, redis_host, redis_port):
#         self.id = id
#         self.redis_host = redis_host
#         self.redis_port = redis_port
#         self.redis_client = redis.Redis(host=redis_host, port=redis_port)
#         self.pubsub = self.redis_client.pubsub()
#         self.pubsub.subscribe('R_topic')
#         self.pilha_mensagens = []
#         self.lock = threading.Lock()  # Lock para proteger a pilha

#     def receber_mensagem(self):
#         for message in self.pubsub.listen():
#             if message['type'] == 'message':
#                 partes = message['data'].decode().split(':')
#                 with self.lock:  # Protege a pilha durante a modificação
#                     if partes[2] == 'ACQUIRE':
#                         self.pilha_mensagens.append(message['data'].decode())
#                     elif partes[2] == 'RELEASE':
#                         # Remove com segurança da pilha
#                         self.pilha_mensagens = [m for m in self.pilha_mensagens if m != message['data'].decode()]

#     def processar_mensagem(self):
#         while True:
#             if self.pilha_mensagens:
#                 with self.lock:  # Protege a pilha durante o acesso
#                     mensagem = self.pilha_mensagens[0]
#                     partes = mensagem.split(':')
#                     if int(partes[0]) == self.id and partes[2] == 'ACQUIRE':
#                         print(f'Elemento {self.id} recebeu ACQUIRE')
#                         time.sleep(random.uniform(0.2, 1))
#                         self.redis_client.publish('R_topic', f'{self.id}:{partes[1]}:RELEASE')
#                         self.pilha_mensagens.pop(0)

# # # Criar 5 elementos do Cluster Sync
# elementos = []
# for i in range(5):
#     elemento = ElementoClusterSync(i, 'redis', 6379)
#     elementos.append(elemento)

# # # Iniciar as threads para receber e processar mensagens
# for elemento in elementos:
#     threading.Thread(target=elemento.receber_mensagem).start()
#     threading.Thread(target=elemento.processar_mensagem).start()


import random
import time
import threading

from redis import Redis

# Constantes
NUM_ELEMENTOS_SYNC = 5
REDIS_HOST = 'redis'  # Nome do serviço Redis no Docker Compose
REDIS_PORT = 6379
R_TOPIC = 'R_topic'
R_RESPONSE_CHANNEL = 'R_response_channel'  # Novo canal para respostas

# Classe para representar o recurso R (apenas para simulação)
class RecursoR:
    def __init__(self):
        self.valor = 0

    def acessar(self, cliente_id):
        print(f"Recurso R acessado pelo cliente {cliente_id}. Valor antigo: {self.valor}")
        time.sleep(random.uniform(0.2, 1))  # Simula acesso
        self.valor += 1
        print(f"Recurso R liberado pelo cliente {cliente_id}. Novo valor: {self.valor}")


class ElementoClusterSync:
    def __init__(self, id, redis_client, recurso_r):
        self.id = id
        self.redis_client = redis_client
        self.recurso_r = recurso_r
        self.fila_mensagens = []
        self.lock = threading.Lock()

    def escutar_mensagens(self):
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(R_TOPIC)
        for mensagem in pubsub.listen():
            if mensagem['type'] == 'message':
                with self.lock:
                    self.fila_mensagens.append(mensagem['data'].decode())

    # def processar_mensagens(self):
    #     while True:
    #         if self.fila_mensagens:
    #             with self.lock:
    #                 mensagem = self.fila_mensagens[0]
    #                 id_cliente, timestamp, status = mensagem.split(':')
    #                 if status == 'ACQUIRE' and int(id_cliente) % NUM_ELEMENTOS_SYNC == self.id:
    #                     print(f"Elemento Sync {self.id} processando mensagem: {mensagem}")
    #                     self.recurso_r.acessar(id_cliente)
    #                     resposta = f"{id_cliente}:{timestamp}:COMMITTED"
    #                     self.redis_client.publish(R_RESPONSE_CHANNEL, resposta)  # Enviar para o canal de respostas
    #                     self.fila_mensagens.pop(0)
    #                 else:
    #                     time.sleep(0.1)
    def processar_mensagens(self):
        while True:
            if self.fila_mensagens:
                with self.lock:
                    mensagem = self.fila_mensagens[0]
                    id_cliente, timestamp, status = mensagem.split(':')
                    if status == 'ACQUIRE' and int(id_cliente) % NUM_ELEMENTOS_SYNC == self.id:
                        print(f"Elemento Sync {self.id} processando mensagem: {mensagem}")
                        self.recurso_r.acessar(id_cliente)
                        resposta = f"{id_cliente}:{timestamp}:COMMITTED"
                        self.redis_client.publish(R_RESPONSE_CHANNEL, resposta)  # Enviar para o canal de respostas
                        self.fila_mensagens.pop(0)
                    else:
                        time.sleep(0.1)

if __name__ == '__main__':
    # Criação do recurso R
    recurso_r = RecursoR()

    # Configuração do Redis
    redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT)

    # Criação do elemento do Cluster Sync
    elemento_sync = ElementoClusterSync(1, redis_client, recurso_r)  # Adapte o ID do elemento se necessário

    # Inicialização das threads
    threads = [
        threading.Thread(target=elemento_sync.escutar_mensagens),
        threading.Thread(target=elemento_sync.processar_mensagens)
    ]

    # Inicia as threads
    for thread in threads:
        thread.start()

    # Aguarda o término das threads (opcional)
    for thread in threads:
        thread.join()
