from django.urls import path
from . import views

app_name = "escola"

urlpatterns = [
    path("", views.inicio_view, name="home"),
    path("portao-direcao/", views.portao_direcao, name="portao_direcao"),
    path("login/", views.login_view, name="login"),
    path("login/recuperar-senha/", views.admin_recuperar_senha, name="admin_recuperar_senha"),
    path("logout/", views.logout_view, name="logout"),
    path("painel/sms/", views.painel_sms, name="painel_sms"),
    path("painel/backup/", views.backup_download, name="backup_download"),
    path("funcionarios/", views.funcionarios_lista, name="funcionarios_lista"),
    path("funcionarios/<int:pk>/", views.funcionario_detail, name="funcionario_detail"),
    path("funcionarios/<int:pk>/historico/", views.funcionario_historico, name="funcionario_historico"),
    path("funcionarios/<int:pk>/historico/pdf/", views.funcionario_historico_pdf, name="funcionario_historico_pdf"),
    path("funcionarios/<int:pk>/mensagens/", views.funcionario_mensagens_lista, name="funcionario_mensagens_lista"),
    path("funcionarios/<int:pk>/mensagens/<int:destino_pk>/", views.funcionario_conversa, name="funcionario_conversa"),
    path("funcionarios/<int:pk>/mensagens/<int:destino_pk>/pdf/", views.funcionario_conversa_pdf, name="funcionario_conversa_pdf"),
    path("funcionarios/<int:pk>/recuperar-senha/", views.funcionario_recuperar_senha, name="funcionario_recuperar_senha"),
    path("funcionarios/<int:pk>/alterar-senha/", views.funcionario_alterar_senha, name="funcionario_alterar_senha"),
    path("funcionarios/<int:pk>/enviar-mensagem-direcao/", views.funcionario_enviar_mensagem_direcao, name="funcionario_enviar_mensagem_direcao"),
    path("funcionarios/<int:pk>/mensagens-direcao/", views.funcionario_mensagens_direcao, name="funcionario_mensagens_direcao"),
    path("painel/mensagens-anonimas/", views.contributos_gerais, name="contributos_gerais"),
    path("painel/alunos/<int:pk>/conversa/", views.aluno_conversa, name="aluno_conversa"),
    path("painel/alunos/<int:pk>/apagar-conversa/", views.aluno_conversa_apagar, name="aluno_conversa_apagar"),
    path("painel/alunos/<int:pk>/conversa/pdf/", views.aluno_conversa_pdf, name="aluno_conversa_pdf"),
    path("regulamento/", views.documentos_lista, name="documentos_lista"),
    path("vitrine/", views.vitrine, name="vitrine"),
    path("desenvolvidor/", views.desenvolvidor_view, name="desenvolvidor"),
    path("horarios/", views.horarios, name="horarios"),
    path("lazer/", views.lazer, name="lazer"),
    path("contributo/", views.contributo_view, name="contributo"),
    path("museu-da-escola/", views.museu_escola, name="museu_escola"),
]
