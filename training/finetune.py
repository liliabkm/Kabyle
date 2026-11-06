"""Real QLoRA training. Requires an NVIDIA GPU; never marks an unrun model trained."""
import argparse,hashlib,json,random
from pathlib import Path


def encode_example(tokenizer, row, max_length=512):
    """Only assistant target tokens contribute to the supervised loss."""
    prompt = tokenizer.apply_chat_template(row['messages'][:-1], tokenize=True, add_generation_prompt=True)
    target = tokenizer(row['messages'][-1]['content'] + tokenizer.eos_token, add_special_tokens=False)['input_ids']
    ids = prompt + target
    return {'input_ids': ids, 'attention_mask': [1] * len(ids),
            'labels': [-100] * len(prompt) + target, 'keep': len(ids) <= max_length}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--dataset',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--base-model',default='Qwen/Qwen2.5-0.5B-Instruct')
    p.add_argument('--max-steps',type=int,default=200,help='Essai court ; -1 pour une époque complète.')
    p.add_argument('--resume',action='store_true')
    p.add_argument('--evaluation-examples',type=int,default=40)
    a=p.parse_args()
    import torch
    if not torch.cuda.is_available():raise SystemExit('GPU NVIDIA requis pour ce notebook QLoRA. Active un runtime GPU dans Colab.')
    from huggingface_hub import model_info
    from transformers import AutoTokenizer,AutoModelForCausalLM,BitsAndBytesConfig,Trainer,TrainingArguments,set_seed
    from transformers.trainer_utils import get_last_checkpoint
    from peft import LoraConfig,get_peft_model,prepare_model_for_kbit_training
    from datasets import load_dataset
    from sacrebleu.metrics import CHRF
    set_seed(42)
    manifest=json.loads((a.dataset/'manifest.json').read_text())
    if manifest.get('version')!='kab-bilingual-sft-v1':raise SystemExit('Format du corpus non pris en charge.')
    for split in ('train','validation','test'):
        h=hashlib.sha256()
        with (a.dataset/(split+'.jsonl')).open('rb') as file:
            for block in iter(lambda:file.read(1024*1024),b''):h.update(block)
        if h.hexdigest()!=manifest['sha256'][split]:raise SystemExit('Empreinte incorrecte : '+split)
    data=load_dataset('json',data_files={s:str(a.dataset/(s+'.jsonl')) for s in ('train','validation','test')})
    if len(data['train'])<64 or min(len(data['validation']),len(data['test']))<8:raise SystemExit('Corpus trop petit ou séparation déséquilibrée. Exporte davantage de paires.')
    train_groups=set(data['train']['group']);validation_groups=set(data['validation']['group']);test_groups=set(data['test']['group'])
    if train_groups&validation_groups or train_groups&test_groups or validation_groups&test_groups:raise SystemExit('Fuite entre les ensembles : entraînement interrompu.')
    a.output.mkdir(parents=True,exist_ok=True)
    existing=get_last_checkpoint(str(a.output))
    if existing and not a.resume:raise SystemExit("Des checkpoints existent : utilise --resume ou un nouveau dossier.")
    checkpoint=existing if a.resume else None
    previous=a.output/'run-input.json'
    resolved=model_info(a.base_model).sha
    inputs={'base_model':a.base_model,'model_revision':resolved,'dataset_sha256':manifest['sha256'],'max_steps':a.max_steps,'seed':42,'max_length':512}
    if checkpoint and not previous.exists():raise SystemExit('Métadonnées du checkpoint absentes : utilise un nouveau dossier.')
    if checkpoint and previous.exists():
        old=json.loads(previous.read_text())
        if old['base_model']!=a.base_model or old['dataset_sha256']!=manifest['sha256'] or old['max_steps']!=a.max_steps:raise SystemExit('Le checkpoint utilise un autre modèle ou corpus.')
        resolved=old['model_revision'];inputs['model_revision']=resolved
    previous.write_text(json.dumps(inputs,indent=2)+'\n')
    tokenizer=AutoTokenizer.from_pretrained(a.base_model,revision=resolved,trust_remote_code=False)
    tokenizer.pad_token=tokenizer.eos_token;tokenizer.padding_side='right'
    def tokenize(row):return encode_example(tokenizer,row)
    tokenized=data.map(tokenize,remove_columns=data['train'].column_names).filter(lambda x:x['keep']).remove_columns('keep')
    if len(tokenized['train'])<64 or len(tokenized['validation'])<8:raise SystemExit('Trop peu d’exemples après tokenisation.')
    model=AutoModelForCausalLM.from_pretrained(a.base_model,revision=resolved,trust_remote_code=False,use_safetensors=True,
        quantization_config=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=torch.float16),device_map={'':0})
    model=prepare_model_for_kbit_training(model)
    model=get_peft_model(model,LoraConfig(r=16,lora_alpha=32,lora_dropout=.05,bias='none',task_type='CAUSAL_LM',target_modules=['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj']))
    model.config.use_cache=False
    def collate(rows):
        batch=tokenizer.pad([{'input_ids':x['input_ids'],'attention_mask':x['attention_mask']} for x in rows],return_tensors='pt')
        labels=torch.full_like(batch['input_ids'],-100)
        for i,row in enumerate(rows):labels[i,:len(row['labels'])]=torch.tensor(row['labels'])
        batch['labels']=labels
        return batch
    args=TrainingArguments(output_dir=str(a.output),per_device_train_batch_size=1,per_device_eval_batch_size=1,gradient_accumulation_steps=16,
        gradient_checkpointing=True,num_train_epochs=1,max_steps=a.max_steps,learning_rate=2e-4,fp16=True,bf16=False,
        logging_steps=10,eval_strategy='steps',eval_steps=100,save_steps=100,save_total_limit=2,report_to='none',seed=42,
        optim='paged_adamw_8bit',remove_unused_columns=False,eval_accumulation_steps=1)
    # Evaluate a bounded validation sample during training, never the test set.
    validation=tokenized['validation'].select(range(min(128,len(tokenized['validation']))))
    trainer=Trainer(model=model,args=args,train_dataset=tokenized['train'],eval_dataset=validation,data_collator=collate)
    result=trainer.train(resume_from_checkpoint=checkpoint)
    adapter=a.output/'adapter';trainer.save_model(str(adapter));tokenizer.save_pretrained(adapter)
    model.eval();model.config.use_cache=True
    rows=data['test'].shuffle(seed=42).select(range(min(a.evaluation_examples,len(data['test']))))
    records=[]
    def generate(messages):
        tokens=tokenizer.apply_chat_template(messages[:-1],tokenize=True,add_generation_prompt=True,return_tensors='pt').to(model.device)
        with torch.inference_mode():out=model.generate(tokens,attention_mask=torch.ones_like(tokens),max_new_tokens=128,do_sample=False,pad_token_id=tokenizer.pad_token_id)
        return tokenizer.decode(out[0,tokens.shape[-1]:],skip_special_tokens=True)
    for row in rows:
        with model.disable_adapter():baseline=generate(row['messages'])
        adapted=generate(row['messages'])
        records.append({'id':row['id'],'question':row['messages'][-2]['content'],'expected':row['messages'][-1]['content'],'baseline':baseline,'adapted':adapted})
    metric=CHRF()
    scores={}
    for direction in ('fr-kab','kab-fr'):
        subset=[r for r in records if r['id'].endswith(direction)]
        if subset:scores[direction]={name:metric.corpus_score([r[name] for r in subset],[[r['expected'] for r in subset]]).score for name in ('baseline','adapted')}
    (a.output/'evaluation.json').write_text(json.dumps({'scores_chrf':scores,'examples':records,'notice':'Évaluation de traduction seulement ; relecture native et tests conversationnels nécessaires.'},ensure_ascii=False,indent=2)+'\n')
    training={'status':'completed','adaptation':'lora','base_model':a.base_model,'model_revision':resolved,'dataset':manifest,
        'training_metrics':result.metrics,'global_steps':trainer.state.global_step,'training_examples_available':len(tokenized['train']),
        'max_steps':a.max_steps,'mode':'pilot' if a.max_steps>0 else 'one_epoch','scores_chrf':scores,'quality_status':'requires_human_evaluation'}
    (adapter/'training_manifest.json').write_text(json.dumps(training,ensure_ascii=False,indent=2)+'\n')
    print('Adaptateur enregistré. Compare evaluation.json et relis les réponses avant de l’utiliser sur le site.',flush=True)

if __name__=='__main__':main()
