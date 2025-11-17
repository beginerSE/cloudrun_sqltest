# app.py
import os
import psycopg2
from flask import Flask, request, jsonify

app = Flask(__name__)

# ---- 環境変数から DB 接続情報を取得 ----
DB_HOST = os.environ.get("DB_HOST", "34.41.230.82")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "sampledb")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")


def get_connection():
    """毎回シンプルに接続を作る最小構成"""
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )
    return conn


@app.route("/")
def root():
    return jsonify(
        {
            "message": "Cloud Run + Cloud SQL minimal CRUD API",
            "endpoints": ["/items (GET, POST)", "/items/<id> (GET, PUT, DELETE)"],
        }
    )


# ---- CREATE & READ ALL ----
@app.route("/items", methods=["GET", "POST"])
def items():
    if request.method == "GET":
        # 一覧取得
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, description FROM items ORDER BY id;")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        items = [
            {"id": r[0], "name": r[1], "description": r[2]}
            for r in rows
        ]
        return jsonify(items)

    elif request.method == "POST":
        data = request.get_json() or {}
        name = data.get("name")
        description = data.get("description")

        if not name:
            return jsonify({"error": "name is required"}), 400

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO items (name, description) VALUES (%s, %s) RETURNING id;",
            (name, description),
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"id": new_id, "name": name, "description": description}), 201


# ---- READ ONE / UPDATE / DELETE ----
@app.route("/items/<int:item_id>", methods=["GET", "PUT", "DELETE"])
def item_detail(item_id):
    if request.method == "GET":
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, description FROM items WHERE id = %s;",
            (item_id,),
        )
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row is None:
            return jsonify({"error": "not found"}), 404

        return jsonify({"id": row[0], "name": row[1], "description": row[2]})

    elif request.method == "PUT":
        data = request.get_json() or {}
        name = data.get("name")
        description = data.get("description")

        if not name:
            return jsonify({"error": "name is required"}), 400

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE items SET name = %s, description = %s WHERE id = %s;",
            (name, description, item_id),
        )
        updated = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()

        if updated == 0:
            return jsonify({"error": "not found"}), 404

        return jsonify({"id": item_id, "name": name, "description": description})

    elif request.method == "DELETE":
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM items WHERE id = %s;", (item_id,))
        deleted = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()

        if deleted == 0:
            return jsonify({"error": "not found"}), 404

        return jsonify({"status": "deleted"})


# Cloud Run で直接実行されることはあまり無いが、ローカル動作用
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
