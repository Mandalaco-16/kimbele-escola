from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.utils import timezone

from .forms import ContributoForm, EnvioSMSForm, LoginAdminForm, MensagemFuncionarioForm, SenhaFuncionarioForm
from .models import (
    Comunicado,
    Contributo,
    Destinatario,
    Documento,
    Funcionario,
    ImagemGaleria,
    Trabalhador,
    DesenvolvidorSite,
)
from .services import InfobipSMSService


def get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("escola:painel_sms")
    if request.method == "POST":
        form = LoginAdminForm(request, data=request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())
            return redirect("escola:painel_sms")
    else:
        form = LoginAdminForm()
    return render(request, "escola/login.html", {"form": form})


def logout_view(request):
    auth_logout(request)
    return redirect("escola:login")


@login_required
def painel_sms(request):
    if request.method == "POST":
        form = EnvioSMSForm(request.POST)
        if form.is_valid():
            numeros = form.limpar_numeros()
            texto = form.cleaned_data["corpo_mensagem"]
            comunicado = Comunicado.objects.create(
                corpo_mensagem=texto,
                criado_por=request.user,
                ip_criacao=get_client_ip(request),
            )
            servico_sms = InfobipSMSService()
            enviados_com_sucesso = 0
            for numero in numeros:
                destinatario = Destinatario.objects.create(
                    comunicado=comunicado,
                    telefone=numero,
                )
                resultado = servico_sms.enviar(numero, texto, destinatario.token)
                destinatario.resposta_gateway = str(resultado["detalhe"])[:2000]
                destinatario.enviado_em = timezone.now()
                destinatario.estado_envio = (
                    Destinatario.Estado.ENVIADO
                    if resultado["sucesso"]
                    else Destinatario.Estado.FALHOU
                )
                destinatario.save()
                if resultado["sucesso"]:
                    enviados_com_sucesso += 1

            if enviados_com_sucesso == len(numeros):
                messages.success(
                    request,
                    f"SMS enviado em tempo real para {enviados_com_sucesso} trabalhador(es) com sucesso.",
                )
            elif enviados_com_sucesso > 0:
                messages.warning(
                    request,
                    f"{enviados_com_sucesso} de {len(numeros)} SMS enviados. Verifica os que falharam no histórico abaixo.",
                )
            else:
                messages.error(
                    request,
                    "Não foi possível enviar os SMS. Verifica a configuração da Infobip e a ligação à internet.",
                )
            return redirect("escola:painel_sms")
    else:
        form = EnvioSMSForm()

    return render(request, "escola/painel_sms.html", {"form": form})


def documentos_lista(request):
    documentos = Documento.objects.filter(
        categoria=Documento.Categoria.REGULAMENTO, ativo=True
    )
    contexto = {
        "titulo_pagina": "Regulamento",
        "documentos": documentos,
        "vazio_texto": "Ainda não há nenhum documento de regulamento publicado.",
    }
    return render(request, "escola/documentos_lista.html", contexto)


def vitrine(request):
    documentos = Documento.objects.filter(categoria=Documento.Categoria.VITRINE, ativo=True)
    contexto = {
        "titulo_pagina": "Vitrine / Novidades",
        "documentos": documentos,
        "vazio_texto": "Ainda não há novidades publicadas.",
    }
    return render(request, "escola/documentos_lista.html", contexto)


def horarios(request):
    imagens = ImagemGaleria.objects.filter(categoria=ImagemGaleria.Categoria.HORARIO, ativo=True)
    contexto = {
        "titulo_pagina": "Horários",
        "imagens": imagens,
        "vazio_texto": "Ainda não há fotografias de horários publicadas.",
    }
    return render(request, "escola/galeria_lista.html", contexto)


def lazer(request):
    imagens = ImagemGaleria.objects.filter(categoria=ImagemGaleria.Categoria.LAZER, ativo=True)
    contexto = {
        "titulo_pagina": "Lazer",
        "imagens": imagens,
        "vazio_texto": "Ainda não há fotografias de lazer publicadas.",
    }
    return render(request, "escola/galeria_lista.html", contexto)


def funcionarios_lista(request):
    funcionarios = Funcionario.objects.filter(ativo=True)
    return render(request, "escola/funcionarios_lista.html", {"funcionarios": funcionarios})



@never_cache
def funcionario_detail(request, pk):
    funcionario = get_object_or_404(Funcionario, pk=pk, ativo=True)
    desbloqueado = False
    senha_confirmada = ""

    senha_form = SenhaFuncionarioForm()
    form = MensagemFuncionarioForm()

    if request.method == "POST":
        acao = request.POST.get("acao")

        if acao == "desbloquear":
            senha_form = SenhaFuncionarioForm(request.POST)
            if senha_form.is_valid():
                senha_digitada = senha_form.cleaned_data["senha"].strip()
                if funcionario.senha_pin and senha_digitada == funcionario.senha_pin:
                    desbloqueado = True
                    senha_confirmada = senha_digitada
                    senha_form = SenhaFuncionarioForm()
                else:
                    messages.error(request, "Senha incorreta.")

        elif acao == "enviar_mensagem":
            form = MensagemFuncionarioForm(request.POST)
            senha_digitada = request.POST.get("senha_confirmada", "").strip()
            if funcionario.senha_pin and senha_digitada == funcionario.senha_pin and form.is_valid():
                Contributo.objects.create(
                    nome=form.cleaned_data["nome"],
                    mensagem=form.cleaned_data["mensagem"],
                    funcionario=funcionario,
                )
                messages.success(request, "Obrigado! A sua sugestão foi enviada à direção da escola.")
                return redirect("escola:funcionario_detail", pk=pk)
            else:
                messages.error(request, "Não foi possível enviar. Digite a senha novamente.")

    return render(request, "escola/funcionario_detail.html", {
        "f": funcionario,
        "desbloqueado": desbloqueado,
        "senha_form": senha_form,
        "form": form,
        "senha_confirmada": senha_confirmada,
    })


def contributo_view(request):
    if request.method == "POST":
        form = ContributoForm(request.POST)
        if form.is_valid():
            Contributo.objects.create(
                nome=form.cleaned_data["nome"],
                mensagem=form.cleaned_data["mensagem"],
            )
            messages.success(
                request,
                "Obrigado! A sua mensagem foi enviada com sucesso à direção da escola.",
            )
            return redirect("escola:contributo")
    else:
        form = ContributoForm()

    return render(request, "escola/contributo.html", {"form": form})


def ver_falta(request, token):
    destinatario = get_object_or_404(Destinatario, token=token)
    if not destinatario.acedido_em:
        destinatario.acedido_em = timezone.now()
        destinatario.ip_acesso = get_client_ip(request)
        destinatario.save(update_fields=["acedido_em", "ip_acesso"])
    return render(request, "escola/falta_detail.html", {"destinatario": destinatario})


def desenvolvidor_view(request):
    dev = DesenvolvidorSite.objects.first()
    contexto = {"dev": dev}
    return render(request, "escola/desenvolvidor.html", contexto)


def inicio_view(request):
    return render(request, "escola/inicio.html", {})


def funcionario_historico(request, pk):
    funcionario = get_object_or_404(Funcionario, pk=pk, ativo=True)
    contributos = Contributo.objects.filter(funcionario=funcionario).order_by("criado_em")
    return render(
        request,
        "escola/funcionario_historico.html",
        {"f": funcionario, "contributos": contributos},
    )


def funcionario_historico_pdf(request, pk):
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas
    import textwrap

    funcionario = get_object_or_404(Funcionario, pk=pk, ativo=True)
    contributos = Contributo.objects.filter(funcionario=funcionario).order_by("criado_em")

    response = HttpResponse(content_type="application/pdf")
    nome_ficheiro = f"historico_{funcionario.nome.replace(' ', '_')}.pdf"
    response["Content-Disposition"] = f'attachment; filename="{nome_ficheiro}"'

    largura, altura = A4
    margem = 2 * cm
    y = altura - margem
    p = canvas.Canvas(response, pagesize=A4)

    def nova_pagina():
        nonlocal y
        p.showPage()
        y = altura - margem

    def escrever_linha(texto, tamanho=11, negrito=False, espaco=14):
        nonlocal y
        if y < margem:
            nova_pagina()
        p.setFont("Helvetica-Bold" if negrito else "Helvetica", tamanho)
        p.drawString(margem, y, texto)
        y -= espaco

    escrever_linha(f"Histórico da Conversa - {funcionario.nome}", tamanho=14, negrito=True, espaco=22)
    escrever_linha(f"Cargo: {funcionario.cargo}", tamanho=10, espaco=20)

    if not contributos:
        escrever_linha("Ainda não há mensagens trocadas.")
    else:
        for c in contributos:
            escrever_linha(f"Enviado em {c.criado_em:%d/%m/%Y %H:%M}", tamanho=10, negrito=True)
            for linha in textwrap.wrap(c.mensagem, width=95):
                escrever_linha(linha)
            if c.resposta:
                escrever_linha(f"Resposta da Direção ({c.respondido_em:%d/%m/%Y %H:%M}):", tamanho=10, negrito=True)
                for linha in textwrap.wrap(c.resposta, width=95):
                    escrever_linha(linha)
            else:
                escrever_linha("(Ainda sem resposta da Direção)")
            y -= 8

    p.showPage()
    p.save()
    return response
