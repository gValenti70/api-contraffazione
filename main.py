from fastapi import FastAPI
from pydantic import BaseModel
from openai import AzureOpenAI
import os

client = AzureOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    api_version="2024-12-01-preview",
    azure_endpoint="https://openai-eqg.openai.azure.com/"
)

app = FastAPI()

class AnalisiInput(BaseModel):
    tipologia: str
    marca: str
    immagini: list[str]

@app.post("/analizza-oggetto")
def analizza(input: AnalisiInput):
    messaggi = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"Analizza questo oggetto di tipo '{input.tipologia}' della marca '{input.marca}' "
                        "e valuta la possibilità che sia contraffatto sulla base delle immagini fornite.\n\n"
                        "Rispondi solo in formato JSON, come segue:\n"
                        "{\n"
                        "  \"percentuale\": numero intero tra 0 e 100,\n"
                        "  \"motivazioni\": [\"motivo 1\", \"motivo 2\", \"motivo 3\"]\n"
                        "}"
                    )
                }
            ]
        }
    ]

    for img in input.immagini:
        messaggi[0]["content"].append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{img}"}
        })

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messaggi
        )
        return {"analisi": response.choices[0].message.content}
    except Exception as e:
        return {"errore": str(e)}
