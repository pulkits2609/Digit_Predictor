"""Verify a running, genuinely trained API using an image supplied on the CLI."""
import argparse
import json
from pathlib import Path
import urllib.error
import urllib.request
import uuid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    for endpoint in ("/healthz", "/readyz", "/api/v1/model/info"):
        with urllib.request.urlopen(base + endpoint, timeout=30) as response:
            assert response.status == 200, endpoint
            json.load(response)
    boundary = uuid.uuid4().hex
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
            f"filename=\"sample.png\"\r\nContent-Type: image/png\r\n\r\n").encode()
    body += args.image.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    request = urllib.request.Request(base + "/api/v1/predict", data=body, headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(request, timeout=60) as response:
        result = json.load(response)
    probabilities = result["probabilities"]
    assert len(probabilities) == 10
    assert all(0 <= value <= 1 for value in probabilities)
    assert abs(sum(probabilities) - 1) < 1e-4
    ranking = sorted(range(10), key=lambda digit: probabilities[digit], reverse=True)
    assert result["prediction"] == ranking[0]
    assert abs(result["confidence"] - probabilities[ranking[0]]) < 1e-6
    assert [item["digit"] for item in result["top_predictions"]] == ranking[:3]
    assert result["processed_image"].startswith("data:image/png;base64,")
    assert result["processing_time_ms"] >= 0
    print(json.dumps({"status": "passed", "prediction": result["prediction"],
                      "confidence": result["confidence"],
                      "processing_time_ms": result["processing_time_ms"]}, indent=2))


if __name__ == "__main__":
    main()
