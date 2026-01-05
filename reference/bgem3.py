import requests

url = "https://api.siliconflow.cn/v1/embeddings"

payload = {
    "model": "BAAI/bge-large-zh-v1.5",
    "input": "Silicon flow embedding online: fast, affordable, and high-quality embedding services. come try it out!",
    "encoding_format": "float",
    "dimensions": 1024,
}
headers = {"Authorization": "Bearer <token>", "Content-Type": "application/json"}

response = requests.post(url, json=payload, headers=headers)

print(response.text)
