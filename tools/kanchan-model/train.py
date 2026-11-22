#!/usr/bin/env python3
"""Trains the Kan-chan add-on (a LoRA adapter for Gemma 3 12B) from output/kanchan-model/train.jsonl.

Runs in the build PC's WSL training environment (/root/kc-train, Unsloth + PyTorch with CUDA) on the
RTX 4080 in about an hour:
  . /root/kc-train/bin/activate && python tools/kanchan-model/train.py [--epochs 2]

Only her replies are learned from (the person's messages and the system prompt are context).
Settings are deliberately gentle (low rank, low learning rate, two passes): the add-on should
strengthen habits her personality prompt already asks for, not replace her.
Writes output/kanchan-model/adapter/ (PEFT safetensors) and a training log.
"""
import argparse
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "output", "kanchan-model")
BASE = "unsloth/gemma-3-12b-it-unsloth-bnb-4bit"     # Gemma 3 12B instruct (Gemma terms), 4-bit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=float, default=2)
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--max-len", type=int, default=4096)
    args = ap.parse_args()

    from unsloth import FastModel
    from unsloth.chat_templates import get_chat_template, train_on_responses_only
    from datasets import Dataset
    from trl import SFTConfig, SFTTrainer

    model, tok = FastModel.from_pretrained(BASE, max_seq_length=args.max_len, load_in_4bit=True,
                                           full_finetuning=False)
    model = FastModel.get_peft_model(model, finetune_vision_layers=False, finetune_language_layers=True,
                                     finetune_attention_modules=True, finetune_mlp_modules=True,
                                     r=args.rank, lora_alpha=args.rank, lora_dropout=0.05, bias="none",
                                     random_state=7)
    tok = get_chat_template(tok, chat_template="gemma-3")

    rows = [json.loads(l) for l in open(os.path.join(OUT, "train.jsonl"), encoding="utf-8")]
    texts = [tok.apply_chat_template(r["messages"], tokenize=False, add_generation_prompt=False)
             .removeprefix("<bos>") for r in rows]
    text_tok = getattr(tok, "tokenizer", tok)      # Gemma 3 gives a processor; count with its tokenizer
    lengths = [len(text_tok(t, add_special_tokens=False)["input_ids"]) for t in texts]
    print(f"{len(texts)} conversations, tokens: max {max(lengths)}, mean {sum(lengths) // len(lengths)}")
    ds = Dataset.from_dict({"text": texts})

    trainer = SFTTrainer(model=model, tokenizer=tok, train_dataset=ds, args=SFTConfig(
        dataset_text_field="text", per_device_train_batch_size=1, gradient_accumulation_steps=8,
        num_train_epochs=args.epochs, learning_rate=args.lr, warmup_steps=5, lr_scheduler_type="cosine",
        logging_steps=5, optim="adamw_8bit", weight_decay=0.01, seed=7, report_to="none",
        output_dir=os.path.join(OUT, "checkpoints"), save_strategy="no", max_length=args.max_len))
    trainer = train_on_responses_only(trainer, instruction_part="<start_of_turn>user\n",
                                      response_part="<start_of_turn>model\n")
    stats = trainer.train()
    model.save_pretrained(os.path.join(OUT, "adapter"))
    tok.save_pretrained(os.path.join(OUT, "adapter"))
    with open(os.path.join(OUT, "train-log.json"), "w") as f:
        json.dump({"args": vars(args), "examples": len(texts), "metrics": stats.metrics,
                   "log": trainer.state.log_history}, f, indent=1)
    print("saved", os.path.join(OUT, "adapter"), stats.metrics)


if __name__ == "__main__":
    main()
