import time


class NovidadesMiddleware:
    MAPA = {"/regulamento/": "regulamento", "/vitrine/": "vitrine", "/horarios/": "horario", "/lazer/": "lazer", "/museu-da-escola/": "museu", "/desenvolvidor/": "historia"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        chave = self.MAPA.get(request.path)
        if chave and request.method == "GET" and hasattr(request, "session"):
            request.session["visto_" + chave] = time.time()
        return self.get_response(request)
