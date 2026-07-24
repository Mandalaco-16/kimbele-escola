import requests
from django.conf import settings


class InfobipSMSService:
    def __init__(self):
        self.api_key = settings.INFOBIP_API_KEY
        self.base_url = settings.INFOBIP_BASE_URL
        self.sender = settings.INFOBIP_SENDER

    def enviar(self, numero, texto, token):
        url = f"{self.base_url}/sms/2/text/advanced"
        headers = {
            "Authorization": f"App {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = {
            "messages": [
                {
                    "from": self.sender,
                    "destinations": [{"to": numero}],
                    "text": texto,
                }
            ]
        }
        try:
            resposta = requests.post(url, json=payload, headers=headers, timeout=15)
            resposta.raise_for_status()
            return {"sucesso": True, "detalhe": resposta.json()}
        except Exception as exc:
            return {"sucesso": False, "detalhe": str(exc)}
