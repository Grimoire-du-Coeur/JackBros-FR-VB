# -*- coding: utf-8 -*-
"""
Jack Bros Translation Tool Backend - FastAPI Server
Développé pour la traduction française de Jack Bros (Virtual Boy)
"""

import os
import sys
import json
import threading
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core_engine import ErreurEncodage, extract_all_text, encode_and_insert_text

app = FastAPI(title="Jack Bros Translation Tool Backend")

DIST_DIR = Path(__file__).parent / "dist"
RACINE = Path(__file__).resolve().parent.parent
PORT = 8000

if (DIST_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")

# Ce serveur écrit des fichiers à un chemin fourni par le client. Avec
# allow_origins=["*"], n'importe quelle page ouverte dans le navigateur
# pendant que l'outil tourne pouvait lui faire écrire sur le disque. Les
# requêtes de l'outil portent un corps JSON, donc elles passent par une
# requête préalable (preflight) : limiter les origines suffit à les bloquer.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def dossier_de_travail(chemin: str) -> Path:
    """Valide un dossier de destination : l'outil n'écrit que dans le dépôt.

    Deuxième barrière après le filtrage d'origines, pour qu'un chemin comme
    « C:\\Windows\\System32 » ou « ../.. » ne puisse pas servir de cible.
    """
    if not chemin:
        raise HTTPException(status_code=400, detail="Dossier de travail manquant.")
    resolu = Path(chemin).resolve()
    if resolu != RACINE and RACINE not in resolu.parents:
        raise HTTPException(
            status_code=403,
            detail=f"Écriture refusée hors du dépôt. Attendu : {RACINE}",
        )
    return resolu


def rom_existante(chemin: str) -> Path:
    """La ROM est lue, pas écrite : elle peut être n'importe où sur le disque,
    mais doit exister et être un fichier."""
    if not chemin:
        raise HTTPException(status_code=400, detail="Chemin de la ROM manquant.")
    rom = Path(chemin).resolve()
    if not rom.is_file():
        raise HTTPException(status_code=400, detail=f"ROM introuvable : {rom}")
    return rom

progress_state = {"current": 0, "task": "", "logs": []}
progress_lock = threading.Lock()

def update_progress(percent: float):
    with progress_lock:
        progress_state["current"] = int(percent * 100)

def reset_progress(task_name: str):
    with progress_lock:
        progress_state["task"] = task_name
        progress_state["current"] = 0
        progress_state["logs"].clear()

def get_logger(work_dir=None):
    def log(msg, level="info"):
        try:
            print(f"[{level.upper()}] {msg}")
        except Exception:
            pass
        with progress_lock:
            progress_state["logs"].append({"msg": msg, "type": level.upper()})
    return log

class RomRequest(BaseModel):
    rom_path: str
    work_dir: str

@app.get("/api/progress")
async def get_progress():
    with progress_lock:
        cur = progress_state["current"]
        task = progress_state["task"]
        response = {
            "current": cur,
            "task": task,
            "logs": list(progress_state["logs"])
        }
        progress_state["logs"].clear()
        if cur >= 100:
            progress_state["current"] = 0
            progress_state["task"] = ""
        return response

@app.get("/api/default-paths")
def api_default_paths():
    root_folder = Path(__file__).resolve().parent.parent
    return {
        "work_dir": str(root_folder),
        "rom_path": ""
    }

@app.post("/api/extract-text")
def api_extract_text(req: RomRequest):
    reset_progress("extract-text")
    logger = get_logger(req.work_dir)
    rom = rom_existante(req.rom_path)
    w = dossier_de_travail(req.work_dir)

    trad_dir = w / "traduction"
    trad_dir.mkdir(parents=True, exist_ok=True)
    # On écrit à côté de la traduction, jamais par-dessus : une extraction
    # faite depuis une ROM déjà patchée écraserait sinon le travail en cours.
    out_json = trad_dir / "JackBros_EXTRAIT.json"

    update_progress(0.2)
    try:
        count = extract_all_text(str(rom), str(out_json), logger)
    except (ErreurEncodage, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    update_progress(1.0)
    return {"status": "ok", "msg": f"{count} dialogues extraits dans {out_json.name}", "count": count}

@app.get("/api/get-translations")
def api_get_translations(work_dir: str):
    w = dossier_de_travail(work_dir)
    target = w / "traduction" / "JackBros_FR.json"
    if not target.exists():
        raise HTTPException(status_code=404, detail="Fichier traduction/JackBros_FR.json introuvable.")
    with open(target, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

@app.post("/api/save-translations")
def api_save_translations(payload: dict):
    work_dir = payload.get("work_dir")
    data = payload.get("data")
    if not work_dir or data is None:
        raise HTTPException(status_code=400, detail="Paramètres manquants")
    w = dossier_de_travail(work_dir)
    target = w / "traduction" / "JackBros_FR.json"
    with open(target, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    return {"status": "ok", "msg": "Traductions sauvegardées avec succès."}

@app.post("/api/rebuild-rom")
def api_rebuild_rom(req: RomRequest):
    reset_progress("rebuild-rom")
    logger = get_logger(req.work_dir)
    rom_orig = rom_existante(req.rom_path)
    w = dossier_de_travail(req.work_dir)

    with open(rom_orig, 'rb') as f:
        rom_bytes = f.read()

    update_progress(0.3)
    json_path = w / "traduction" / "JackBros_FR.json"
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Fichier traduction/JackBros_FR.json introuvable.")

    try:
        rom_bytes = encode_and_insert_text(rom_bytes, str(json_path), logger)
    except ErreurEncodage as exc:
        # Mieux vaut refuser de compiler qu'écrire une ROM aux dialogues
        # tronqués : le joueur ne verrait l'erreur qu'en jeu.
        logger(str(exc), "error")
        raise HTTPException(status_code=400, detail=str(exc))

    update_progress(0.8)
    out_rom = w / "Jack Bros (Fr).vb"
    with open(out_rom, 'wb') as f:
        f.write(rom_bytes)

    update_progress(1.0)
    logger(f"[OK] ROM compilée avec succès : {out_rom.name}", "success")
    return {"status": "ok", "msg": "ROM compilée avec succès !", "out_path": str(out_rom)}

@app.get("/")
def get_index():
    return FileResponse(str(DIST_DIR / "index.html"))

app.mount("/", StaticFiles(directory=str(DIST_DIR)), name="static")

if __name__ == "__main__":
    import uvicorn
    import webbrowser
    threading.Timer(1.2, lambda: webbrowser.open(f"http://127.0.0.1:{PORT}")).start()
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="info")
