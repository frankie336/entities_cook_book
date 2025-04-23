# recipes/files/basic_file_client_crud.py
"""
Cookbook Demo: FileClient CRUD
──────────────────────────────

0.  SDK / env setup
1.  UPLOAD  →  /v1/uploads
2.  READ    →  /v1/files/{id}
3.  SIGNED  →  /v1/files/{id}/signed‑url
4.  BASE64  →  /v1/files/{id}/base64   (optional)
5.  DELETE  →  /v1/files/{id}
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from projectdavid import Entity

# ─────────────────────────────────────────────────────────────────────────────
# 0.  SDK init + env
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv()

client = Entity(
    base_url=os.getenv("BASE_URL", "http://localhost:9000"),
    api_key=os.getenv("ADMIN_API_KEY"),        # X‑API‑Key for auth
)

file_client = client.files                      # ⇐ this is the FileClient wrapper

# Test asset (any small txt file will do)
TEST_FILE = Path(__file__).parent / "hello_world.txt"
TEST_FILE.write_text("Hello, Project David!")   # create on the fly if absent

# ─────────────────────────────────────────────────────────────────────────────
# 1.  UPLOAD
# ─────────────────────────────────────────────────────────────────────────────
print("\n[UPLOAD] …")
upload_resp = file_client.upload_file(
    file_path=str(TEST_FILE),
    purpose="assistants",
)
print(upload_resp.model_dump_json(indent=2))

file_id = upload_resp.id                      # keep for later steps

# ─────────────────────────────────────────────────────────────────────────────
# 2.  READ (metadata)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[READ] /v1/files/{id} …")
meta = file_client.retrieve_file(file_id)
print(meta.model_dump_json(indent=2))

# ─────────────────────────────────────────────────────────────────────────────
# 3.  SIGNED URL  (download link good for 5 minutes)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[SIGNED URL] …")
signed = file_client.get_signed_url(
    file_id=file_id,
    expires_in=300,          # seconds
    use_real_filename=True,
)
print(signed or "No URL returned")

# ─────────────────────────────────────────────────────────────────────────────
# 4.  BASE64  (optional convenience endpoint)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[BASE64] …")
base64_blob = file_client.get_file_as_base64(file_id)
print(f"{base64_blob[:60]}…")   # preview first 60 chars

# ─────────────────────────────────────────────────────────────────────────────
# 5.  DELETE
# ─────────────────────────────────────────────────────────────────────────────
print("\n[DELETE] …")
deleted = file_client.delete_file(file_id)
print("Deleted?" , deleted)

# ─────────────────────────────────────────────────────────────────────────────
# Done
# ─────────────────────────────────────────────────────────────────────────────
"""
Expected terminal output (abridged):

[UPLOAD] …
{
  "id": "file_DG3a…",
  "object": "file",
  "bytes": 23,
  "created_at": 1713792347,
  ...
}

[READ] /v1/files/{id} …
{ … same fields … }

[SIGNED URL] …
http://localhost:9000/v1/files/download?file_id=file_DG3a…&expires=…

[BASE64] …
SGVsbG8sIFByb2plY3QgRGF2aWQh…

[DELETE] …
Deleted?  True
"""
