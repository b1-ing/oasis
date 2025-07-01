# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
import subprocess


# Path to your model folder (downloaded using huggingface-cli)
model_path = "models/tinyllama"

# A name you assign to this model
served_model_name = "tinyllama"

# Port to expose the server on
port = 8000

# Launch vLLM server locally
cmd = (
    f"python3 -m vllm.entrypoints.openai.api_server "
    f"--model {model_path} "
    f"--served-model-name {served_model_name} "
    f"--port {port} "
    f"--gpu-memory-utilization 0.82 "
    f"--disable-log-stats"
)

print(f"Running command:\n{cmd}")
subprocess.run(cmd, shell=True)

