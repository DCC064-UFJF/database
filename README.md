# Repositório *database*
Esse é o repositório onde fica o projeto de banco de dados replicável.

# Para rodar:

Certifique-se de ter o docker-compose instalado e rode:

docker-compose up -d --build

# Para parar:

docker-compose down ou docker stop

# Para verificar o que está rodando:

docker-compose ps

# Para ver qual é o primary:

docker exec -it <nome-replica-healthy> mongosh --eval "rs.status()"

# Para matar o primary:

docker stop <nome-primary>

# Para ver qual a nova configuração do replica set:

docker exec -it <nome-replica-healthy> mongosh --eval "rs.status()"

# Para testar a consistência

## Ler da primária
curl http://localhost:5000/data/primary

## Ler da primeira secundária
curl http://localhost:5000/data/secondary1

## Ler da segunda secundária
curl http://localhost:5000/data/secondary2


# Para inserir dados

## Inserir na primária
curl -X POST http://localhost:5000/data/primary \
-H "Content-Type: application/json" \
-d '{"name": "Exemplo", "value": 123}'

## Inserir na primeira secundária
curl -X POST http://localhost:5000/data/secondary1 \
-H "Content-Type: application/json" \
-d '{"name": "Exemplo", "value": 123}'

## Inserir na segunda secundária
curl -X POST http://localhost:5000/data/secondary2 \
-H "Content-Type: application/json" \
-d '{"name": "Exemplo", "value": 123}'


# Para conferência

curl http://localhost:5000/replica-status
curl http://localhost:5000/is-primary/<nome-da-replica>

# IMPORTANTE

Em um MongoDB Replica Set, você não precisa se preocupar em conectar diretamente ao master/primary. Ao invés disso, você deve usar uma string de conexão que lista todos os membros do replica set. Essa string de conexão está no arquivo da aplicação de suporte *app.py*. O driver do MongoDB automaticamente gerencia a descoberta do primary e o failover.
Por exemplo, sua string de conexão deve ser algo como:

mongodb://localhost:27017,localhost:27018,localhost:27019/?replicaSet=rs0

Quando você usa esta string de conexão, o driver tenta conectar em qualquer um dos membros listados e descobre automaticamente qual é o primary atual. Se o primary falhar, o driver automaticamente: detecta a falha, aguarda a eleição do novo primary, e redireciona as operações de escrita para o novo primary.

Então ao invés de modificar seu código quando o primary muda, você deixa o driver do MongoDB gerenciar isso. É por isso que sua aplicação deve sempre usar a string de conexão com todos os membros do replica set.
