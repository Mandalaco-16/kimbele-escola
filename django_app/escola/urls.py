from django.urls import path
from . import views

app_name = "escola"

urlpatterns = [
    path("", views.funcionarios_lista, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("painel/sms/", views.painel_sms, name="painel_sms"),
    path("funcionarios/", views.funcionarios_lista, name="funcionarios_lista"),
    path("funcionarios/<int:pk>/", views.funcionario_detail, name="funcionario_detail"),
    path("regulamento/", views.documentos_lista, name="documentos_lista"),
    path("vitrine/", views.vitrine, name="vitrine"),
    path("desenvolvidor/", views.desenvolvidor_view, name="desenvolvidor"),
    path("horarios/", views.horarios, name="horarios"),
    path("lazer/", views.lazer, name="lazer"),
    path("contributo/", views.contributo_view, name="contributo"),
    path("falta/<uuid:token>/", views.ver_falta, name="ver_falta"),
]
