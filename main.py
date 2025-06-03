from fastapi import FastAPI
from pydantic import BaseModel
from openai import AzureOpenAI
import os
import json
client = AzureOpenAI(
    api_key=os.getenv("OPENAI_APIKEY"),
    api_version="2024-12-01-preview",
    azure_endpoint="https://openaifashion.openai.azure.com/"
)


# FastAPI
app = FastAPI()

class AnalisiInput(BaseModel):
    tipologia: str
    marca: str
    immagini: list[str]  # immagini in base64

@app.post("/analizza-oggetto")
def analizza(input: AnalisiInput):
    messaggi = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"Devi analizzare un oggetto di tipo '{input.tipologia}' della marca '{input.marca}', "
                        "usando solo le immagini fornite. Il tuo obiettivo è stimare la probabilità che l'oggetto sia contraffatto.\n\n"
                        "⚠️ Rispondi **solo** in formato JSON valido, senza spiegazioni o testo aggiuntivo.\n\n"
                        "Il formato della risposta deve essere **esattamente questo**:\n\n"
                        "{\n"
                        "  \"percentuale\": 85,\n"
                        "  \"motivazioni\": [\n"
                        "    \"Logo leggermente distorto\",\n"
                        "    \"Cuciture non regolari\",\n"
                        "    \"Materiale non coerente con gli originali\"\n"
                        "  ]\n"
                        "}\n\n"
                        "Se non riesci a determinare nulla o le immagini sono fuori contesto, imposta:\n"
                        "\"percentuale\": \"N.D.\",\n"
                        "\"motivazioni\": [\"Immagini non sufficienti o fuori contesto\"]\n\n"
                        "Non includere nulla prima o dopo il JSON. Non inserire note. Solo JSON puro e valido."
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
            model=deployment,
            messages=messaggi
        )
        content = response.choices[0].message.content.strip()

        # Rimuove eventuali blocchi Markdown
        if content.startswith("```json"):
            content = content.removeprefix("```json").strip()
        if content.endswith("```"):
            content = content.removesuffix("```").strip()

        try:
            analisi_json = json.loads(content)

            # Se percentuale non è un numero, o troppo bassa e motivazione ambigua → segna come N.D.
            if (
                isinstance(analisi_json.get("percentuale"), (int, float)) and analisi_json["percentuale"] == 0 and
                any(k in analisi_json.get("motivazioni", [])[0].lower() for k in ["non", "sconosciuto", "indeterminato", "fuori contesto"])
            ):
                analisi_json["percentuale"] = "N.D."

            return analisi_json

        except json.JSONDecodeError:
            return {
                "percentuale": "N.D.",
                "motivazioni": ["Errore di parsing o risposta non valida"],
                "contenuto_raw": content
            }

    except Exception as e:
        return {"errore": str(e)}
