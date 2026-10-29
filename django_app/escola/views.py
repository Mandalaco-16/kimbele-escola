import random
import string
from urllib.parse import quote
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Exists, OuterRef
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.utils import timezone

from .forms import ContributoForm, LoginAdminForm, MensagemFuncionarioForm, MensagemInternaForm, PortaoDirecaoForm, SenhaFuncionarioForm, RecuperarSenhaForm, AlterarSenhaForm, MensagemDirecaoForm, MensagemAlunoForm, RecuperarSenhaAdminForm
from .models import (
    MensagemDirecao,
    Aluno,
    MensagemDirecaoAluno,
    Contributo,
    Documento,
    Funcionario,
    ImagemGaleria,
    MensagemInterna,
    DesenvolvidorSite,
)


def get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


@never_cache
def portao_direcao(request):
    etapa = request.GET.get("etapa", "1")
    form = None
    if etapa == "2":
        if request.method == "POST":
            form = PortaoDirecaoForm(request.POST)
            if form.is_valid():
                return redirect("escola:login")
        else:
            form = PortaoDirecaoForm()
    contexto = {"etapa": etapa, "form": form}
    return render(request, "escola/portao_direcao.html", contexto)


@never_cache
def login_view(request):
    if request.user.is_authenticated:
        auth_logout(request)
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
@never_cache
def painel_sms(request):
    tem_contributo_nao_lido = Contributo.objects.filter(
        funcionario=OuterRef("pk"), lido=False
    )
    funcionarios = Funcionario.objects.filter(ativo=True).annotate(
        tem_contributo_nao_lido=Exists(tem_contributo_nao_lido)
    )
    return render(request, "escola/painel_sms.html", {
        "funcionarios": funcionarios,
    })


def museu_escola(request):
    imagens = ImagemGaleria.objects.filter(categoria=ImagemGaleria.Categoria.MUSEU, ativo=True)
    documentos = Documento.objects.filter(categoria=Documento.Categoria.MUSEU, ativo=True)
    contexto = {
        "imagens": imagens,
        "documentos": documentos,
    }
    return render(request, "escola/museu_escola.html", contexto)


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

    import time
    if request.GET.get("sair"):
        request.session.pop(chave_sessao, None)
        request.session.pop(chave_sessao + "_ts", None)
        desbloqueado = False
    elif desbloqueado and time.time() - request.session.get(chave_sessao + "_ts", 0) > 1800:
        request.session.pop(chave_sessao, None)
        desbloqueado = False

    senha_form = SenhaFuncionarioForm()
    form = MensagemFuncionarioForm()

    if request.method == "POST":
        acao = request.POST.get("acao")

        if acao == "desbloquear":
            senha_form = SenhaFuncionarioForm(request.POST)
            if senha_form.is_valid():
                senha_digitada = senha_form.cleaned_data["senha"].strip()
                if funcionario.verificar_senha(senha_digitada):
                    desbloqueado = True
                    senha_confirmada = senha_digitada
                    senha_form = SenhaFuncionarioForm()
                    request.session[chave_sessao] = True
                    request.session[chave_sessao + "_ts"] = time.time()
                else:
                    messages.error(request, "Senha incorreta.")

        elif acao == "enviar_mensagem":
            form = MensagemFuncionarioForm(request.POST, request.FILES)
            senha_digitada = request.POST.get("senha_confirmada", "").strip()
            if desbloqueado and form.is_valid():
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
    tem_mensagem_direcao_nao_lida = MensagemDirecao.objects.filter(
        funcionario=funcionario, lida=False
    ).exists()

    return render(request, "escola/funcionario_detail.html", {
        "f": funcionario,
        "desbloqueado": desbloqueado,
        "senha_form": senha_form,
        "form": form,
        "senha_confirmada": senha_confirmada,
        "mensagens_nao_lidas": mensagens_nao_lidas,
        "encarregado_nao_lidas": MensagemEncarregado.objects.filter(professor=funcionario, do_professor=False, lida=False).exists(),
        "tem_resposta_nao_vista": tem_resposta_nao_vista,
        "tem_mensagem_direcao_nao_lida": tem_mensagem_direcao_nao_lida,
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
    aluno = None
    erro_matricula = False
    form = MensagemAlunoForm()
    if request.method == "GET":
        if request.GET.get("sair"):
            request.session.pop("aluno_publico_id", None)  # aluno_publico_sair
        else:
            aluno = _aluno_publico(request)

    if request.method == "POST":
        acao = request.POST.get("acao")

        if acao == "pesquisar":
            matricula = request.POST.get("matricula", "").strip()
            nasc = request.POST.get("nascimento", "").strip()
            from django.core.cache import cache
            chave = f"tentativas_{matricula}"
            if cache.get(chave, 0) >= 5:
                messages.error(request, "Demasiadas tentativas. Aguarde 15 minutos e tente de novo.")
            else:
                alvo = Aluno.objects.filter(matricula=matricula, ativo=True).first()
                if alvo and alvo.nascimento and "".join(c for c in nasc if c.isdigit()) in (alvo.nascimento.strftime("%d%m%Y"), alvo.nascimento.strftime("%Y%m%d")):
                    aluno = alvo
                    cache.delete(chave)
                    request.session["aluno_publico_id"] = alvo.pk
                else:
                    cache.set(chave, cache.get(chave, 0) + 1, 900)
                    erro_matricula = True

        elif acao == "baixar_pdf":
            aluno_id = request.POST.get("aluno_id")
            aluno = get_object_or_404(Aluno, pk=aluno_id, ativo=True)
            if request.session.get("aluno_publico_id") != aluno.pk:
                return redirect("/contributo/")
            conversa_pdf = []
            for c in Contributo.objects.filter(aluno=aluno):
                conversa_pdf.append({"tipo": "aluno", "texto": c.mensagem, "anexo": c.anexo, "quando": c.criado_em})
                if c.resposta or c.resposta_anexo:
                    conversa_pdf.append({"tipo": "direcao", "texto": c.resposta, "anexo": c.resposta_anexo, "quando": c.respondido_em or c.criado_em})
            for m in MensagemDirecaoAluno.objects.filter(aluno=aluno):
                conversa_pdf.append({"tipo": "direcao", "texto": m.mensagem, "anexo": m.anexo, "quando": m.criado_em})
            conversa_pdf.sort(key=lambda e: e["quando"])
            nome_ficheiro = f"conversa_{aluno.nome.replace(' ', '_')}.pdf"
            return _gerar_pdf_conversa(
                f"Conversa sobre {aluno.nome}", "Fala com a Direção da Escola", conversa_pdf, nome_ficheiro
            )

        elif acao == "enviar":
            aluno_id = request.POST.get("aluno_id")
            aluno = get_object_or_404(Aluno, pk=aluno_id, ativo=True)
            if request.session.get("aluno_publico_id") != aluno.pk:
                return redirect("/contributo/")
            form = MensagemAlunoForm(request.POST, request.FILES)
            if form.is_valid():
                Contributo.objects.create(
                    aluno=aluno,
                    mensagem=form.cleaned_data["mensagem"],
                    anexo=form.cleaned_data["anexo"],
                )
                messages.success(
                    request,
                    "Obrigado! A sua mensagem foi enviada com sucesso à direção da escola.",
                )
                form = MensagemAlunoForm()

    conversa = []
    if aluno:
        for c in Contributo.objects.filter(aluno=aluno):
            conversa.append({
                "tipo": "aluno",
                "texto": c.mensagem,
                "anexo": c.anexo,
                "quando": c.criado_em,
            })
            if c.resposta or c.resposta_anexo:
                conversa.append({
                    "tipo": "direcao",
                    "texto": c.resposta,
                    "anexo": c.resposta_anexo,
                    "quando": c.respondido_em or c.criado_em,
                })
        for m in MensagemDirecaoAluno.objects.filter(aluno=aluno):
            conversa.append({
                "tipo": "direcao",
                "texto": m.mensagem,
                "anexo": m.anexo,
                "quando": m.criado_em,
            })
        conversa.sort(key=lambda e: e["quando"])

    return render(request, "escola/contributo.html", {
        "aluno": aluno,
        "erro_matricula": erro_matricula,
        "form": form,
        "conversa": conversa,
    })


def desenvolvidor_view(request):
    dev = DesenvolvidorSite.objects.first()
    contexto = {"dev": dev}
    return render(request, "escola/desenvolvidor.html", contexto)


def inicio_view(request):
    return render(request, "escola/inicio.html", {})


def funcionario_historico(request, pk):
    funcionario = get_object_or_404(Funcionario, pk=pk, ativo=True)
    if not _exige_desbloqueio(request, funcionario):
        messages.error(request, "Digite a sua senha primeiro para aceder à conversa.")
        return redirect("escola:funcionario_detail", pk=pk)

    if request.method == "POST":
        form = MensagemFuncionarioForm(request.POST, request.FILES)
        if form.is_valid():
            Contributo.objects.create(
                nome=form.cleaned_data["nome"],
                mensagem=form.cleaned_data["mensagem"],
                anexo=form.cleaned_data["anexo"],
                funcionario=funcionario,
            )
            messages.success(request, "Mensagem enviada à direção da escola.")
            return redirect("escola:funcionario_historico", pk=pk)
    else:
        form = MensagemFuncionarioForm()

    Contributo.objects.filter(
        funcionario=funcionario, resposta_vista=False
    ).exclude(resposta="").update(resposta_vista=True)
    MensagemDirecao.objects.filter(funcionario=funcionario, lida=False).update(lida=True)

    conversa = []
    for c in Contributo.objects.filter(funcionario=funcionario):
        conversa.append({
            "tipo": "funcionario",
            "texto": c.mensagem,
            "anexo": c.anexo,
            "quando": c.criado_em,
        })
        if c.resposta or c.resposta_anexo:
            conversa.append({
                "tipo": "direcao",
                "texto": c.resposta,
                "anexo": c.resposta_anexo,
                "quando": c.respondido_em or c.criado_em,
            })
    for m in MensagemDirecao.objects.filter(funcionario=funcionario):
        conversa.append({
            "tipo": "direcao",
            "texto": m.mensagem,
            "anexo": m.anexo,
            "quando": m.criado_em,
        })
    conversa.sort(key=lambda e: e["quando"])

    return render(
        request,
        "escola/funcionario_historico.html",
        {"f": funcionario, "conversa": conversa, "form": form},
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


def funcionario_recuperar_senha(request, pk):
    funcionario = get_object_or_404(Funcionario, pk=pk, ativo=True)
    link_whatsapp = None
    senha_nova = None

    if request.method == "POST":
        form = RecuperarSenhaForm(request.POST)
        if form.is_valid():
            telefone_digitado = "".join(c for c in form.cleaned_data["telefone"] if c.isdigit())
            telefone_cadastrado = "".join(c for c in (funcionario.telefone or "") if c.isdigit())
            whatsapp_cadastrado = "".join(c for c in (funcionario.whatsapp or "") if c.isdigit())

            if telefone_digitado and (
                telefone_digitado == telefone_cadastrado
                or telefone_digitado == whatsapp_cadastrado
            ):
                senha_nova = "".join(random.choices(string.digits, k=6))
                funcionario.definir_senha(senha_nova)

                numero_envio = whatsapp_cadastrado or telefone_cadastrado
                texto = (
                    f"Ola {funcionario.nome}, a sua nova senha de acesso e: {senha_nova}"
                )
                link_whatsapp = f"https://wa.me/{numero_envio}?text={quote(texto)}"
            else:
                messages.error(request, "O número de telefone não confere com o cadastrado.")
    else:
        form = RecuperarSenhaForm()

    return render(request, "escola/funcionario_recuperar_senha.html", {
        "funcionario": funcionario,
        "form": form,
        "link_whatsapp": link_whatsapp,
        "senha_nova": senha_nova,
    })


def funcionario_alterar_senha(request, pk):
    funcionario = get_object_or_404(Funcionario, pk=pk, ativo=True)
    chave_sessao = f"funcionario_desbloqueado_{pk}"
    desbloqueado = request.session.get(chave_sessao, False)

    if not desbloqueado:
        messages.error(request, "Digite a sua senha primeiro para aceder a esta área.")
        return redirect("escola:funcionario_detail", pk=pk)

    if request.method == "POST":
        form = AlterarSenhaForm(request.POST)
        if form.is_valid():
            senha_atual = form.cleaned_data["senha_atual"].strip()
            nova_senha = form.cleaned_data["nova_senha"].strip()
            if funcionario.verificar_senha(senha_atual):
                funcionario.definir_senha(nova_senha)
                messages.success(request, "Senha alterada com sucesso!")
                return redirect("escola:funcionario_detail", pk=pk)
            else:
                messages.error(request, "A senha atual está incorreta.")
    else:
        form = AlterarSenhaForm()

    return render(request, "escola/funcionario_alterar_senha.html", {
        "funcionario": funcionario,
        "form": form,
    })


@login_required
@never_cache
def funcionario_enviar_mensagem_direcao(request, pk):
    funcionario = get_object_or_404(Funcionario, pk=pk, ativo=True)

    if request.method == "POST":
        form = MensagemDirecaoForm(request.POST, request.FILES)
        if form.is_valid():
            MensagemDirecao.objects.create(
                funcionario=funcionario,
                mensagem=form.cleaned_data["mensagem"],
                anexo=form.cleaned_data["anexo"],
            )
            messages.success(request, f"Mensagem enviada para {funcionario.nome} com sucesso!")
            return redirect("escola:funcionario_enviar_mensagem_direcao", pk=pk)
    else:
        form = MensagemDirecaoForm()

    Contributo.objects.filter(funcionario=funcionario, lido=False).update(lido=True)

    conversa = []
    for c in Contributo.objects.filter(funcionario=funcionario):
        conversa.append({
            "tipo": "funcionario",
            "texto": c.mensagem,
            "anexo": c.anexo,
            "quando": c.criado_em,
        })
        if c.resposta or c.resposta_anexo:
            conversa.append({
                "tipo": "direcao",
                "texto": c.resposta,
                "anexo": c.resposta_anexo,
                "quando": c.respondido_em or c.criado_em,
            })
    for m in MensagemDirecao.objects.filter(funcionario=funcionario):
        conversa.append({
            "tipo": "direcao",
            "texto": m.mensagem,
            "anexo": m.anexo,
            "quando": m.criado_em,
        })
    conversa.sort(key=lambda e: e["quando"])

    return render(request, "escola/funcionario_enviar_mensagem_direcao.html", {
        "funcionario": funcionario,
        "form": form,
        "conversa": conversa,
    })


def funcionario_mensagens_direcao(request, pk):
    funcionario = get_object_or_404(Funcionario, pk=pk, ativo=True)
    if not _exige_desbloqueio(request, funcionario):
        messages.error(request, "Digite a sua senha primeiro para aceder às mensagens.")
        return redirect("escola:funcionario_detail", pk=pk)

    MensagemDirecao.objects.filter(funcionario=funcionario, lida=False).update(lida=True)

    conversa = []
    for c in Contributo.objects.filter(funcionario=funcionario):
        conversa.append({
            "tipo": "funcionario",
            "texto": c.mensagem,
            "anexo": c.anexo,
            "quando": c.criado_em,
        })
        if c.resposta or c.resposta_anexo:
            conversa.append({
                "tipo": "direcao",
                "texto": c.resposta,
                "anexo": c.resposta_anexo,
                "quando": c.respondido_em or c.criado_em,
            })
    for m in MensagemDirecao.objects.filter(funcionario=funcionario):
        conversa.append({
            "tipo": "direcao",
            "texto": m.mensagem,
            "anexo": m.anexo,
            "quando": m.criado_em,
        })
    conversa.sort(key=lambda e: e["quando"])

    return render(request, "escola/funcionario_mensagens_direcao.html", {
        "funcionario": funcionario,
        "conversa": conversa,
    })


@login_required
@never_cache
def contributos_gerais(request):
    nao_lido = Contributo.objects.filter(aluno=OuterRef("pk"), lido=False)
    alunos = Aluno.objects.filter(ativo=True).annotate(
        tem_notificacao=Exists(nao_lido)
    ).order_by("nome")
    return render(request, "escola/contributos_gerais.html", {"alunos": alunos})


@login_required
@never_cache
def aluno_conversa(request, pk):
    aluno = get_object_or_404(Aluno, pk=pk)

    if request.method == "POST":
        form = MensagemDirecaoForm(request.POST, request.FILES)
        if form.is_valid():
            MensagemDirecaoAluno.objects.create(
                aluno=aluno,
                mensagem=form.cleaned_data["mensagem"],
                anexo=form.cleaned_data["anexo"],
            )
            messages.success(request, f"Resposta enviada para {aluno.nome}.")
            return redirect("escola:aluno_conversa", pk=pk)
    else:
        form = MensagemDirecaoForm()

    Contributo.objects.filter(aluno=aluno, lido=False).update(lido=True)

    conversa = []
    for c in Contributo.objects.filter(aluno=aluno):
        conversa.append({
            "tipo": "aluno",
            "texto": c.mensagem,
            "anexo": c.anexo,
            "quando": c.criado_em,
        })
        if c.resposta or c.resposta_anexo:
            conversa.append({
                "tipo": "direcao",
                "texto": c.resposta,
                "anexo": c.resposta_anexo,
                "quando": c.respondido_em or c.criado_em,
            })
    for m in MensagemDirecaoAluno.objects.filter(aluno=aluno):
        conversa.append({
            "tipo": "direcao",
            "texto": m.mensagem,
            "anexo": m.anexo,
            "quando": m.criado_em,
        })
    conversa.sort(key=lambda e: e["quando"])

    return render(request, "escola/aluno_conversa.html", {
        "aluno": aluno,
        "form": form,
        "conversa": conversa,
    })


@login_required
@never_cache
def backup_download(request):
    from django.core import management
    from django.http import HttpResponse
    from django.utils import timezone
    import io

    buffer = io.StringIO()
    management.call_command(
        "dumpdata",
        "escola",
        indent=2,
        stdout=buffer,
    )
    conteudo = buffer.getvalue()

    data = timezone.now().strftime("%Y%m%d_%H%M")
    nome_ficheiro = f"backup_kimbele_escola_{data}.json"

    response = HttpResponse(conteudo, content_type="application/json")
    response["Content-Disposition"] = f'attachment; filename="{nome_ficheiro}"'
    return response


@login_required
@never_cache
def aluno_conversa_apagar(request, pk):
    aluno = get_object_or_404(Aluno, pk=pk)
    if request.method == "POST":
        Contributo.objects.filter(aluno=aluno).delete()
        MensagemDirecaoAluno.objects.filter(aluno=aluno).delete()
        messages.success(request, f"Conversa de {aluno.nome} apagada com sucesso.")
    return redirect("escola:contributos_gerais")


def _gerar_pdf_conversa(titulo, subtitulo, conversa, nome_ficheiro, rotulo_resposta="Resposta da Direção"):
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas
    import textwrap

    response = HttpResponse(content_type="application/pdf")
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

    escrever_linha(titulo, tamanho=14, negrito=True, espaco=22)
    escrever_linha(subtitulo, tamanho=10, espaco=20)

    if not conversa:
        escrever_linha("Ainda não há mensagens trocadas.")
    else:
        for m in conversa:
            quem = "Enviado" if m["tipo"] == "aluno" else rotulo_resposta
            escrever_linha(f"{quem} - {m['quando']:%d/%m/%Y %H:%M}", tamanho=10, negrito=True)
            if m["texto"]:
                for linha in textwrap.wrap(m["texto"], width=95):
                    escrever_linha(linha)
            if m["anexo"]:
                escrever_linha("(Tem anexo - ver no site)")
            y -= 8

    p.showPage()
    p.save()
    return response


@login_required
@never_cache
def aluno_conversa_pdf(request, pk):
    aluno = get_object_or_404(Aluno, pk=pk)

    conversa = []
    for c in Contributo.objects.filter(aluno=aluno):
        conversa.append({"tipo": "aluno", "texto": c.mensagem, "anexo": c.anexo, "quando": c.criado_em})
        if c.resposta or c.resposta_anexo:
            conversa.append({"tipo": "direcao", "texto": c.resposta, "anexo": c.resposta_anexo, "quando": c.respondido_em or c.criado_em})
    for m in MensagemDirecaoAluno.objects.filter(aluno=aluno):
        conversa.append({"tipo": "direcao", "texto": m.mensagem, "anexo": m.anexo, "quando": m.criado_em})
    conversa.sort(key=lambda e: e["quando"])

    nome_ficheiro = f"conversa_{aluno.nome.replace(' ', '_')}.pdf"
    return _gerar_pdf_conversa(
        f"Conversa sobre {aluno.nome}", "Fala com a Direção da Escola", conversa, nome_ficheiro
    )


def admin_recuperar_senha(request):
    from django.contrib.auth.models import User
    from urllib.parse import quote
    import random, string

    opcao = request.GET.get("opcao") or request.POST.get("opcao")
    link_whatsapp = None
    erro_username = False
    erro_telefone = False
    telefone_confirmado = False
    form = None
    NUMERO_DIRECAO = "927889999"

    if opcao in ("1", "2", "3") and request.method == "POST":
        telefone = "".join(ch for ch in request.POST.get("telefone", "") if ch.isdigit())
        if telefone.endswith(NUMERO_DIRECAO) or telefone == NUMERO_DIRECAO:
            telefone_confirmado = True
        else:
            erro_telefone = True

    if opcao == "1" and telefone_confirmado:
        from .models import ConfiguracaoAcesso
        config, _ = ConfiguracaoAcesso.objects.get_or_create(pk=1)
        senha_nova = "".join(random.choices(string.digits, k=8))
        config.senha_portao = senha_nova
        config.save()
        texto = f"Nova senha do Acesso Reservado a Direcao: {senha_nova}"
        link_whatsapp = f"https://wa.me/244927889999?text={quote(texto)}"

    elif opcao == "2" and telefone_confirmado:
        user = User.objects.filter(is_staff=True).order_by("id").first()
        if user:
            texto = f"O seu nome de utilizador do admin e: {user.username}"
            link_whatsapp = f"https://wa.me/244927889999?text={quote(texto)}"

    elif opcao == "3":
        form = RecuperarSenhaAdminForm(request.POST or None)
        if telefone_confirmado and request.method == "POST" and form.is_valid():
            username = form.cleaned_data["username"].strip()
            try:
                user = User.objects.get(username=username, is_staff=True)
                senha_nova = "".join(random.choices(string.digits, k=8))
                user.set_password(senha_nova)
                user.save()
                texto = f"Ola {user.username}, a sua nova senha de acesso ao admin e: {senha_nova}"
                link_whatsapp = f"https://wa.me/244927889999?text={quote(texto)}"
            except User.DoesNotExist:
                erro_username = True

    return render(request, "escola/admin_recuperar_senha.html", {
        "opcao": opcao,
        "form": form,
        "link_whatsapp": link_whatsapp,
        "erro_username": erro_username,
        "erro_telefone": erro_telefone,
        "telefone_confirmado": telefone_confirmado,
    })


@login_required
@never_cache
def admin_alterar_senha(request):
    from django.contrib.auth.forms import PasswordChangeForm
    from django.contrib.auth import update_session_auth_hash
    from .models import ConfiguracaoAcesso

    config, _ = ConfiguracaoAcesso.objects.get_or_create(pk=1)

    if request.method == "POST":
        form_senha = PasswordChangeForm(request.user, request.POST)
        nova_senha_portao = request.POST.get("nova_senha_portao", "").strip()
        alterou_algo = False

        if form_senha.is_valid():
            user = form_senha.save()
            update_session_auth_hash(request, user)
            alterou_algo = True

        if nova_senha_portao:
            config.senha_portao = nova_senha_portao
            config.save()
            alterou_algo = True

        if alterou_algo:
            messages.success(request, "Senha(s) alterada(s) com sucesso.")
            return redirect("escola:painel_sms")
    else:
        form_senha = PasswordChangeForm(request.user)

    return render(request, "escola/admin_alterar_senha.html", {
        "form_senha": form_senha,
        "senha_portao_atual": config.senha_portao,
    })


def _aluno_publico(request):
    aluno_id = request.session.get("aluno_publico_id")
    if not aluno_id:
        return None
    return Aluno.objects.filter(pk=aluno_id, ativo=True).first()


@never_cache
def encarregado_professores(request):
    aluno = _aluno_publico(request)
    if not aluno:
        messages.error(request, "Insira primeiro o número de matrícula do aluno.")
        return redirect("/contributo/")
    resposta_nova = MensagemEncarregado.objects.filter(
        aluno=aluno, professor=OuterRef("pk"), do_professor=True, lida=False
    )
    professores = Funcionario.objects.filter(ativo=True).annotate(
        tem_notificacao=Exists(resposta_nova)
    ).order_by("nome")
    return render(request, "escola/encarregado_professores.html", {
        "aluno": aluno, "professores": professores,
    })


@never_cache
def encarregado_conversa(request, func_pk):
    from .models import MensagemEncarregado
    aluno = _aluno_publico(request)
    if not aluno:
        messages.error(request, "Insira primeiro o número de matrícula do aluno.")
        return redirect("/contributo/")
    professor = get_object_or_404(Funcionario, pk=func_pk, ativo=True)

    form = MensagemAlunoForm()
    if request.method == "POST":
        form = MensagemAlunoForm(request.POST, request.FILES)
        if form.is_valid():
            MensagemEncarregado.objects.create(
                aluno=aluno,
                professor=professor,
                do_professor=False,
                mensagem=form.cleaned_data["mensagem"],
                anexo=form.cleaned_data["anexo"],
            )
            return redirect("escola:encarregado_conversa", func_pk=func_pk)

    MensagemEncarregado.objects.filter(
        aluno=aluno, professor=professor, do_professor=True, lida=False
    ).update(lida=True)
    conversa = MensagemEncarregado.objects.filter(aluno=aluno, professor=professor)
    return render(request, "escola/encarregado_conversa.html", {
        "aluno": aluno, "professor": professor, "conversa": conversa, "form": form,
    })


@never_cache
def encarregado_conversa_pdf(request, func_pk):
    from .models import MensagemEncarregado
    aluno = _aluno_publico(request)
    if not aluno:
        return redirect("/contributo/")
    professor = get_object_or_404(Funcionario, pk=func_pk, ativo=True)
    itens = [
        {"tipo": "direcao" if m.do_professor else "aluno",
         "texto": m.mensagem, "anexo": m.anexo, "quando": m.criado_em}
        for m in MensagemEncarregado.objects.filter(aluno=aluno, professor=professor)
    ]
    nome = f"conversa_{aluno.nome.replace(' ', '_')}_{professor.nome.replace(' ', '_')}.pdf"
    return _gerar_pdf_conversa(
        f"Conversa sobre {aluno.nome}", f"Encarregado e Professor/a {professor.nome}", itens, nome,
        rotulo_resposta="Resposta da Direção"
    )


def _conversa_direcao(aluno):
    conversa = []
    for c in Contributo.objects.filter(aluno=aluno):
        conversa.append({"tipo": "aluno", "texto": c.mensagem, "anexo": c.anexo, "quando": c.criado_em})
        if c.resposta or c.resposta_anexo:
            conversa.append({"tipo": "direcao", "texto": c.resposta, "anexo": c.resposta_anexo, "quando": c.respondido_em or c.criado_em})
    for m in MensagemDirecaoAluno.objects.filter(aluno=aluno):
        conversa.append({"tipo": "direcao", "texto": m.mensagem, "anexo": m.anexo, "quando": m.criado_em})
    conversa.sort(key=lambda e: e["quando"])
    return conversa


@never_cache
def encarregado_direcao(request):
    aluno = _aluno_publico(request)
    if not aluno:
        messages.error(request, "Insira primeiro o número de matrícula do aluno.")
        return redirect("/contributo/")
    form = MensagemAlunoForm()
    if request.method == "POST":
        form = MensagemAlunoForm(request.POST, request.FILES)
        if form.is_valid():
            Contributo.objects.create(
                aluno=aluno,
                mensagem=form.cleaned_data["mensagem"],
                anexo=form.cleaned_data["anexo"],
            )
            return redirect("escola:encarregado_direcao")
    MensagemDirecaoAluno.objects.filter(aluno=aluno, vista_aluno=False).update(vista_aluno=True)
    Contributo.objects.filter(aluno=aluno, resposta_vista=False).update(resposta_vista=True)
    return render(request, "escola/encarregado_direcao.html", {
        "aluno": aluno, "conversa": _conversa_direcao(aluno), "form": form,
    })


@never_cache
def encarregado_direcao_pdf(request):
    aluno = _aluno_publico(request)
    if not aluno:
        return redirect("/contributo/")
    nome = f"conversa_{aluno.nome.replace(' ', '_')}.pdf"
    return _gerar_pdf_conversa(
        f"Conversa sobre {aluno.nome}", "Fala com a Direção da Escola", _conversa_direcao(aluno), nome
    )


from .models import MensagemEncarregado


def funcionario_encarregados(request, pk):
    funcionario = get_object_or_404(Funcionario, pk=pk, ativo=True)
    if not _exige_desbloqueio(request, funcionario):
        messages.error(request, "Digite a sua senha primeiro.")
        return redirect("escola:funcionario_detail", pk=pk)
    nao_lida = MensagemEncarregado.objects.filter(
        aluno=OuterRef("pk"), professor=funcionario, do_professor=False, lida=False
    )
    alunos = Aluno.objects.filter(
        mensagens_encarregado__professor=funcionario
    ).distinct().annotate(tem_notificacao=Exists(nao_lida)).order_by("nome")
    return render(request, "escola/funcionario_encarregados.html", {"f": funcionario, "alunos": alunos})


def funcionario_encarregado_conversa(request, pk, aluno_pk):
    funcionario = get_object_or_404(Funcionario, pk=pk, ativo=True)
    aluno = get_object_or_404(Aluno, pk=aluno_pk)
    if not _exige_desbloqueio(request, funcionario):
        messages.error(request, "Digite a sua senha primeiro.")
        return redirect("escola:funcionario_detail", pk=pk)
    form = MensagemInternaForm()
    if request.method == "POST":
        form = MensagemInternaForm(request.POST, request.FILES)
        if form.is_valid():
            MensagemEncarregado.objects.create(
                aluno=aluno, professor=funcionario, do_professor=True,
                mensagem=form.cleaned_data["mensagem"], anexo=form.cleaned_data["anexo"],
            )
            return redirect("escola:funcionario_encarregado_conversa", pk=pk, aluno_pk=aluno_pk)
    MensagemEncarregado.objects.filter(
        aluno=aluno, professor=funcionario, do_professor=False, lida=False
    ).update(lida=True)
    conversa = MensagemEncarregado.objects.filter(aluno=aluno, professor=funcionario)
    return render(request, "escola/funcionario_encarregado_conversa.html", {
        "f": funcionario, "aluno": aluno, "conversa": conversa, "form": form,
    })


def funcionario_encarregado_pdf(request, pk, aluno_pk):
    funcionario = get_object_or_404(Funcionario, pk=pk, ativo=True)
    aluno = get_object_or_404(Aluno, pk=aluno_pk)
    if not _exige_desbloqueio(request, funcionario):
        return redirect("escola:funcionario_detail", pk=pk)
    itens = [
        {"tipo": "direcao" if m.do_professor else "aluno",
         "texto": m.mensagem, "anexo": m.anexo, "quando": m.criado_em}
        for m in MensagemEncarregado.objects.filter(aluno=aluno, professor=funcionario)
    ]
    nome = f"conversa_{aluno.nome.replace(' ', '_')}_{funcionario.nome.replace(' ', '_')}.pdf"
    return _gerar_pdf_conversa(
        f"Conversa sobre {aluno.nome}", f"Encarregado e Professor/a {funcionario.nome}", itens, nome,
        rotulo_resposta="Resposta da Direção"
    )


def funcionario_presencas(request, pk):
    import datetime
    from .models import Presenca
    funcionario = get_object_or_404(Funcionario, pk=pk, ativo=True)
    if not _exige_desbloqueio(request, funcionario):
        messages.error(request, "Digite a sua senha primeiro.")
        return redirect("escola:funcionario_detail", pk=pk)

    data_txt = request.POST.get("data") or request.GET.get("data") or ""
    try:
        data = datetime.date.fromisoformat(data_txt)
    except ValueError:
        data = timezone.localdate()

    alunos = Aluno.objects.filter(
        ativo=True, classe__iexact=funcionario.classe.strip(), turma__iexact=funcionario.turma.strip()
    ).order_by("nome") if (funcionario.classe.strip() and funcionario.turma.strip()) else Aluno.objects.none()

    if request.method == "POST" and request.POST.get("acao") == "gravar":
        for a in alunos:
            estado = request.POST.get(f"estado_{a.pk}")
            if estado in ("P", "F", "J"):
                obs = request.POST.get(f"obs_{a.pk}", "").strip()[:200]
                ant = Presenca.objects.filter(aluno=a, data=data).first()
                if ant and ant.estado == estado and ant.observacao == obs:
                    continue
                Presenca.objects.update_or_create(
                    aluno=a, data=data,
                    defaults={"estado": estado, "observacao": obs,
                              "marcado_por": funcionario, "visto": estado == "P"},
                )
        messages.success(request, "Presenças gravadas.")
        return redirect(f"{request.path}?data={data.isoformat()}")

    existentes = {p.aluno_id: p for p in Presenca.objects.filter(data=data, aluno__in=alunos)}
    linhas = [{"aluno": a, "p": existentes.get(a.pk)} for a in alunos]
    return render(request, "escola/funcionario_presencas.html", {
        "f": funcionario, "data": data, "linhas": linhas,
    })


@never_cache
def encarregado_presencas(request):
    from .models import Presenca
    aluno = _aluno_publico(request)
    if not aluno:
        messages.error(request, "Insira primeiro os dados de acesso do aluno.")
        return redirect("/contributo/")
    registos = list(Presenca.objects.filter(aluno=aluno).order_by("-data"))
    Presenca.objects.filter(aluno=aluno, visto=False).update(visto=True)
    return render(request, "escola/encarregado_presencas.html", {
        "aluno": aluno,
        "registos": registos,
        "total_p": sum(1 for r in registos if r.estado == "P"),
        "total_f": sum(1 for r in registos if r.estado == "F"),
        "total_j": sum(1 for r in registos if r.estado == "J"),
        "professores": list(dict.fromkeys(r.marcado_por.nome for r in registos if r.marcado_por)),
    })


@never_cache
def encarregado_presencas_pdf(request):
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas
    from .models import Presenca
    aluno = _aluno_publico(request)
    if not aluno:
        return redirect("/contributo/")
    registos = list(Presenca.objects.filter(aluno=aluno).order_by("data"))
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="presencas_{aluno.nome.replace(" ", "_")}.pdf"'
    largura, altura = A4
    margem = 2 * cm
    y = altura - margem
    p = canvas.Canvas(response, pagesize=A4)

    def linha(texto, tamanho=11, negrito=False, espaco=15):
        nonlocal y
        if y < margem:
            p.showPage()
            y = altura - margem
        p.setFont("Helvetica-Bold" if negrito else "Helvetica", tamanho)
        p.drawString(margem, y, texto[:100])
        y -= espaco

    tp = sum(1 for r in registos if r.estado == "P")
    tf = sum(1 for r in registos if r.estado == "F")
    tj = sum(1 for r in registos if r.estado == "J")
    linha("Presenças, Faltas e Justificações", 14, True, 22)
    linha(f"Aluno: {aluno.nome}", 11, False, 18)
    linha(f"Presenças: {tp}   Faltas: {tf}   Justificadas: {tj}", 11, True, 22)
    if not registos:
        linha("Ainda não há registos.")
    for r in registos:
        txt = f"{r.data:%d/%m/%Y} - {r.get_estado_display()}"
        if r.observacao:
            txt += f" ({r.observacao})"
        linha(txt)
    p.showPage()
    p.save()
    return response


@never_cache
def avisos_escola(request):
    from django.db.models import Q
    from .models import Aviso
    aluno = _aluno_publico(request)
    qs = Aviso.objects.filter(publicado=True)
    if aluno and aluno.classe.strip():
        qs = qs.filter(Q(classe="") | Q(classe__iexact=aluno.classe.strip()))
    else:
        qs = qs.filter(classe="")
    hoje = timezone.localdate()
    ultimo = Aviso.objects.filter(publicado=True).order_by("-id").first()
    if ultimo:
        request.session["avisos_visto_id"] = ultimo.id
    return render(request, "escola/avisos.html", {
        "proximos": qs.filter(data_evento__gte=hoje).order_by("data_evento"),
        "passados": qs.filter(data_evento__lt=hoje).order_by("-data_evento")[:10],
        "aluno": aluno,
    })


def funcionario_notas(request, pk):
    from decimal import Decimal, InvalidOperation
    from .models import Disciplina, Nota
    funcionario = get_object_or_404(Funcionario, pk=pk, ativo=True)
    if not _exige_desbloqueio(request, funcionario):
        messages.error(request, "Digite a sua senha primeiro.")
        return redirect("escola:funcionario_detail", pk=pk)

    disciplinas = list(Disciplina.objects.all())
    try:
        disc = next(d for d in disciplinas if str(d.pk) == (request.POST.get("disciplina") or request.GET.get("disciplina") or ""))
    except StopIteration:
        disc = disciplinas[0] if disciplinas else None
    try:
        tri = int(request.POST.get("trimestre") or request.GET.get("trimestre") or 1)
    except ValueError:
        tri = 1
    if tri not in (1, 2, 3):
        tri = 1

    if funcionario.classe.strip() and funcionario.turma.strip():
        alunos = Aluno.objects.filter(
            ativo=True, classe__iexact=funcionario.classe.strip(), turma__iexact=funcionario.turma.strip()
        ).order_by("nome")
    else:
        alunos = Aluno.objects.none()

    if request.method == "POST" and request.POST.get("acao") == "gravar" and disc:
        for a in alunos:
            txt = request.POST.get(f"nota_{a.pk}", "").strip().replace(",", ".")
            if not txt:
                continue
            try:
                valor = Decimal(txt)
            except InvalidOperation:
                continue
            if valor < 0 or valor > 10:
                continue
            ant = Nota.objects.filter(aluno=a, disciplina=disc, trimestre=tri).first()
            if ant and ant.valor == valor:
                continue
            Nota.objects.update_or_create(
                aluno=a, disciplina=disc, trimestre=tri,
                defaults={"valor": valor, "marcado_por": funcionario, "visto": False},
            )
        messages.success(request, "Notas gravadas.")
        return redirect(f"{request.path}?disciplina={disc.pk}&trimestre={tri}")

    existentes = {}
    if disc:
        existentes = {n.aluno_id: n for n in Nota.objects.filter(disciplina=disc, trimestre=tri, aluno__in=alunos)}
    linhas = [{"aluno": a, "n": existentes.get(a.pk)} for a in alunos]
    return render(request, "escola/funcionario_notas.html", {
        "f": funcionario, "disciplinas": disciplinas, "disc": disc, "tri": tri, "linhas": linhas,
    })


def _dados_boletim(aluno):
    from .models import Disciplina, Nota
    notas = {(n.disciplina_id, n.trimestre): n.valor for n in Nota.objects.filter(aluno=aluno)}
    linhas = []
    for d in Disciplina.objects.all():
        vals = [notas.get((d.pk, t)) for t in (1, 2, 3)]
        if any(v is not None for v in vals):
            linhas.append({"disc": d, "t": vals})
    medias = []
    for t in (0, 1, 2):
        col = [l["t"][t] for l in linhas if l["t"][t] is not None]
        medias.append(round(sum(col) / len(col), 1) if col else None)
    return linhas, medias


@never_cache
def encarregado_boletim(request):
    from .models import Nota
    aluno = _aluno_publico(request)
    if not aluno:
        messages.error(request, "Insira primeiro os dados de acesso do aluno.")
        return redirect("/contributo/")
    Nota.objects.filter(aluno=aluno, visto=False).update(visto=True)
    linhas, medias = _dados_boletim(aluno)
    return render(request, "escola/encarregado_boletim.html", {
        "aluno": aluno, "linhas": linhas, "medias": medias,
    })


@never_cache
def encarregado_boletim_pdf(request):
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas
    aluno = _aluno_publico(request)
    if not aluno:
        return redirect("/contributo/")
    linhas, medias = _dados_boletim(aluno)
    response = HttpResponse(content_type="application/pdf")
    nome = aluno.nome.replace(" ", "_")
    response["Content-Disposition"] = f'attachment; filename="boletim_{nome}.pdf"'
    largura, altura = A4
    margem = 2 * cm
    y = altura - margem
    p = canvas.Canvas(response, pagesize=A4)

    def fmt(v):
        return "-" if v is None else str(v)

    p.setFont("Helvetica-Bold", 14)
    p.drawString(margem, y, "Boletim de Notas")
    y -= 22
    p.setFont("Helvetica", 11)
    p.drawString(margem, y, f"Aluno: {aluno.nome}")
    y -= 26
    p.setFont("Helvetica-Bold", 10)
    p.drawString(margem, y, "Disciplina")
    for i, t in enumerate(("1o Trim.", "2o Trim.", "3o Trim.")):
        p.drawString(margem + 8 * cm + i * 3 * cm, y, t)
    y -= 18
    p.setFont("Helvetica", 10)
    for l in linhas:
        p.drawString(margem, y, l["disc"].nome[:40])
        for i, v in enumerate(l["t"]):
            p.drawString(margem + 8 * cm + i * 3 * cm, y, fmt(v))
        y -= 16
    y -= 6
    p.setFont("Helvetica-Bold", 10)
    p.drawString(margem, y, "Média")
    for i, v in enumerate(medias):
        p.drawString(margem + 8 * cm + i * 3 * cm, y, fmt(v))
    p.showPage()
    p.save()
    return response


@login_required
@never_cache
def aluno_hub(request, pk):
    aluno = get_object_or_404(Aluno, pk=pk)
    return render(request, "escola/aluno_hub.html", {
        "aluno": aluno,
        "nao_lidas": Contributo.objects.filter(aluno=aluno, lido=False).exists(),
    })


@login_required
@never_cache
def aluno_professores_direcao(request, pk):
    from .models import MensagemEncarregado
    aluno = get_object_or_404(Aluno, pk=pk)
    profs = Funcionario.objects.filter(mensagens_encarregados__aluno=aluno).distinct().order_by("nome")
    grupos = [
        {"prof": f, "msgs": MensagemEncarregado.objects.filter(aluno=aluno, professor=f)}
        for f in profs
    ]
    return render(request, "escola/aluno_professores_direcao.html", {"aluno": aluno, "grupos": grupos})


@login_required
@never_cache
def aluno_faltas_direcao(request, pk):
    from .models import Presenca
    aluno = get_object_or_404(Aluno, pk=pk)
    registos = list(Presenca.objects.filter(aluno=aluno).order_by("-data"))
    return render(request, "escola/aluno_faltas_direcao.html", {
        "aluno": aluno, "registos": registos,
        "total_p": sum(1 for r in registos if r.estado == "P"),
        "total_f": sum(1 for r in registos if r.estado == "F"),
        "total_j": sum(1 for r in registos if r.estado == "J"),
    })


@never_cache
def encarregado_pagamentos(request):
    from .models import BoletimPagamento
    aluno = _aluno_publico(request)
    if not aluno:
        messages.error(request, "Insira primeiro os dados de acesso do aluno.")
        return redirect("/contributo/")
    BoletimPagamento.objects.filter(aluno=aluno, visto=False).update(visto=True)
    anos = []
    for b in BoletimPagamento.objects.filter(aluno=aluno).order_by("-ano"):
        anos.append({"ano": b.ano, "t": [("1.º Trimestre", b.valor_1), ("2.º Trimestre", b.valor_2), ("3.º Trimestre", b.valor_3)]})
    return render(request, "escola/encarregado_pagamentos.html", {"aluno": aluno, "anos": anos})


@never_cache
def encarregado_pagamentos_pdf(request):
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas
    from .models import BoletimPagamento
    aluno = _aluno_publico(request)
    if not aluno:
        return redirect("/contributo/")
    response = HttpResponse(content_type="application/pdf")
    nome = aluno.nome.replace(" ", "_")
    response["Content-Disposition"] = f'attachment; filename="pagamentos_{nome}.pdf"'
    largura, altura = A4
    margem = 2 * cm
    y = altura - margem
    p = canvas.Canvas(response, pagesize=A4)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(margem, y, "Boletim de Pagamento por Ano")
    y -= 22
    p.setFont("Helvetica", 11)
    p.drawString(margem, y, f"Aluno: {aluno.nome}")
    y -= 26
    registos = BoletimPagamento.objects.filter(aluno=aluno).order_by("-ano")
    if not registos:
        p.drawString(margem, y, "Ainda nao ha registos de pagamento.")
    for b in registos:
        p.setFont("Helvetica-Bold", 11)
        p.drawString(margem, y, f"Ano {b.ano}")
        y -= 16
        p.setFont("Helvetica", 11)
        for rot, v in (("1o Trimestre", b.valor_1), ("2o Trimestre", b.valor_2), ("3o Trimestre", b.valor_3)):
            txt = f"{v:.2f} Kz - Pago" if v is not None else "Por pagar"
            p.drawString(margem + 0.5 * cm, y, f"{rot}: {txt}")
            y -= 15
        y -= 10
    p.showPage()
    p.save()
    return response
