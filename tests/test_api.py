from tests.conftest import login


def test_precisa_login(client):
    assert client.get("/api/projects").status_code == 401


def test_bloqueia_email_fora_da_gm(client):
    assert login(client, email="alguem@gmail.com").status_code == 403


def test_portfolio_e_alertas(client):
    login(client)
    projects = client.get("/api/projects").json()
    assert len(projects) == 8
    dash = client.get("/api/dashboard").json()
    assert dash["kpis"]["stale"] == 2            # Armored (41 dias) e RESS (36 dias)
    assert sum(dash["by_phase"].values()) == 8


def test_mover_fase_respeita_lucro_e_grava_autor(client):
    login(client, role="Master")
    r = client.post("/api/projects/GP-342/phase", json={"phase": "Measure"})  # sem lucro estimado
    assert r.status_code == 422
    r = client.post("/api/projects/GP-330/phase", json={"phase": "Improve"})
    assert r.status_code == 200
    body = r.json()
    assert body["phase"] == "Improve"
    assert body["history"][0]["author"].startswith("Julia Viterbo")


def test_viewer_nao_edita(client):
    login(client, role="Viewer")
    assert client.post("/api/projects/GP-330/phase", json={"phase": "Improve"}).status_code == 403
    assert client.get("/api/admin/users").status_code == 403


def test_criar_projeto(client):
    login(client)
    data = {"name": "Teste", "type": "Opex", "phase": "Measure", "master": "Ana e Bia",
            "leader": "Leo", "value_musd": 0.5}
    assert client.post("/api/projects", json=data).status_code == 422          # dois Masters
    data["master"] = "Ana"
    r = client.post("/api/projects", json=data)
    assert r.status_code == 201 and r.json()["id"].startswith("OP-")


def test_meeting_notes_propoe_terca_e_libera_bloqueio(client):
    login(client)
    assert any(b["id"] == "GP-184" for b in client.get("/api/schedule").json()["blocked"])
    r = client.post("/api/projects/GP-184/notes", json={"text": "Piloto aprovado", "return_weeks": 4})
    assert r.status_code == 200
    meeting = r.json()["meeting"]
    assert meeting["state"] == "aguardando"
    assert not any(b["id"] == "GP-184" for b in client.get("/api/schedule").json()["blocked"])


def test_recusar_reagenda_e_aceitar_confirma(client):
    login(client)
    before = client.get("/api/projects/GP-034").json()["meeting"]["day"]
    after = client.post("/api/projects/GP-034/meeting/decline").json()["meeting"]
    assert after["day"] > before and after["state"] == "aguardando"
    assert client.post("/api/projects/GP-034/meeting/accept").json()["meeting"]["state"] == "confirmado"


def test_upload_zera_material_parado(client):
    login(client)
    r = client.post("/api/decks", json={"project_id": "GP-330", "file_type": "PPTX", "name": "Status"})
    assert r.status_code == 201 and r.json()["stale_days"] == 0
    decks = client.get("/api/decks").json()
    assert any(d["featured"] for d in decks["items"])


def test_pauta_e_nopex(client):
    login(client)
    day = client.get("/api/schedule").json()["slots"][0]["day"]
    rows = client.get(f"/api/schedule/{day}/agenda").json()
    assert rows[0]["project"] == "Abertura" and rows[-1]["project"] == "Encerramento"
    assert "dias" in client.post("/api/nopex", json={"question": "quem está atrasado?"}).json()["answer"]


def test_site_abre(client):
    r = client.get("/")
    assert r.status_code == 200 and "InnOpEx" in r.text
