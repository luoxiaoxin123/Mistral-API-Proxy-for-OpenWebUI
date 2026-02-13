from flask import Flask, request, Response, stream_with_context
import requests
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
MISTRAL_API_BASE = "https://api.mistral.ai"
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "XXXXXXXXXXXXXXXXXXXXX")  # set via env or replace directly

# OpenWebUI may send OpenAI-specific fields that Mistral rejects with 422.
UNSUPPORTED_CHAT_FIELDS = {
    "logit_bias",
    "user",
    "additionalProp1",
    "stream_options",
    "enable_thinking",
    "thinking",
    "reasoning",
    "prediction",
    "parallel_tool_calls",
}

def build_streaming_response(response):
    excluded_headers = {
        'content-encoding', 'transfer-encoding', 'content-length',
        'connection', 'keep-alive', 'proxy-authenticate',
        'proxy-authorization', 'te', 'trailers', 'upgrade'
    }

    def generate():
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                yield chunk

    content_type = response.headers.get('Content-Type', 'application/json')
    flask_response = Response(
        stream_with_context(generate()),
        status=response.status_code,
        content_type=content_type
    )

    for k, v in response.headers.items():
        if k.lower() not in excluded_headers and k.lower() != 'content-type':
            flask_response.headers[k] = v

    return flask_response

def inject_auth_header(original_headers):
    headers = dict(original_headers)
    headers["Authorization"] = f"Bearer {MISTRAL_API_KEY}"
    headers.pop("Host", None)
    headers.pop("Accept-Encoding", None)  # prevent gzip
    return headers


def sanitize_chat_payload(json_payload):
    for field in UNSUPPORTED_CHAT_FIELDS:
        json_payload.pop(field, None)

    # Fix for Mistral API: ensure last message is NOT from assistant
    messages = json_payload.get("messages", [])
    if messages and messages[-1].get("role") == "assistant":
        messages.append({"role": "user", "content": "Continue response"})
        json_payload["messages"] = messages

    return json_payload


@app.route('/v1/chat/completions', methods=["POST"])
def intercept_and_forward():
    headers = inject_auth_header(request.headers)

    json_payload = request.get_json(force=True, silent=True)
    if not json_payload:
        return Response("Invalid JSON", status=400)

    json_payload = sanitize_chat_payload(json_payload)

    response = requests.post(
        f"{MISTRAL_API_BASE}/v1/chat/completions",
        json=json_payload,
        headers=headers,
        stream=True
    )

    if response.status_code >= 400:
        try:
            print(f"[Mistral upstream error] status={response.status_code} body={response.text[:2000]}")
        except Exception:
            pass

    response.raw.decode_content = True
    return build_streaming_response(response)

@app.route('/', defaults={'path': ''}, methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@app.route('/<path:path>', methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
def catch_all(path):
    method = request.method
    headers = inject_auth_header(request.headers)
    url = f"{MISTRAL_API_BASE}/{path}"

    kwargs = {
        "headers": headers,
        "params": request.args if method == "GET" else None,
        "data": request.get_data(),
    }

    response = requests.request(
        method,
        url,
        headers=headers,
        data=request.get_data(),
        stream=True
    )
    response.raw.decode_content = True
    return build_streaming_response(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6432)
