from openai import OpenAI

# Replace this with your actual API key
client = OpenAI(api_key="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")  # Don't use "your-api-key-here"

response = client.images.generate(
    model="dall-e-3",
    prompt="a white siamese cat",
    size="1024x1024",
    quality="standard",
    n=1,
)

print(response.data[0].url)