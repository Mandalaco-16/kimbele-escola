from django.urls import path
from . import views

app_name = "escola"

urlpatterns = [
    path("", views.inicio_view, name="home"),
    path("portao-direcao/", views.portao_direcao, name="portao_direcao"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("painel/sms/", views.painel_sms, name="painel_sms"),
    path("funcionarios/", views.funcionarios_lista, name="funcionarios_lista"),
    path("funcionarios/<int:pk>/", views.funcionario_detail, name="funcionario_detail"),
    path("funcionarios/<int:pk>/historico/", views.funcionario_historico, name="funcionario_historico"),
    path("funcionarios/<int:pk>/historico/pdf/", views.funcionario_historico_pdf, name="funcionario_historico_pdf"),
    path("funcionarios/<int:pk>/mensagens/", views.funcionario_mensagens_lista, name="funcionario_mensagens_lista"),
    path("funcionarios/<int:pk>/mensagens/<int:destino_pk>/", views.funcionario_conversa, name="funcionario_conversa"),
    path("funcionarios/<int:pk>/mensagens/<int:destino_pk>/pdf/", views.funcionario_conversa_pdf, name="funcionario_conversa_pdf"),
    path("regulamento/", views.documentos_lista, name="documentos_lista"),
    path("vitrine/", views.vitrine, name="vitrine"),
    path("desenvolvidor/", views.desenvolvidor_view, name="desenvolvidor"),
    path("horarios/", views.horarios, name="horarios"),
    path("lazer/", views.lazer, name="lazer"),
    path("contributo/", views.contributo_view, name="contributo"),
    path("museu-da-escola/", views.museu_escola, name="museu_escola"),
    path("falta/<uuid:token>/", views.ver_falta, name="ver_falta"),
]
