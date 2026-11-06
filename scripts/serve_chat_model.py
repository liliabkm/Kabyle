"""Optional local inference worker. Heavy ML dependencies are isolated from the site."""
import argparse
import json
from pathlib import Path
import threading


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--adapter', default='artifacts/chat-model/adapter')
    parser.add_argument('--base-only', action='store_true')
    parser.add_argument('--base-model', default='Qwen/Qwen2.5-0.5B-Instruct')
    parser.add_argument('--device', choices=['cpu', 'cuda'], default='cpu')
    args = parser.parse_args()
    import torch
    import uvicorn
    from fastapi import FastAPI, HTTPException
    from transformers import AutoTokenizer, AutoModelForCausalLM
    from peft import PeftModel
    metadata = {}
    if not args.base_only:
        folder = Path(args.adapter)
        metadata = json.loads((folder / 'training_manifest.json').read_text())
        if metadata.get('status') != 'completed':
            raise SystemExit('Adaptateur incomplet : terminer le notebook Colab.')
        args.base_model = metadata['base_model']
    revision = metadata.get('model_revision', 'main')
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, revision=revision, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(args.base_model, revision=revision,
        trust_remote_code=False, use_safetensors=True, low_cpu_mem_usage=True,
        torch_dtype=torch.float16 if args.device == 'cuda' else torch.float32)
    if not args.base_only:
        model = PeftModel.from_pretrained(model, args.adapter, is_trainable=False)
    model.to(args.device).eval()
    lock = threading.Lock()
    app = FastAPI()

    @app.get('/v1/health')
    def health():
        return {'model': args.base_model, 'adaptation': 'base' if args.base_only else 'lora_loaded'}

    @app.post('/v1/chat/completions')
    def complete(body: dict):
        messages = body.get('messages', [])
        if not isinstance(messages, list) or not 1 <= len(messages) <= 12:
            raise HTTPException(422, 'Messages invalides')
        for message in messages:
            if not isinstance(message, dict) or message.get('role') not in ['system', 'user', 'assistant'] or not isinstance(message.get('content'), str) or len(message['content']) > 16000:
                raise HTTPException(422, 'Message invalide')
        limit = body.get('max_tokens', 256)
        if type(limit) is not int or not 1 <= limit <= 256:
            raise HTTPException(422, 'Limite invalide')
        if not lock.acquire(blocking=False):
            raise HTTPException(429, 'Le modèle traite déjà une demande')
        try:
            inputs = tokenizer.apply_chat_template(messages, add_generation_prompt=True, return_tensors='pt').to(args.device)
            if inputs.shape[1] > 4096:
                raise HTTPException(422, 'Conversation trop longue')
            with torch.inference_mode():
                output = model.generate(inputs, attention_mask=torch.ones_like(inputs), max_new_tokens=limit,
                    do_sample=False, pad_token_id=tokenizer.eos_token_id)
            text = tokenizer.decode(output[0, inputs.shape[1]:], skip_special_tokens=True)
            return {'choices': [{'message': {'role': 'assistant', 'content': text}}]}
        finally:
            lock.release()
    uvicorn.run(app, host='127.0.0.1', port=8010)

if __name__ == '__main__':
    main()
