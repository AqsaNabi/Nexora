import os
import json
import requests

from dotenv import load_dotenv

load_dotenv()


class BedrockEmbeddings:

    def __init__(self):

        self.url = os.getenv("BEDROCK_EMBED_URL")
        self.api_key = os.getenv("BEDROCK_API_KEY")
        self.model = os.getenv("BEDROCK_EMBED_MODEL")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def embed_documents(self, texts):

        embeddings = []

        for text in texts:

            response = requests.post(
                f"{self.url}/model/{self.model}/invoke",
                headers=self.headers,
                json={
                    "inputText": text,
                    "dimensions": 1024,
                    "normalize": True
                },
                timeout=120
            )

            response.raise_for_status()

            embeddings.append(
                response.json()["embedding"]
            )

        return embeddings

    def embed_query(self, text):

        return self.embed_documents([text])[0]


embedding_model = BedrockEmbeddings()
embeddings = embedding_model.embed_documents(["Hello, world!", "This is a test."])
print(embeddings)