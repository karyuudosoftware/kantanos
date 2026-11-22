#!/usr/bin/env python3
"""Merges the trained Kan-chan add-on (output/kanchan-model/adapter) into a full bf16 copy of
Gemma 3 12B that Ollama can import (Ollama no longer takes LoRA add-ons). Works from the
cached 4-bit base one weight at a time, so it needs little memory. Run in the training venv:
  python merge.py [--out DIR]
then on Windows: ollama create kanchan -f output/kanchan-model/Modelfile --quantize q4_K_M"""
import argparse
import glob
import json
import os
import shutil

import torch
import bitsandbytes.functional as bnbf
from bitsandbytes.functional import QuantState
from safetensors import safe_open
from safetensors.torch import save_file

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "output", "kanchan-model")
BASE = glob.glob(os.path.join(os.environ.get("HF_HOME", "/root/hf"),
                              "hub/models--unsloth--gemma-3-12b-it-unsloth-bnb-4bit/snapshots/*"))[0]
SHARD = 4 << 30  # bytes per output file

ap = argparse.ArgumentParser()
ap.add_argument("--out", default=os.path.join(OUT, "merged"))
args = ap.parse_args()
os.makedirs(args.out, exist_ok=True)

# The add-on: "base_model.model.model.language_model.layers.N.x.y.lora_A.weight" pairs.
acfg = json.load(open(os.path.join(OUT, "adapter", "adapter_config.json")))
scale = acfg["lora_alpha"] / acfg["r"]
lora = {}
with safe_open(os.path.join(OUT, "adapter", "adapter_model.safetensors"), "pt") as f:
    for k in f.keys():
        name, part = k.rsplit(".lora_", 1)
        name = name.replace("base_model.model.model.language_model.", "language_model.model.")
        lora.setdefault(name + ".weight", {})[part.split(".")[0]] = f.get_tensor(k)
print(f"add-on: {len(lora)} weights, scale {scale}")

files = sorted(glob.glob(os.path.join(BASE, "*.safetensors")))
where = {}
for p in files:
    with safe_open(p, "pt") as f:
        for k in f.keys():
            where[k] = p
AUX = (".absmax", ".quant_map", ".nested_absmax", ".nested_quant_map", ".quant_state.bitsandbytes__nf4")
names = [k for k in where if not k.endswith(AUX)]

index, buf, size, n, used = {}, {}, 0, 0, 0
def flush():
    global buf, size, n
    if buf:
        n += 1
        fn = f"model-{n:05d}.safetensors"
        save_file(buf, os.path.join(args.out, fn), metadata={"format": "pt"})
        for k in buf:
            index[k] = fn
        print("wrote", fn, f"{size / 2**30:.1f} GB", flush=True)
    buf, size = {}, 0

handles = {p: safe_open(p, "pt", device="cpu") for p in files}
for k in names:
    f = handles[where[k]]
    w = f.get_tensor(k)
    if k + ".quant_state.bitsandbytes__nf4" in where:      # a 4-bit weight: unpack it on the GPU
        qs = {s[1:]:handles[where[k + s]].get_tensor(k + s) for s in AUX if k + s in where}
        state = QuantState.from_dict(qs, device=torch.device("cuda"))
        w = bnbf.dequantize_4bit(w.cuda(), state).to(torch.bfloat16)
    if k in lora:
        a, b = lora[k]["A"].cuda().float(), lora[k]["B"].cuda().float()
        w = (w.cuda().float() + scale * (b @ a)).to(torch.bfloat16)
        used += 1
    w = w.to(torch.bfloat16).cpu().contiguous() if w.is_floating_point() else w.cpu().contiguous()
    buf[k] = w
    size += w.numel() * w.element_size()
    if size >= SHARD:
        flush()
flush()
assert used == len(lora), f"only {used} of {len(lora)} add-on weights matched"

json.dump({"metadata": {}, "weight_map": index}, open(os.path.join(args.out, "model.safetensors.index.json"), "w"))
cfg = json.load(open(os.path.join(BASE, "config.json")))
cfg.pop("quantization_config", None)
cfg["torch_dtype"] = "bfloat16"
json.dump(cfg, open(os.path.join(args.out, "config.json"), "w"), indent=2)
for name in ("generation_config.json", "added_tokens.json", "tokenizer.json", "tokenizer_config.json",
             "tokenizer.model", "special_tokens_map.json", "chat_template.json", "processor_config.json",
             "preprocessor_config.json"):
    if os.path.exists(os.path.join(BASE, name)):
        shutil.copy(os.path.join(BASE, name), args.out)
print("merged", args.out, f"({used} add-on weights)")
