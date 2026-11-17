from pathlib import Path
import numpy as np
import pytest
from fastapi.testclient import TestClient
from app.core.config import ROOT, Settings
from app.main import create_app
from app.ml.inference import ModelService
from tests.test_preprocessing import image_bytes

class StubService(ModelService):
    """Explicit deterministic unit-test double; integration test uses real weights."""
    def load(self):
        self.metadata={"version":"unit-test"}
        self.model=lambda tensor,training: np.array([[0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.9,0.02,0.01]])

@pytest.fixture
def client():
    settings=Settings(app_env="test",rate_limit_enabled=False)
    with TestClient(create_app(settings,StubService(settings))) as client:
        yield client

def test_health_and_ready(client):
    assert client.get("/healthz").json()=={"status":"ok"}
    assert client.get("/readyz").status_code==200
    assert client.get("/api/v1/model/info").json()["version"]=="unit-test"

def test_prediction_schema(client):
    response=client.post("/api/v1/predict",files={"file":("digit.png",image_bytes(),"image/png")})
    assert response.status_code==200
    data=response.json()
    assert data["prediction"]==7
    assert len(data["probabilities"])==10
    assert sum(data["probabilities"])==pytest.approx(1)
    assert data["top_predictions"]==sorted(data["top_predictions"],key=lambda x:-x["confidence"])
    assert len(data["top_predictions"])==3
    assert data["processed_image"].startswith("data:image/png;base64,")
    assert data["processing_time_ms"]>0
    assert response.headers["x-content-type-options"]=="nosniff"

@pytest.mark.parametrize("mime,data,status",[("text/plain",b"bad",415),("image/png",b"bad",400),("image/png",b"",400)])
def test_validation(client,mime,data,status):
    response=client.post("/api/v1/predict",files={"file":("input",data,mime)})
    assert response.status_code==status
    assert isinstance(response.json()["error"]["message"],str)

def test_missing_form_field(client):
    assert client.post("/api/v1/predict").status_code==422

def test_missing_model():
    settings=Settings(app_env="test",model_path=Path("models/nonexistent.keras"))
    with TestClient(create_app(settings)) as client:
        assert client.get("/healthz").status_code==200
        assert client.get("/readyz").status_code==503
        assert client.post("/api/v1/predict",files={"file":("digit.png",image_bytes(),"image/png")}).status_code==503

def test_cors(client):
    response=client.options("/api/v1/predict",headers={"Origin":"http://localhost:5173","Access-Control-Request-Method":"POST"})
    assert response.headers["access-control-allow-origin"]=="http://localhost:5173"
    response=client.options("/api/v1/predict",headers={"Origin":"https://attacker.example","Access-Control-Request-Method":"POST"})
    assert "access-control-allow-origin" not in response.headers

def test_oversized_upload(client):
    response=client.post("/api/v1/predict",files={"file":("big.png",b"0"*(5*1024*1024+1),"image/png")})
    assert response.status_code==413

def test_body_limit(client):
    assert client.post("/api/v1/predict",content=b"0"*(6*1024*1024)).status_code==413

def test_rate_limit():
    settings=Settings(app_env="test",rate_limit_per_minute=1)
    with TestClient(create_app(settings,StubService(settings))) as client:
        assert client.post("/api/v1/predict").status_code==422
        response=client.post("/api/v1/predict")
        assert response.status_code==429
        assert response.headers["Retry-After"]=="60"

def test_config_rejects_unsafe_origins():
    with pytest.raises(ValueError):
        create_app(Settings(cors_origins="*"))
    with pytest.raises(ValueError):
        create_app(Settings(app_env="production",cors_origins="http://example.com"))

@pytest.mark.skipif(not (ROOT/"models/neuralink.keras").exists(),reason="Train the CNN before real-model integration")
def test_real_model():
    settings=Settings(app_env="test",rate_limit_enabled=False)
    with TestClient(create_app(settings)) as client:
        assert client.get("/readyz").status_code==200
        sample=(ROOT/"models/samples/digit-7.png").read_bytes()
        response=client.post("/api/v1/predict",files={"file":("digit.png",sample,"image/png")})
        assert response.status_code==200
        data=response.json()
        assert data["model_version"]=="1.0.0"
        assert data["prediction"]==7
        assert len(data["probabilities"])==10


def test_feature_maps_real_model():
    if not (ROOT/"models/neuralink.keras").exists() or not (ROOT/"models/metadata.json").exists():
        pytest.skip("Train the model before activation integration")
    settings=Settings(app_env="test",rate_limit_enabled=False)
    with TestClient(create_app(settings)) as client:
        sample=(ROOT/"models/samples/digit-7.png").read_bytes()
        response=client.post("/api/v1/visualize",files={"file":("digit.png",sample,"image/png")})
        assert response.status_code==200
        maps=response.json()["feature_maps"]
        assert [m["layer"] for m in maps]==["conv1","conv2"]
        assert all(len(m["images"])==8 for m in maps)
        assert all(image.startswith("data:image/png;base64,") for m in maps for image in m["images"])


def test_unknown_route_has_consistent_error(client):
    response=client.get("/does-not-exist")
    assert response.status_code==404
    assert response.json()=={"error":{"code":"http_404","message":"Not Found"}}

@pytest.mark.parametrize("origin",["https://", "https://example.com/path", "https://user:secret@example.com", "*", "https://example.com?query=true"])
def test_invalid_origins(origin):
    with pytest.raises(ValueError):
        create_app(Settings(cors_origins=origin))
