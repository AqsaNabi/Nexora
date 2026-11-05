from langchain_openai import ChatOpenAI

 
llm = ChatOpenAI(
    model="gemma4:31b",
    base_url="https://ollama.com/v1",
    api_key="8ac3185e8cec4cdd9f4c658dde3a989f.yFVDw1yTThf0c-liSpU6fm80",
)
print(llm.invoke("Write a short story about a robot learning to love."))