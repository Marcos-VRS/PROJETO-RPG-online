"""Smoke test do lock — sem UI."""
import json
import os
import sys
import time
from pathlib import Path

# Override pra não tocar o OneDrive de verdade durante o teste.
TEST_HOME = Path(os.environ["TEMP"]) / "roll3d6_lock_test"
TEST_HOME.mkdir(parents=True, exist_ok=True)

from desktop import lock, runtime_config, tunnel  # noqa: E402

# --- 1. lock vazio: read_existing retorna None
l = lock.SessionLock(TEST_HOME)
if l.path.exists():
    l.path.unlink()
assert l.read_existing() is None, "deveria estar livre"
print("[1] livre quando arquivo não existe — OK")

# --- 2. acquire normal
ok = l.acquire()
assert ok, "acquire deveria ter sucesso"
assert l.path.exists(), "lock file não foi criado"
print(f"[2] acquire OK — {l.path}")

# --- 3. read_existing ignora nosso próprio PID
assert l.read_existing() is None, "deveria ignorar próprio lock"
print("[3] read_existing ignora nosso próprio lock — OK")

# --- 4. simular lock de outro PC (modifica o JSON)
data = json.loads(l.path.read_text(encoding="utf-8"))
data["pc"] = "OTHER-PC"
data["pid"] = 99999
data["heartbeat"] = time.time()  # fresh
l.path.write_text(json.dumps(data), encoding="utf-8")

l2 = lock.SessionLock(TEST_HOME)
existing = l2.read_existing()
assert existing is not None, "deveria ver lock do outro PC"
assert existing["pc"] == "OTHER-PC"
print(f"[4] lock de outro PC visível — pc={existing['pc']}")

# --- 5. acquire (sem force) falha quando outro lock fresco
ok = l2.acquire(force=False)
assert not ok, "acquire não-force deveria falhar"
print("[5] acquire sem force falha quando há lock alheio — OK")

# --- 6. acquire com force sobrescreve
ok = l2.acquire(force=True)
assert ok, "force acquire deveria ter sucesso"
data = json.loads(l2.path.read_text(encoding="utf-8"))
assert data["pid"] == os.getpid(), "lock não foi sobrescrito"
print("[6] force acquire sobrescreve — OK")

# --- 7. stale lock é tratado como livre
data["heartbeat"] = time.time() - 10 * 60  # 10 min atrás
data["pc"] = "OTHER-PC"
data["pid"] = 99999
l.path.write_text(json.dumps(data), encoding="utf-8")
l3 = lock.SessionLock(TEST_HOME)
assert l3.read_existing() is None, "lock stale deveria ser ignorado"
print("[7] lock stale (>6min) tratado como livre — OK")

# --- 8. release
l2.release()
print(f"[8] release OK. path exists agora? {l2.path.exists()}")

# --- 9. cloudflared_path agora é per-PC, não home
home_onedrive = Path(os.environ.get("OneDrive", "")) / "roll3d6_fake"
cf = tunnel.cloudflared_path(home_onedrive)
print(f"[9] cloudflared_path com home_onedrive='{home_onedrive}'")
print(f"    -> {cf}")
assert "OneDrive" not in str(cf), f"cloudflared NÃO deveria estar no OneDrive (got {cf})"
print("    confirmado: não está no OneDrive")

# limpeza
import shutil
shutil.rmtree(TEST_HOME, ignore_errors=True)
print("\nTODOS OS TESTES PASSARAM")
