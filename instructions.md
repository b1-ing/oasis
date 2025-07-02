## Instructions

1. download the qwen 1.5b model
```angular2html
huggingface-cli download --resume-download "Qwen/Qwen2.5-1.5B-Instruct"  --local-dir "models\qwen" --local-dir-use-symlinks False --token ""

```

2. open wsl. run
```angular2html
vllm serve models/qwen --host 0.0.0.0 --port 8000 --served-model-name 'qwen-2'--enable-auto-tool-choice --tool-call-parser hermes

```

3. run the python file with this config for yaml file:
```angular2html
inference:
  model_type: qwen-2
  model_path: 'models/qwen'  # update path as needed
  stop_tokens: ["<|im_end|>", "<|endoftext|>"]
  server_url:
    - host: localhost
      ports: [8000]

```

or the following for plain python file:
```angular2html
tinyllama_model = ModelFactory.create(
            model_platform=ModelPlatformType.VLLM,
            model_type="qwen-2",
            url="http://localhost:8000/v1",
        )
```