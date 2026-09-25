import base64
import json
import sqlite3
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from lumina.api import create_app

ROOT = Path(__file__).resolve().parent
PROMPTS = [
    "A night-time observatory dashboard with a dark navy background, a large circular moon, thin constellation lines, a red warning accent, and a small cyan telemetry panel",
    "A clean product-launch poster with a white background, cobalt blue rectangle, three stacked feature cards, a high-contrast headline reading LUMINA, and a color bar along the bottom",
    "A traffic operations map represented as a dark grid, three colored route lines, four circular station markers, a yellow incident region, and a compact legend",
    "A painterly mountain landscape at sunset with a violet sky, orange horizon, three mountain silhouettes, a lake reflection, and a small moon",
    "A cybersecurity incident response board with a charcoal background, red alert card, green recovered card, blue timeline, and a centered title SAFE MODE",
    "A scientific poster about orbital mechanics with a black background, an elliptical orbit, a bright planet, a smaller moon, arrows, and a white caption block",
    "An accessibility-first infographic with a cream background, large blue title, three high-contrast cards, readable labels, and a green completion badge",
    "A retro-futuristic control room with a dark purple background, neon magenta geometry, cyan panels, orange status lights, and a large central circular display",
]

def save_image(response, folder, name):
    payload = response.json()
    if "image_base64" in payload:
        (folder / f"{name}.png").write_bytes(base64.b64decode(payload["image_base64"]))
    return payload

def main():
    with TemporaryDirectory() as temp:
        client = TestClient(create_app(output_dir=temp))
        records = []
        health = client.get("/health")
        records.append({"kind": "health", "request": {"method": "GET", "path": "/health"}, "response": health.json(), "status": health.status_code})
        for index, prompt in enumerate(PROMPTS, 1):
            folder = ROOT / "images"
            folder.mkdir(exist_ok=True)
            create = client.post("/v1/images", json={"prompt": prompt, "width": 768, "height": 512})
            created = save_image(create, folder, f"prompt-{index:02d}-create") if create.status_code == 201 else create.json()
            record = {"kind": "complex_prompt", "number": index, "prompt": prompt, "create": {"request": {"prompt": prompt, "width": 768, "height": 512}, "status": create.status_code, "response": created}}
            if create.status_code == 201:
                image = created["image_base64"]
                edit = client.post("/v1/images/edit", json={"image_base64": image, "operation": "draw_text", "params": {"text": f"TEST {index:02d}", "xy": [24, 24], "size": 32, "fill": "#ffffff"}})
                record["edit"] = {"status": edit.status_code, "response": save_image(edit, folder, f"prompt-{index:02d}-edit") if edit.status_code == 200 else edit.json()}
                analyze = client.post("/v1/images/analyze", files={"image": (f"prompt-{index:02d}.png", base64.b64decode(image), "image/png")})
                record["analyze"] = {"status": analyze.status_code, "response": analyze.json()}
                if edit.status_code == 200:
                    compare = client.post("/v1/images/compare", json={"original_base64": image, "candidate_base64": edit.json()["image_base64"]})
                    record["compare"] = {"status": compare.status_code, "response": compare.json()}
            scene_seed = uuid.uuid4().hex
            scene = client.post("/v1/scenes/render", json={"width": 960, "height": 540, "background": "#101827", "idempotency_key": scene_seed, "layers": [
                {"id": "title", "type": "text", "text": "LUMINA RUNTIME", "xy": [40, 48], "size": 34, "fill": "#f8fafc"},
                {"id": "panel", "type": "rectangle", "box": [40, 120, 920, 500], "fill": "#1d4ed8"},
                {"id": "orb", "type": "ellipse", "box": [390, 170, 570, 350], "fill": "#22d3ee"},
                {"id": "status", "type": "text", "text": "CREATE  →  ANALYZE  →  REVISE", "xy": [70, 450], "size": 20, "fill": "#ffffff"},
            ]})
            scene_data = scene.json()
            if scene.status_code == 200 and "artifact_id" in scene_data:
                scene_file = client.get(f"/v1/artifacts/{scene_data['artifact_id']}/content")
                (ROOT / "canvases" / f"scene-{index:02d}.png").write_bytes(scene_file.content)
            record["scene"] = {"status": scene.status_code, "response": scene_data}
            records.append(record)
        metrics = client.get("/v1/metrics")
        records.append({"kind": "metrics", "status": metrics.status_code, "response": metrics.json()})
        db = Path(temp) / "jobs.sqlite3"
        with sqlite3.connect(db) as conn:
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        records.append({"kind": "local_database", "path": str(db), "tables": tables})
        (ROOT / "responses.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
        summary = {
            "prompts": len(PROMPTS),
            "create_successes": sum(r.get("create", {}).get("status") == 201 for r in records if r.get("kind") == "complex_prompt"),
            "edit_successes": sum(r.get("edit", {}).get("status") == 200 for r in records if r.get("kind") == "complex_prompt"),
            "analyze_successes": sum(r.get("analyze", {}).get("status") == 200 for r in records if r.get("kind") == "complex_prompt"),
            "compare_successes": sum(r.get("compare", {}).get("status") == 200 for r in records if r.get("kind") == "complex_prompt"),
            "scene_successes": sum(r.get("scene", {}).get("status") == 200 for r in records if r.get("kind") == "complex_prompt"),
            "health_status": health.status_code,
            "issues": [],
            "observations": [
                "The default canvas backend is deterministic and validates the complete request/response path; it is not an AI image model.",
                "Complex prompts exercise structured HTTP creation, analysis, declarative editing, comparison, and scene composition.",
                "SQLite is used for local job persistence and requires no Docker service.",
            ],
        }
        (ROOT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary, indent=2))
        if summary["create_successes"] != len(PROMPTS) or summary["scene_successes"] != len(PROMPTS):
            raise SystemExit(1)

if __name__ == "__main__":
    main()
