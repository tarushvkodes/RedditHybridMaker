import argparse
import json
from pathlib import Path

import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel


def main():
    ap = argparse.ArgumentParser(description="Persistent Qwen3 TTS worker")
    ap.add_argument("--model", default="Qwen/Qwen3-TTS-12Hz-0.6B-Base")
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--dtype", default="bfloat16", choices=["float16", "bfloat16", "float32"])
    ap.add_argument("--language", default="English")
    ap.add_argument("--ref-audio", required=True)
    ap.add_argument("--ref-text-file", required=True)
    args = ap.parse_args()

    dtype = {
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
        "float32": torch.float32,
    }[args.dtype]

    ref_text = Path(args.ref_text_file).read_text(encoding="utf-8").strip()

    model = Qwen3TTSModel.from_pretrained(
        args.model,
        device_map=args.device,
        dtype=dtype,
    )

    print(json.dumps({"ready": True, "device": args.device, "dtype": args.dtype}), flush=True)

    for line in iter(input, ""):
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            if req.get("cmd") == "shutdown":
                print(json.dumps({"ok": True, "shutdown": True}), flush=True)
                break

            text = (req.get("text") or "").strip()
            out = req.get("out")
            max_new_tokens = int(req.get("max_new_tokens", 220))
            language = req.get("language", args.language)

            if not out:
                raise ValueError("missing out path")
            if not text:
                text = "..."

            wavs, sr = model.generate_voice_clone(
                text=text,
                language=language,
                ref_audio=args.ref_audio,
                ref_text=ref_text,
                x_vector_only_mode=False,
                max_new_tokens=max_new_tokens,
            )

            out_path = Path(out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            sf.write(str(out_path), wavs[0], sr)
            print(json.dumps({"ok": True, "out": str(out_path), "sr": int(sr)}), flush=True)
        except Exception as e:
            print(json.dumps({"ok": False, "error": str(e)}), flush=True)


if __name__ == "__main__":
    main()
