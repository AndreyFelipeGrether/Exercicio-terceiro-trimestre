from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uuid

app = FastAPI(title="Mohamed Light")

# Banco de dados em memória
tarefas_db = {}

# Modelo de dados
class Tarefa(BaseModel):
    id: str | None = None
    titulo: str = Field(..., min_length=3)
    descricao: str | None = None
    concluida: bool = False


# Criar tarefa
@app.post("/tarefas", status_code=201)
def criar_tarefa(tarefa: Tarefa):
    if not tarefa.titulo or len(tarefa.titulo) < 3:
        raise HTTPException(status_code=422, detail="Título deve ter pelo menos 3 caracteres.")

    tarefa.id = str(uuid.uuid4())
    tarefas_db[tarefa.id] = tarefa
    return tarefa


# Listar todas as tarefas
@app.get("/tarefas")
def listar_tarefas():
    return list(tarefas_db.values())


# Obter tarefa por ID
@app.get("/tarefas/{id}")
def obter_tarefa(id: str):
    tarefa = tarefas_db.get(id)
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")
    return tarefa


# Atualizar tarefa
@app.put("/tarefas/{id}")
def atualizar_tarefa(id: str, dados: Tarefa):
    tarefa = tarefas_db.get(id)
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")
    if not dados.titulo or len(dados.titulo) < 3:
        raise HTTPException(status_code=422, detail="Título inválido.")

    dados.id = id
    tarefas_db[id] = dados
    return dados


# Deletar tarefa
@app.delete("/tarefas/{id}", status_code=204)
def deletar_tarefa(id: str):
    if id not in tarefas_db:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")
    del tarefas_db[id]
    return
----------------------------------------------------------------------------------------

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_criar_tarefa_sucesso():
    response = client.post("/tarefas", json={"titulo": "Estudar", "descricao": "Revisar FastAPI"})
    assert response.status_code == 201
    assert response.json()["titulo"] == "Estudar"


def test_criar_tarefa_sem_titulo():
    response = client.post("/tarefas", json={"descricao": "Sem título"})
    assert response.status_code in (400, 422)


def test_listar_tarefas_vazio():
    client.delete("/tarefas")  # limpar db, se necessário
    response = client.get("/tarefas")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_criar_e_listar_tarefa():
    client.post("/tarefas", json={"titulo": "Nova tarefa"})
    response = client.get("/tarefas")
    assert len(response.json()) >= 1


def test_buscar_tarefa_por_id():
    nova = client.post("/tarefas", json={"titulo": "Buscar tarefa"}).json()
    response = client.get(f"/tarefas/{nova['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == nova["id"]


def test_buscar_tarefa_inexistente():
    response = client.get("/tarefas/999")
    assert response.status_code == 404


def test_atualizar_tarefa():
    nova = client.post("/tarefas", json={"titulo": "Antiga"}).json()
    response = client.put(f"/tarefas/{nova['id']}", json={
        "titulo": "Atualizada",
        "descricao": "Teste",
        "concluida": True
    })
    assert response.status_code == 200
    assert response.json()["titulo"] == "Atualizada"


def test_atualizar_tarefa_inexistente():
    response = client.put("/tarefas/999", json={"titulo": "Nada"})
    assert response.status_code == 404


def test_deletar_tarefa():
    nova = client.post("/tarefas", json={"titulo": "Excluir"}).json()
    response = client.delete(f"/tarefas/{nova['id']}")
    assert response.status_code == 204
    response2 = client.get(f"/tarefas/{nova['id']}")
    assert response2.status_code == 404
