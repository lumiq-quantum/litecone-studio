from flask import Flask, request, jsonify
import os

app = Flask(__name__)
call_count = 0
fail_count = int(os.getenv('FAIL_COUNT', '5'))

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/', methods=['POST'])
def process():
    global call_count
    call_count += 1
    print(f"Call #{call_count}")
    
    if call_count <= fail_count:
        print(f"  → Failing (call {call_count}/{fail_count})")
        return jsonify({
            "jsonrpc": "2.0",
            "id": request.json.get('id'),
            "error": {"code": -32000, "message": f"Simulated failure {call_count}/{fail_count}"}
        }), 500
    else:
        print(f"  → Success (call {call_count})")
        return jsonify({
            "jsonrpc": "2.0",
            "id": request.json.get('id'),
            "result": {
                "status": {"state": "completed"},
                "artifacts": [{"parts": [{"kind": "text", "text": f"Success after {fail_count} failures!"}]}]
            }
        }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8090)
