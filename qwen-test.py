from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Set the model name
model_name = "Qwen/Qwen3-Coder-480B-A35B-Instruct"

# Load the tokenizer and model
try:
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    
    print("Loading model... (this may take a while)")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True
    )
    
    # Prepare the input
    prompt = "Write a Python function to calculate the factorial of a number."
    messages = [
        {"role": "user", "content": prompt}
    ]
    
    print("\nGenerating response...")
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    
    # Generate response
    model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
    generated_ids = model.generate(
        **model_inputs,
        max_new_tokens=1000,
        temperature=0.7,
        do_sample=True
    )
    
    # Decode and print the response
    response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    print("\nResponse:")
    print(response)
    
except Exception as e:
    print(f"An error occurred: {str(e)}")
