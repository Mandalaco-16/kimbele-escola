from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Exists, OuterRef
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.utils import timezone

from .forms import ContributoForm, LoginAdminForm, MensagemFuncionarioForm, MensagemInternaForm, SenhaFuncionarioForm
from .models import (
    Contributo,
    Destinatario,
    Documento,
    Funcionario,
    ImagemGaleria,
    MensagemInterna,
    Trabalhador,
    DesenvolvidorSite,
)


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
    return render(request, "escola/painel_sms.html", {})


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
        "titulo_pagina": "Vitrine",
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
    chave_sessao = f"funcionario_desbloqueado_{pk}"
    desbloqueado = request.session.get(chave_sessao, False)
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
                    request.session[chave_sessao] = True
                else:
                    messages.error(request, "Senha incorreta.")

        elif acao == "enviar_mensagem":
            form = MensagemFuncionarioForm(request.POST, request.FILES)
            senha_digitada = request.POST.get("senha_confirmada", "").strip()
            if funcionario.senha_pin and senha_digitada == funcionario.senha_pin and form.is_valid():
                Contributo.objects.create(
                    nome=form.cleaned_data["nome"],
                    mensagem=form.cleaned_data["mensagem"],
                    anexo=form.cleaned_data["anexo"],
                    funcionario=funcionario,
                )
                messages.success(request, "Obrigado! A sua sugestão foi enviada à direção da escola.")
                return redirect("escola:funcionario_detail", pk=pk)
            else:
                messages.error(request, "Não foi possível enviar. Digite a senha novamente.")

    mensagens_nao_lidas = MensagemInterna.objects.filter(destinatario=funcionario, lida=False).count()
    tem_resposta_nao_vista = Contributo.objects.filter(
        funcionario=funcionario, resposta_vista=False
    ).exclude(resposta="").exists()

    return render(request, "escola/funcionario_detail.html", {
        "f": funcionario,
        "desbloqueado": desbloqueado,
        "senha_form": senha_form,
        "form": form,
        "senha_confirmada": senha_confirmada,
        "mensagens_nao_lidas": mensagens_nao_lidas,
        "tem_resposta_nao_vista": tem_resposta_nao_vista,
    })


def _exige_desbloqueio(request, funcionario):
    chave_sessao = f"funcionario_desbloqueado_{funcionario.pk}"
    return request.session.get(chave_sessao, False)


def funcionario_mensagens_lista(request, pk):
    funcionario = get_object_or_404(Funcionario, pk=pk, ativo=True)
    if not _exige_desbloqueio(request, funcionario):
        messages.error(request, "Digite a sua senha primeiro para aceder às mensagens.")
        return redirect("escola:funcionario_detail", pk=pk)

    tem_msg_nao_lida = MensagemInterna.objects.filter(
        remetente=OuterRef("pk"), destinatario=funcionario, lida=False
    )
    colegas = Funcionario.objects.filter(ativo=True).exclude(pk=pk).annotate(
        tem_notificacao=Exists(tem_msg_nao_lida)
    )
    return render(request, "escola/funcionario_mensagens_lista.html", {
        "f": funcionario,
        "colegas": colegas,
    })


def funcionario_conversa(request, pk, destino_pk):
    funcionario = get_object_or_404(Funcionario, pk=pk, ativo=True)
    destino = get_object_or_404(Funcionario, pk=destino_pk, ativo=True)
    if not _exige_desbloqueio(request, funcionario):
        messages.error(request, "Digite a sua senha primeiro para aceder às mensagens.")
        return redirect("escola:funcionario_detail", pk=pk)

    form = MensagemInternaForm()
    if request.method == "POST":
        form = MensagemInternaForm(request.POST, request.FILES)
        if form.is_valid():
            MensagemInterna.objects.create(
                remetente=funcionario,
                destinatario=destino,
                mensagem=form.cleaned_data["mensagem"],
                anexo=form.cleaned_data["anexo"],
            )
            return redirect("escola:funcionario_conversa", pk=pk, destino_pk=destino_pk)

    MensagemInterna.objects.filter(
        remetente=destino, destinatario=funcionario, lida=False
    ).update(lida=True)

    conversa = MensagemInterna.objects.filter(
        remetente__in=[funcionario, destino], destinatario__in=[funcionario, destino]
    ).order_by("criado_em")

    return render(request, "escola/funcionario_conversa.html", {
        "f": funcionario,
        "destino": destino,
        "conversa": conversa,
        "form": form,
    })


def funcionario_conversa_pdf(request, pk, destino_pk):
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas
    import textwrap

    funcionario = get_object_or_404(Funcionario, pk=pk, ativo=True)
    destino = get_object_or_404(Funcionario, pk=destino_pk, ativo=True)
    if not _exige_desbloqueio(request, funcionario):
        messages.error(request, "Digite a sua senha primeiro para aceder às mensagens.")
        return redirect("escola:funcionario_detail", pk=pk)

    conversa = MensagemInterna.objects.filter(
        remetente__in=[funcionario, destino], destinatario__in=[funcionario, destino]
    ).order_by("criado_em")

    response = HttpResponse(content_type="application/pdf")
    nome_ficheiro = f"conversa_{funcionario.nome.replace(' ', '_')}_{destino.nome.replace(' ', '_')}.pdf"
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

    escrever_linha(f"Conversa: {funcionario.nome} <-> {destino.nome}", tamanho=14, negrito=True, espaco=22)

    if not conversa:
        escrever_linha("Ainda não há mensagens trocadas.")
    else:
        for m in conversa:
            escrever_linha(f"{m.remetente.nome} ({m.criado_em:%d/%m/%Y %H:%M}):", tamanho=10, negrito=True)
            if m.mensagem:
                for linha in textwrap.wrap(m.mensagem, width=95):
                    escrever_linha(linha)
            if m.anexo:
                escrever_linha(f"[anexo: {m.anexo.name.split('/')[-1]}]", tamanho=9)
            y -= 8

    p.showPage()
    p.save()
    return response


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
    Contributo.objects.filter(
        funcionario=funcionario, resposta_vista=False
    ).exclude(resposta="").update(resposta_vista=True)
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
