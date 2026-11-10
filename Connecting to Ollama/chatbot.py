from openai import OpenAI
from agents import agent, Runner, OpenAIChatCompletions





if __name__ == "__main__":
    
    client = OpenAI(base_url="http://localhost:11434/v1",api_key="ollama")
    
    MODEL = "muse-glimmer:30b-mlx"
    model = OpenAIChatCompletions(
        model=MODEL,
        openai_client=client)

    messages = []
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        messages.append({"role": "user", "content": user_input})
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=150,
            temperature=0.7,
        )
        reply = response.choices[0].message.content
        print(f"Bot: {reply}")
        messages.append({"role": "assistant", "content": reply})

        