import sys
import os
import pytest
from fastapi.testclient import TestClient
from PIL import Image
import io
import json

# Add backend to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_parse_text_valid():
    text = "1. What is AI?\n- Definition: It is Artificial Intelligence."
    response = client.post("/api/parse-text", data={"text": text})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["questions"][0]["question"] == "What is AI?"

def test_parse_text_invalid():
    # Sending empty text or text without numbers
    text = "Just some random text."
    response = client.post("/api/parse-text", data={"text": text})
    assert response.status_code == 200 # It should just return 0 questions, not fail
    data = response.json()
    assert data["total"] == 0

def test_parse_docx_invalid_extension():
    # Attempt to upload a .exe file
    files = {'file': ('test.exe', b'content', 'application/octet-stream')}
    response = client.post("/api/parse-docx", files=files)

    # The backend (docx_parser.py) tries to parse it.
    # If it fails, main.py catches Exception and returns 400.
    # Note: docx_parser falls back to slow_parse_fallback which uses python-docx.
    # python-docx will raise an error if it's not a valid docx/zip.
    assert response.status_code == 400
    assert "Error parsing docx" in response.json()["detail"]

def test_parse_docx_gdoc():
    # Attempt to upload a .gdoc file
    files = {'file': ('test.gdoc', b'{"url": "..."}', 'application/json')}
    response = client.post("/api/parse-docx", files=files)
    assert response.status_code == 400
    assert "Google Docs shortcut files" in response.json()["detail"]

def test_generate_preview_valid():
    # Create a dummy image
    img = Image.new('RGB', (100, 100), color = 'red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    files = {'background': ('bg.png', img_byte_arr, 'image/png')}
    question_data = json.dumps({
        "number": 1,
        "question": "Test Q",
        "pointers": [["Label", "Content"]]
    })
    config = json.dumps({
        "instructor_name": "Test",
        "font_family": "Chalk"
    })

    response = client.post(
        "/api/generate-preview",
        files=files,
        data={"question_data": question_data, "config": config}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

def test_generate_preview_invalid_image():
    # Sending text content as image
    files = {'background': ('bg.png', b'not an image', 'image/png')}
    question_data = json.dumps({
        "number": 1,
        "question": "Test Q",
        "pointers": []
    })
    config = json.dumps({})

    response = client.post(
        "/api/generate-preview",
        files=files,
        data={"question_data": question_data, "config": config}
    )
    # Expecting 400 Bad Request now
    assert response.status_code == 400
    assert "Invalid image file" in response.json()["detail"]

def test_generate_pptx_valid():
    # Create a dummy image
    img = Image.new('RGB', (100, 100), color = 'blue')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    files = {'background': ('bg.png', img_byte_arr, 'image/png')}
    questions_data = json.dumps([{
        "number": 1,
        "question": "Test Q",
        "pointers": [["Label", "Content"]]
    }])
    config = json.dumps({
        "instructor_name": "Test",
        "font_family": "Chalk"
    })

    response = client.post(
        "/api/generate-pptx",
        files=files,
        data={"questions_data": questions_data, "config": config}
    )
    assert response.status_code == 200
    # Check for SSE
    content = response.content.decode('utf-8')
    assert "data: " in content
    assert "complete" in content

def test_generate_pptx_invalid_image():
    # Sending invalid image for PPTX generation
    files = {'background': ('bg.png', b'not an image', 'image/png')}
    questions_data = json.dumps([{
        "number": 1,
        "question": "Test Q",
        "pointers": []
    }])
    config = json.dumps({})

    response = client.post(
        "/api/generate-pptx",
        files=files,
        data={"questions_data": questions_data, "config": config}
    )

    # Since this is a streaming response, the status code will be 200,
    # but the stream should contain an error event.
    assert response.status_code == 200
    content = response.content.decode('utf-8')
    assert '"type": "error"' in content
    assert "Invalid image file" in content
