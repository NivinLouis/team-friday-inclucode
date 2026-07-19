from fastapi.testclient import TestClient
from server import app
from pose_format import Pose

client = TestClient(app)

def test_api_success_ins():
    response = client.get("/spoken_text_to_signed_pose?text=hello&spoken=en&signed=ins")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    
    # Verify it is a valid Pose file
    pose = Pose.read(response.content)
    assert pose.body.data.shape[0] > 0

def test_api_success_ase():
    response = client.get("/spoken_text_to_signed_pose?text=goodbye&spoken=en&signed=ase")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    
    pose = Pose.read(response.content)
    assert pose.body.data.shape[0] > 0

def test_api_fingerspelling_fallback():
    # 'abcd' is not in lexicon, but should fingerspell and succeed
    response = client.get("/spoken_text_to_signed_pose?text=abcd&spoken=en&signed=ase")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    
    pose = Pose.read(response.content)
    assert pose.body.data.shape[0] > 0

def test_api_failure_invalid_spoken():
    response = client.get("/spoken_text_to_signed_pose?text=hello&spoken=fr&signed=ins")
    assert response.status_code == 400
    assert response.text == "The sign is unavailable."

def test_api_failure_invalid_signed():
    response = client.get("/spoken_text_to_signed_pose?text=hello&spoken=en&signed=fr")
    assert response.status_code == 400
    assert response.text == "The sign is unavailable."

def test_api_failure_empty_text():
    response = client.get("/spoken_text_to_signed_pose?text=&spoken=en&signed=ins")
    assert response.status_code == 400
    assert response.text == "The sign is unavailable."
