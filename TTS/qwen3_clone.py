import json
import os
import re
import subprocess
import tempfile
from pathlib import Path


class Qwen3Clone:
    def __init__(self):
        self.max_chars = 5000
        self.ref_audio = os.getenv(
            "QWEN3_REF_AUDIO",
            r"C:\Users\tarus\.openclaw\workspace\voice_samples\tarushv_ref_16k.wav",
        )
        self.ref_text_file = os.getenv(
            "QWEN3_REF_TEXT",
            r"C:\Users\tarus\.openclaw\workspace\voice_samples\tarushv_ref_transcript.txt",
        )
        self.clone_script = os.getenv(
            "QWEN3_CLONE_SCRIPT",
            r"C:\Users\tarus\.openclaw\workspace\qwen3_voice_clone.py",
        )
        self.python_exe = os.getenv(
            "QWEN3_PYTHON",
            r"C:\Users\tarus\.openclaw\workspace\.venv-qwen3-tts312\Scripts\python.exe",
        )
        self.ffmpeg_bin = os.getenv("QWEN3_FFMPEG", "ffmpeg")
        self.sox_dir = os.getenv(
            "QWEN3_SOX_DIR",
            r"C:\Users\tarus\AppData\Local\Microsoft\WinGet\Packages\ChrisBagwell.SoX_Microsoft.Winget.Source_8wekyb3d8bbwe\sox-14.4.2",
        )
        self.use_wsl = os.getenv("QWEN3_USE_WSL", "1").strip().lower() in {"1", "true", "yes"}
        self.wsl_distro = os.getenv("QWEN3_WSL_DISTRO", "Ubuntu-24.04")
        self.wsl_python = os.getenv("QWEN3_WSL_PYTHON", "/home/tarushv/.venvs/rhm/bin/python")
        self.worker_script = str(Path(__file__).with_name("qwen3_worker.py"))
        self._workers = {}

    def _prepare_text(self, text: str) -> str:
        # Keep script fidelity as close to original pipeline as possible.
        # Only normalize whitespace; do not lowercase or strip characters.
        return re.sub(r"\s+", " ", (text or "")).strip()

    def _split_sentences(self, text: str, max_chunk_chars: int = 900):
        # Split for generation stability, but NEVER truncate content.
        parts = re.split(r"(?<=[\.!?])\s+", text)
        parts = [p.strip() for p in parts if p and p.strip()]

        if not parts:
            parts = [text]

        chunks = []
        current = ""
        for part in parts:
            # If this sentence is huge, split by words while preserving all text.
            if len(part) > max_chunk_chars:
                words = part.split()
                seg = ""
                for w in words:
                    nxt = (seg + " " + w).strip()
                    if len(nxt) <= max_chunk_chars:
                        seg = nxt
                    else:
                        if seg:
                            chunks.append(seg)
                        seg = w
                if seg:
                    if current:
                        if len((current + " " + seg).strip()) <= max_chunk_chars:
                            current = (current + " " + seg).strip()
                        else:
                            chunks.append(current)
                            current = seg
                    else:
                        current = seg
                continue

            candidate = (current + " " + part).strip() if current else part
            if len(candidate) <= max_chunk_chars:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                current = part

        if current:
            chunks.append(current)

        return chunks

    def _to_wsl_path(self, p: str) -> str:
        p = str(p).replace('\\', '/')
        if len(p) >= 2 and p[1] == ':':
            drive = p[0].lower()
            return f"/mnt/{drive}{p[2:]}"
        return p

    def _build_base_cmd(self, chunk: str, out_wav: str, max_new_tokens: int = 220):
        if self.use_wsl:
            return [
                "wsl.exe",
                "-d",
                self.wsl_distro,
                "--",
                self.wsl_python,
                self._to_wsl_path(self.clone_script),
                "--text",
                chunk,
                "--language",
                "English",
                "--ref-audio",
                self._to_wsl_path(self.ref_audio),
                "--ref-text-file",
                self._to_wsl_path(self.ref_text_file),
                "--max-new-tokens",
                str(max_new_tokens),
                "--out",
                self._to_wsl_path(out_wav),
            ]
        return [
            self.python_exe,
            self.clone_script,
            "--text",
            chunk,
            "--language",
            "English",
            "--ref-audio",
            self.ref_audio,
            "--ref-text-file",
            self.ref_text_file,
            "--max-new-tokens",
            str(max_new_tokens),
            "--out",
            out_wav,
        ]

    def _start_wsl_worker(self, device: str, dtype: str, env: dict):
        key = (device, dtype)
        proc = self._workers.get(key)
        if proc and proc.poll() is None:
            return proc

        cmd = [
            "wsl.exe",
            "-d",
            self.wsl_distro,
            "--",
            self.wsl_python,
            self._to_wsl_path(self.worker_script),
            "--device",
            device,
            "--dtype",
            dtype,
            "--language",
            "English",
            "--ref-audio",
            self._to_wsl_path(self.ref_audio),
            "--ref-text-file",
            self._to_wsl_path(self.ref_text_file),
        ]
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
            env=env,
        )

        ready = proc.stdout.readline().strip() if proc.stdout else ""
        try:
            payload = json.loads(ready) if ready else {}
        except Exception:
            payload = {}
        if not payload.get("ready"):
            try:
                proc.kill()
            except Exception:
                pass
            return None

        self._workers[key] = proc
        return proc

    def _run_wsl_worker_request(self, proc, text: str, out_wav: str, max_tokens: int):
        if not proc or proc.poll() is not None or not proc.stdin or not proc.stdout:
            return False
        req = {
            "text": text,
            "out": self._to_wsl_path(out_wav),
            "language": "English",
            "max_new_tokens": int(max_tokens),
        }
        proc.stdin.write(json.dumps(req) + "\n")
        proc.stdin.flush()
        resp = proc.stdout.readline().strip()
        try:
            payload = json.loads(resp) if resp else {}
        except Exception:
            payload = {}
        return bool(payload.get("ok"))

    def _write_silence_wav(self, wav_path: Path, duration_sec: float = 0.4):
        subprocess.run(
            [
                self.ffmpeg_bin,
                "-y",
                "-f",
                "lavfi",
                "-i",
                "anullsrc=r=24000:cl=mono",
                "-t",
                f"{max(0.12, float(duration_sec)):.3f}",
                "-ac",
                "1",
                "-ar",
                "24000",
                str(wav_path),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def run(self, text: str, filepath: str, random_voice: bool = False):
        out_mp3 = Path(filepath)
        out_mp3.parent.mkdir(parents=True, exist_ok=True)

        text = self._prepare_text(text)
        if len(text) < 2:
            text = "..."
        chunks = self._split_sentences(text)

        env = os.environ.copy()
        if self.sox_dir and os.path.isdir(self.sox_dir):
            env["PATH"] = self.sox_dir + os.pathsep + env.get("PATH", "")
        env.setdefault("PYTHONUTF8", "1")

        with tempfile.TemporaryDirectory() as td:
            tmp_dir = Path(td)
            wav_paths = []

            for i, chunk in enumerate(chunks):
                tmp_wav = tmp_dir / f"part_{i:02d}.wav"

                attempts = [
                    ("cuda:0", "bfloat16", 220, 420),
                    ("cuda:0", "float16", 180, 360),
                    ("cpu", "float32", 180, 420),
                ]

                success = False
                for device, dtype, max_tokens, timeout_sec in attempts:
                    if self.use_wsl:
                        proc = self._start_wsl_worker(device, dtype, env)
                        try:
                            if proc and self._run_wsl_worker_request(proc, chunk, str(tmp_wav), max_tokens):
                                success = True
                                break
                        except Exception:
                            pass
                    else:
                        base_cmd = self._build_base_cmd(chunk, str(tmp_wav), max_new_tokens=max_tokens)
                        try:
                            subprocess.run(
                                base_cmd + ["--device", device, "--dtype", dtype],
                                check=True,
                                env=env,
                                timeout=timeout_sec,
                            )
                            success = True
                            break
                        except Exception:
                            continue

                if not success:
                    # Keep pipeline alive on rare model hangs/failures.
                    self._write_silence_wav(tmp_wav)

                wav_paths.append(tmp_wav)

            list_file = tmp_dir / "list.txt"
            with list_file.open("w", encoding="utf-8") as f:
                for p in wav_paths:
                    f.write(f"file '{str(p).replace('\\', '/')}'\n")

            merged_wav = tmp_dir / "merged.wav"
            subprocess.run(
                [
                    self.ffmpeg_bin,
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    str(list_file),
                    "-c",
                    "copy",
                    str(merged_wav),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            subprocess.run(
                [
                    self.ffmpeg_bin,
                    "-y",
                    "-i",
                    str(merged_wav),
                    "-ar",
                    "44100",
                    "-ac",
                    "1",
                    "-b:a",
                    "192k",
                    str(out_mp3),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
