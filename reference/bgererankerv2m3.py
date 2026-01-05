import requests

url = "https://api.siliconflow.cn/v1/rerank"

payload = {
    "model": "BAAI/bge-reranker-v2-m3",
    "query": "Apple",
    "documents": ["apple", "banana", "fruit", "vegetable"],
    "instruction": "Please rerank the documents based on the query.",
    "top_n": 4,
    "return_documents": True,
    "max_chunks_per_doc": 123,
    "overlap_tokens": 79,
}
headers = {"Authorization": "Bearer <token>", "Content-Type": "application/json"}

response = requests.post(url, json=payload, headers=headers)

print(response.text)
