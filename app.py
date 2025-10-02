import os
import json
from flask import Flask, request, jsonify, render_template_string

class Storage:
    def add(self, item): raise NotImplementedError
    def list(self): raise NotImplementedError

class RedisStorage(Storage):
    def __init__(self, url):
        import redis
        self.r = redis.from_url(url, decode_responses=True)
        self.key = "items"

    def add(self, item):
        self.r.rpush(self.key, json.dumps(item))

    def list(self):
        vals = self.r.lrange(self.key, 0, -1)
        return [json.loads(v) for v in vals]

class MemoryStorage(Storage):
    def __init__(self):
        self.items = []

    def add(self, item):
        self.items.append(item)

    def list(self):
        return list(self.items)

def create_app():
    app = Flask(__name__)

    redis_url = os.environ.get("REDIS_URL")
    use_mem = os.environ.get("USE_MEMORY_DB", "0") == "1"

    if use_mem or not redis_url:
        storage = MemoryStorage()
        app.logger.info("Using in-memory storage")
    else:
        storage = RedisStorage(redis_url)
        app.logger.info(f"Using Redis at {redis_url}")

    app.storage = storage

    # HTML template for the form and output
    HTML_TEMPLATE = '''
    <!doctype html>
    <html>
    <head><title>Simple Data App</title></head>
    <body>
        <h1>Enter your value:</h1>
        <form method="POST">
            <input type="text" name="value" placeholder="Type something..." required>
            <button type="submit">Add</button>
        </form>
        {% if message %}
            <h2>{{ message }}</h2>
        {% endif %}
        <h3>All Values:</h3>
        <ul>
            {% for item in items %}
                <li>{{ item['value'] }}</li>
            {% endfor %}
        </ul>
        <p><a href="/data">View as JSON</a> | <a href="/health">Health Check</a></p>
    </body>
    </html>
    '''

    @app.route("/", methods=["GET", "POST"])
    def index():
        message = None
        if request.method == "POST":
            value = request.form.get("value")
            if value:
                item = {"value": value}
                app.storage.add(item)
                message = f"Added: {value}"
            else:
                message = "Error: Missing value!"

        # Get all items
        items = app.storage.list()
        return render_template_string(HTML_TEMPLATE, message=message, items=items)

    @app.route("/data", methods=["POST"])
    def post_data():
        payload = request.get_json(silent=True) or {}
        value = payload.get("value")
        if value is None:
            return jsonify({"error": "missing 'value' in JSON body"}), 400
        item = {"value": value}
        app.storage.add(item)
        return jsonify(item), 201

    @app.route("/data", methods=["GET"])
    def get_data():
        return jsonify(app.storage.list()), 200

    @app.route("/health", methods=["GET"])
    def health():
        try:
            _ = app.storage.list()
            return jsonify({"status": "ok"}), 200
        except Exception as e:
            app.logger.exception("health check failed")
            return jsonify({"status": "error", "error": str(e)}), 500

    return app

if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", "8080"))   
    app.run(host="0.0.0.0", port=port)