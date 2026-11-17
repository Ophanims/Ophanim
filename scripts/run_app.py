"""Own both local server processes and stop them together; no containers or databases."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
from http.client import HTTPConnection, HTTPException
from run_backend import ROOT, load_environment

RUNTIME_DIR = ROOT / "data" / "runtime"
PID_FILE = RUNTIME_DIR / "app.json"
BUILD_FILE = RUNTIME_DIR / "frontend-build.json"


def supervisor_pid():
    if not PID_FILE.exists():
        return None
    try:
        pid = json.loads(PID_FILE.read_text())["pid"]
        command = subprocess.run(["ps", "-p", str(pid), "-o", "command="], capture_output=True, text=True).stdout
        return pid if str(ROOT / "scripts" / "run_app.py") in command and " start" in command else None
    except (OSError, ValueError, KeyError):
        return None


def build_fingerprint(api_url):
    digest = hashlib.sha256(api_url.encode())
    frontend = ROOT / "frontend"
    paths = list((frontend / "src").rglob("*"))
    paths += [path for path in frontend.iterdir() if path.is_file() and path.name != "next-env.d.ts" and path.suffix in {".json", ".ts", ".mjs"}]
    for path in sorted(path for path in paths if path.is_file()):
        digest.update(str(path.relative_to(frontend)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def assert_port_available(port):
    if not 1 <= port <= 65535:
        raise RuntimeError("Ports must be between 1 and 65535.")
    with socket.socket() as connection:
        try:
            connection.bind(("127.0.0.1", port))
        except OSError as error:
            raise RuntimeError(f"Port {port} is occupied. Stop its owner or choose another port.") from error


class LocalApplication:
    def __init__(self, backend_port, frontend_port):
        self.backend_port = backend_port
        self.frontend_port = frontend_port
        self.processes = []
        self.stopping = threading.Event()
        self.environment = os.environ.copy()
        self.environment["NEXT_PUBLIC_API_URL"] = f"http://127.0.0.1:{backend_port}"
        self.environment.setdefault("MPLCONFIGDIR", str(RUNTIME_DIR / "matplotlib"))
        self.environment.setdefault("PYTHONUNBUFFERED", "1")
        self.environment.setdefault("NEXT_TELEMETRY_DISABLED", "1")

    def spawn(self, command, directory):
        process = subprocess.Popen(command, cwd=directory, env=self.environment, start_new_session=True)
        self.processes.append(process)
        return process

    def wait_process(self, process):
        while process.poll() is None:
            if self.stopping.wait(0.2):
                raise InterruptedError()
        if process.returncode:
            raise RuntimeError(f"A child process exited with code {process.returncode}")

    def prepare_frontend(self):
        frontend = ROOT / "frontend"
        if not (frontend / "node_modules" / "next" / "dist" / "bin" / "next").exists():
            raise RuntimeError("Frontend dependencies are missing. Run ./setup.sh first.")
        fingerprint = build_fingerprint(self.environment["NEXT_PUBLIC_API_URL"])
        try:
            previous = json.loads(BUILD_FILE.read_text()).get("fingerprint")
        except (OSError, ValueError):
            previous = None
        if previous != fingerprint or not (frontend / ".next" / "BUILD_ID").exists():
            print("Building frontend (subsequent starts reuse this build)…", flush=True)
            self.wait_process(self.spawn([shutil.which("npm"), "run", "build"], frontend))
            BUILD_FILE.write_text(json.dumps({"fingerprint": fingerprint}))

    def wait_backend(self, process):
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            if self.stopping.is_set():
                raise InterruptedError()
            if process.poll() is not None:
                raise RuntimeError("Backend exited before becoming ready.")
            connection = HTTPConnection("127.0.0.1", self.backend_port, timeout=1)
            try:
                connection.request("GET", "/health")
                response = connection.getresponse()
                response.read()
                if response.status == 200:
                    return
            except (OSError, HTTPException):
                pass
            finally:
                connection.close()
            self.stopping.wait(0.2)
        raise RuntimeError("Backend startup timed out.")

    def run(self):
        assert_port_available(self.backend_port)
        assert_port_available(self.frontend_port)
        if self.backend_port == self.frontend_port:
            raise RuntimeError("Frontend and backend must use different ports.")
        if not shutil.which("node") or not shutil.which("npm"):
            raise RuntimeError("Node.js and npm are required.")
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(PID_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, "w") as stream:
            json.dump({"pid": os.getpid(), "backend_port": self.backend_port, "frontend_port": self.frontend_port}, stream)
        for signum in (signal.SIGINT, signal.SIGTERM):
            signal.signal(signum, lambda *_: self.stopping.set())
        try:
            self.prepare_frontend()
            backend = self.spawn([sys.executable, str(ROOT / "scripts" / "run_backend.py"), "--port", str(self.backend_port)], ROOT)
            self.wait_backend(backend)
            frontend = self.spawn([shutil.which("node"), str(ROOT / "frontend" / "node_modules" / "next" / "dist" / "bin" / "next"),
                                   "start", "--hostname", "127.0.0.1", "--port", str(self.frontend_port)], ROOT / "frontend")
            print(f"Open http://127.0.0.1:{self.frontend_port}/ — Ctrl+C or ./stop.sh stops both servers.", flush=True)
            while not self.stopping.wait(0.5):
                if backend.poll() is not None or frontend.poll() is not None:
                    raise RuntimeError("A server exited; stopping the other server.")
        except InterruptedError:
            pass
        finally:
            self.close()
            PID_FILE.unlink(missing_ok=True)

    def close(self):
        active = [process for process in reversed(self.processes) if process.poll() is None]
        for process in active:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        for process in active:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()


def main():
    load_environment()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["start", "stop", "status"])
    parser.add_argument("--backend-port", type=int, default=int(os.environ.get("BACKEND_PORT", "8000")))
    parser.add_argument("--frontend-port", type=int, default=int(os.environ.get("FRONTEND_PORT", "3000")))
    arguments = parser.parse_args()
    pid = supervisor_pid()
    if arguments.action == "status":
        print(f"Running (PID {pid})" if pid else "Stopped")
    elif arguments.action == "stop":
        if not pid:
            print("Stopped")
            return
        os.kill(pid, signal.SIGTERM)
        deadline = time.monotonic() + 35
        while PID_FILE.exists() and time.monotonic() < deadline:
            time.sleep(0.2)
        if PID_FILE.exists():
            raise RuntimeError("Shutdown did not finish; inspect the startup terminal.")
        print("Stopped")
    else:
        if pid:
            raise RuntimeError(f"Already running (PID {pid}). Use ./stop.sh first.")
        PID_FILE.unlink(missing_ok=True)
        LocalApplication(arguments.backend_port, arguments.frontend_port).run()


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
