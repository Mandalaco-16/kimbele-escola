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
        "tem_mensagem_direcao_nao_lida": tem_mensagem_direcao_nao_lida or _falta_nova_funcionario(funcionario),
    })


def _falta_nova_funcionario(funcionario):
    from .models import PresencaFuncionario
    return PresencaFuncionario.objects.filter(funcionario=funcionario, visto=False).exclude(estado="P").exists()


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


@never_cache
def contributo_view(request):
    aluno = None
    erro_matricula = False
    form = MensagemAlunoForm()
    if request.method == "GET":
        if request.GET.get("sair") or request.get_host() not in request.META.get("HTTP_REFERER", ""):
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

    from .models import PresencaFuncionario
    faltas = list(PresencaFuncionario.objects.filter(funcionario=funcionario).exclude(estado="P")[:15])
    PresencaFuncionario.objects.filter(funcionario=funcionario, visto=False).update(visto=True)

    return render(
        request,
        "escola/funcionario_historico.html",
        {"f": funcionario, "conversa": conversa, "form": form, "faltas": faltas},
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
    from django.db.models import Q
    filtro = Q(mensagens_encarregado__professor=funcionario)
    if funcionario.classe.strip() and funcionario.turma.strip():
        filtro = filtro | Q(ativo=True, classe__iexact=funcionario.classe.strip(), turma__iexact=funcionario.turma.strip())
    alunos = Aluno.objects.filter(filtro).distinct().annotate(tem_notificacao=Exists(nao_lida)).order_by("nome")
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


def _pauta_pdf(pauta):
    import os
    from django.conf import settings
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    resp = HttpResponse(content_type="application/pdf")
    resp["Content-Disposition"] = 'attachment; filename="pauta_%s%s_20%s.pdf"' % (pauta.classe, pauta.turma, pauta.ano_inicio)
    W, H = landscape(A4)
    c = canvas.Canvas(resp, pagesize=landscape(A4))
    larg = [24, 140] + [20] * 27 + [52, 56]
    x0 = (W - sum(larg)) / 2

    def cabecalho():
        try:
            img = ImageReader(os.path.join(settings.BASE_DIR, "escola", "static", "escola", "insignia.png"))
            c.drawImage(img, W / 2 - 20, H - 62, 40, 40, mask="auto")
        except Exception:
            pass
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(W / 2, H - 72, "REPÚBLICA DE ANGOLA")
        c.setFont("Helvetica", 9)
        c.drawCentredString(W / 2, H - 85, "GOVERNO PROVINCIAL DO UÍGE")
        c.drawCentredString(W / 2, H - 96, "ADMINISTRAÇÃO MUNICIPAL DE QUIMBELE")
        c.drawCentredString(W / 2, H - 107, "DIRECÇÃO DA EDUCAÇÃO")
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x0, H - 124, "ESCOLA PRIMÁRIA Nº %s DE %s" % (pauta.escola_numero, pauta.escola_nome))
        c.setFont("Helvetica", 9)
        c.drawString(x0, H - 138, "PAUTA PARA CLASSES DE EXAME - FORMAÇÃO GERAL")
        c.drawString(x0, H - 152, "CLASSE %sª   SALA %s   TURMA %s   PERIODO %s   ANO LECTIVO 20%s / 20%s" % (pauta.classe, pauta.sala, pauta.turma, pauta.periodo, pauta.ano_inicio, pauta.ano_fim))
        bx = W - 260
        c.rect(bx, H - 150, 220, 88)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(bx + 110, H - 76, "O CORPO DE JÚRI")
        c.setFont("Helvetica", 8)
        for i, (rot, val) in enumerate((("Presidente", pauta.presidente), ("1º Vogal", pauta.vogal1), ("2º Vogal", pauta.vogal2))):
            yy = H - 96 - i * 18
            c.drawString(bx + 8, yy, rot)
            c.line(bx + 58, yy - 2, bx + 212, yy - 2)
            c.drawString(bx + 60, yy, val[:34])

    def cab_tabela(y):
        c.setLineWidth(0.8)
        c.setFont("Helvetica-Bold", 7)
        c.rect(x0, y - 60, 24, 60)
        c.drawCentredString(x0 + 12, y - 33, "N.º")
        c.rect(x0 + 24, y - 60, 140, 60)
        c.drawCentredString(x0 + 94, y - 33, "NOME COMPLETO")
        x = x0 + 164
        for cod, rot, cols in PAUTA_DISC:
            w = len(cols) * 20
            c.setFillColorRGB(0.81, 0.89, 0.97)
            c.rect(x, y - 16, w, 16, stroke=1, fill=1)
            c.setFillColorRGB(0, 0, 0)
            c.drawCentredString(x + w / 2, y - 11, rot)
            for i, col in enumerate(cols):
                cx = x + i * 20
                if col == "med":
                    c.setFillColorRGB(0.80, 0.93, 0.80)
                else:
                    c.setFillColorRGB(1, 1, 1)
                c.rect(cx, y - 60, 20, 44, stroke=1, fill=1)
                c.setFillColorRGB(0, 0, 0)
                c.saveState()
                c.translate(cx + 13, y - 56)
                c.rotate(90)
                c.setFont("Helvetica-Bold", 7)
                c.drawString(0, 0, PAUTA_ROT[col])
                c.restoreState()
            x += w
        c.rect(x, y - 60, 52, 60)
        c.setFont("Helvetica-Bold", 6)
        c.drawCentredString(x + 26, y - 33, "COMPORTAMENTO")
        c.rect(x + 52, y - 60, 56, 60)
        c.drawCentredString(x + 80, y - 30, "RESULTADO")
        c.drawCentredString(x + 80, y - 38, "FINAL")
        return y - 60

    cabecalho()
    y = cab_tabela(H - 170)
    for l in pauta.linhas.all():
        if y - 16 < 30:
            c.showPage()
            y = cab_tabela(H - 30)
        c.setFont("Helvetica", 8)
        x = x0
        c.rect(x, y - 16, 24, 16)
        c.drawCentredString(x + 12, y - 11, str(l.numero))
        x += 24
        c.rect(x, y - 16, 140, 16)
        c.drawString(x + 3, y - 11, l.nome[:30])
        x += 140
        for cod, rot, cols in PAUTA_DISC:
            for col in cols:
                if col == "med":
                    c.setFillColorRGB(0.80, 0.93, 0.80)
                    c.rect(x, y - 16, 20, 16, stroke=1, fill=1)
                else:
                    c.rect(x, y - 16, 20, 16)
                val = getattr(l, cod + "_" + col)
                try:
                    nota = float(val.replace(",", "."))
                except ValueError:
                    nota = None
                if nota is None:
                    c.setFillColorRGB(0, 0, 0)
                elif nota < 5:
                    c.setFillColorRGB(0.85, 0, 0)
                else:
                    c.setFillColorRGB(0.03, 0.27, 0.68)
                c.drawCentredString(x + 10, y - 11, val)
                c.setFillColorRGB(0, 0, 0)
                x += 20
        c.rect(x, y - 16, 52, 16)
        c.setFont("Helvetica", 7)
        c.drawCentredString(x + 26, y - 11, l.comportamento[:12])
        c.rect(x + 52, y - 16, 56, 16)
        c.drawCentredString(x + 80, y - 11, _pauta_res_txt(l.resultado, l.nome))
        y -= 16
    try:
        img = ImageReader(os.path.join(settings.BASE_DIR, "escola", "static", "escola", "carimbo.jpg"))
        iw, ih = img.getSize()
        w = 130.0
        cl = 0.09
        wf = w / (1 - cl)
        h = wf * ih / iw
        if y - h - 40 < 20:
            c.showPage()
            y = H - 40
        xr = x0 + sum(larg) - w - 10
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(xr + w / 2, y - 22, "O Director")
        top = y - 28
        c.saveState()
        cp = c.beginPath()
        cp.rect(xr, top - h, w, h)
        c.clipPath(cp, stroke=0, fill=0)
        c.drawImage(img, xr - cl * wf, top - h, wf, h, mask=[165, 255, 165, 255, 165, 255])
        c.restoreState()
    except Exception:
        pass
    c.showPage()
    c.save()
    return resp


@login_required
@never_cache
def pauta_pdf(request, pk):
    from .models import Pauta
    return _pauta_pdf(get_object_or_404(Pauta, pk=pk))


@never_cache
def funcionario_pauta_pdf(request, pk):
    from .models import Pauta
    funcionario = get_object_or_404(Funcionario, pk=pk, ativo=True)
    if not _exige_desbloqueio(request, funcionario):
        return redirect("escola:funcionario_detail", pk=pk)
    ini, fim = _pauta_ano_atual()
    pauta = get_object_or_404(
        Pauta, classe__iexact=funcionario.classe.strip(), turma__iexact=funcionario.turma.strip(), ano_inicio=ini
    )
    return _pauta_pdf(pauta)


PAUTA_DISC = [
    ("lport", "L.PORT", ("med", "ne", "nf")),
    ("mat", "MAT.", ("med", "ne", "nf")),
    ("hist", "HIST.", ("med", "ne", "nf")),
    ("geo", "GEO", ("med", "ne", "nf")),
    ("cnat", "C NAT", ("med", "ne", "nf")),
    ("emc", "EM.C", ("med", "ne", "nf")),
    ("emp", "E.M.P", ("med", "ne", "nf")),
    ("edmus", "ED.MUS", ("med", "ne", "nf")),
    ("edfis", "ED.FIS", ("med", "ne", "nf")),
]
PAUTA_ROT = {"med": "MFD", "ne": "NE", "nf": "MF"}


def _pauta_ano_atual():
    hoje = timezone.localdate()
    ini = hoje.year if hoje.month >= 9 else hoje.year - 1
    return f"{ini % 100:02d}", f"{(ini + 1) % 100:02d}"


def _pauta_sincronizar(pauta):
    from .models import PautaLinha
    ja = set(pauta.linhas.exclude(aluno=None).values_list("aluno_id", flat=True))
    proximo = (pauta.linhas.order_by("-numero").values_list("numero", flat=True).first() or 0) + 1
    alunos = Aluno.objects.filter(
        ativo=True, classe__iexact=pauta.classe.strip(), turma__iexact=pauta.turma.strip()
    ).order_by("nome")
    for a in alunos:
        if a.pk not in ja:
            PautaLinha.objects.create(pauta=pauta, numero=proximo, aluno=a, nome=a.nome)
            proximo += 1


def _pauta_contexto(pauta, editar_cabecalho):
    _pauta_numerar(pauta)
    linhas = []
    for l in pauta.linhas.all():
        cells = []
        for cod, rot, cols in PAUTA_DISC:
            for c in cols:
                campo = cod + "_" + c
                cells.append({"campo": campo, "valor": getattr(l, campo)})
        linhas.append({"obj": l, "cells": cells, "fem": _pauta_genero(l.nome) == "f"})
    discs = [{"rot": rot, "n": len(cols), "cols": [PAUTA_ROT[c] for c in cols]} for cod, rot, cols in PAUTA_DISC]
    return {"pauta": pauta, "linhas": linhas, "discs": discs, "editar_cabecalho": editar_cabecalho}


PAUTA_MAX_NEGATIVAS = 0


def _pauta_mfd(ne, mf):
    return str(int((float(ne.replace(",", ".")) + float(mf.replace(",", "."))) / 2 + 0.5))


PAUTA_FEM_SEM_A = {"ester", "raquel", "isabel", "beatriz", "ines", "ruth", "rute", "carmen", "mercedes", "lourdes", "dolores", "abigail", "judite", "alice", "denise", "elisabete", "joyce", "nice", "dulce", "cleide", "aline", "eunice", "janete", "ivone", "yvone", "marie", "michele", "sarah", "esther", "noemi", "miriam"}
PAUTA_MASC_COM_A = {"luca", "joshua", "josua", "mustafa", "jonata"}


def _pauta_genero(nome):
    import unicodedata
    partes = (nome or "").strip().split()
    if not partes:
        return "m"
    p = unicodedata.normalize("NFD", partes[0].lower())
    p = "".join(ch for ch in p if unicodedata.category(ch) != "Mn")
    if p in PAUTA_FEM_SEM_A:
        return "f"
    if p in PAUTA_MASC_COM_A:
        return "m"
    return "f" if p.endswith("a") else "m"


def _pauta_res_txt(res, nome):
    if _pauta_genero(nome) == "f":
        return {"Aprovado": "Aprovada", "Reprovado": "Reprovada"}.get(res, res)
    return res


def _pauta_numerar(pauta):
    for i, l in enumerate(pauta.linhas.order_by("nome"), 1):
        if l.numero != i:
            l.numero = i
            l.save(update_fields=["numero"])


def _pauta_gravar(request, pauta, editar_cabecalho):
    invalidas = 0
    if True:
        for f in (("escola_numero", "escola_nome", "sala", "periodo", "ano_inicio", "ano_fim", "presidente", "vogal1", "vogal2") if editar_cabecalho else ("presidente", "vogal1", "vogal2")):
            if "h_" + f in request.POST:
                setattr(pauta, f, request.POST.get("h_" + f, "").strip()[:150])
        pauta.save()
    for l in pauta.linhas.all():
        for cod, rot, cols in PAUTA_DISC:
            for c in cols:
                campo = cod + "_" + c
                raw = request.POST.get("l" + str(l.pk) + "_" + campo, "").strip()[:6]
                ok = raw == ""
                if raw:
                    try:
                        ok = 0 <= float(raw.replace(",", ".")) <= 10
                    except ValueError:
                        ok = False
                if ok:
                    setattr(l, campo, raw)
                else:
                    invalidas += 1
            ne_v = getattr(l, cod + "_ne")
            mf_v = getattr(l, cod + "_nf")
            if ne_v and mf_v:
                setattr(l, cod + "_med", _pauta_mfd(ne_v, mf_v))
        l.comportamento = request.POST.get("l" + str(l.pk) + "_comportamento", "").strip()[:30]
        l.resultado = request.POST.get("l" + str(l.pk) + "_resultado", "").strip()[:30]
        meds = []
        for cod, rot, cols in PAUTA_DISC:
            try:
                meds.append(float(getattr(l, cod + "_med").replace(",", ".")))
            except ValueError:
                pass
        if len(meds) == len(PAUTA_DISC) and l.resultado != "Desistente":
            l.resultado = "Reprovado" if sum(1 for m in meds if m < 5) > PAUTA_MAX_NEGATIVAS else "Aprovado"
        l.save()
    if invalidas:
        messages.warning(request, "Algumas notas não foram gravadas: só são aceites valores de 0 a 10.")


@login_required
@never_cache
def pauta_lista(request):
    from .models import Pauta
    if request.method == "POST" and request.POST.get("acao") == "criar":
        classe = request.POST.get("classe", "").strip()
        turma = request.POST.get("turma", "").strip()
        ini, fim = _pauta_ano_atual()
        if classe and turma:
            pauta = Pauta.objects.filter(classe__iexact=classe, turma__iexact=turma, ano_inicio=ini).first()
            if not pauta:
                pauta = Pauta.objects.create(classe=classe, turma=turma, ano_inicio=ini, ano_fim=fim)
            _pauta_sincronizar(pauta)
            return redirect("escola:pauta_direcao", pk=pauta.pk)
        messages.error(request, "Escreva a classe e a turma.")
    return render(request, "escola/pauta_lista.html", {"pautas": Pauta.objects.all()})


@login_required
@never_cache
def pauta_direcao(request, pk):
    from .models import Pauta
    from django.urls import reverse
    pauta = get_object_or_404(Pauta, pk=pk)
    if request.method == "POST":
        if request.POST.get("acao") == "atualizar":
            _pauta_sincronizar(pauta)
            messages.success(request, "Lista de alunos atualizada.")
        else:
            _pauta_gravar(request, pauta, True)
            messages.success(request, "Pauta gravada.")
        return redirect("escola:pauta_direcao", pk=pk)
    if not pauta.linhas.exists():
        _pauta_sincronizar(pauta)
    ctx = _pauta_contexto(pauta, True)
    ctx["url_pdf"] = reverse("escola:pauta_pdf", args=[pk])
    ctx["url_voltar"] = reverse("escola:pauta_lista")
    return render(request, "escola/pauta.html", ctx)


@never_cache
def funcionario_pauta(request, pk):
    from .models import Pauta
    from django.urls import reverse
    funcionario = get_object_or_404(Funcionario, pk=pk, ativo=True)
    if not _exige_desbloqueio(request, funcionario):
        messages.error(request, "Digite a sua senha primeiro.")
        return redirect("escola:funcionario_detail", pk=pk)
    classe, turma = funcionario.classe.strip(), funcionario.turma.strip()
    if not classe or not turma:
        messages.error(request, "A sua ficha não tem Classe e Turma. Peça à Direção para as preencher.")
        return redirect("escola:funcionario_detail", pk=pk)
    ini, fim = _pauta_ano_atual()
    pauta = Pauta.objects.filter(classe__iexact=classe, turma__iexact=turma, ano_inicio=ini).first()
    if not pauta:
        pauta = Pauta.objects.create(
            classe=classe, turma=turma, ano_inicio=ini, ano_fim=fim,
            sala=funcionario.sala, periodo=funcionario.periodo,
        )
    if request.method == "POST":
        if request.POST.get("acao") == "atualizar":
            _pauta_sincronizar(pauta)
            messages.success(request, "Lista de alunos atualizada.")
        else:
            _pauta_gravar(request, pauta, False)
            messages.success(request, "Pauta gravada.")
        return redirect("escola:funcionario_pauta", pk=pk)
    if not pauta.linhas.exists():
        _pauta_sincronizar(pauta)
    ctx = _pauta_contexto(pauta, False)
    ctx["url_pdf"] = reverse("escola:funcionario_pauta_pdf", args=[pk])
    ctx["url_voltar"] = reverse("escola:funcionario_detail", args=[pk])
    return render(request, "escola/pauta.html", ctx)


@never_cache
def encarregado_pauta(request):
    from .models import PautaLinha
    aluno = _aluno_publico(request)
    if not aluno:
        messages.error(request, "Insira primeiro os dados de acesso do aluno.")
        return redirect("/contributo/")
    linha = PautaLinha.objects.filter(aluno=aluno).select_related("pauta").order_by("-pauta__ano_inicio").first()
    if linha:
        request.session["pauta_vista_%s" % linha.pk] = linha.resultado
    discs = []
    if linha:
        for cod, rot, cols in PAUTA_DISC:
            vals = {c: (getattr(linha, cod + "_" + c) or "-") for c in cols}
            discs.append({"rot": rot, "med": vals.get("med"), "ne": vals.get("ne"), "nf": vals.get("nf", "-")})
    return render(request, "escola/encarregado_pauta.html", {"aluno": aluno, "linha": linha, "discs": discs, "fem": _pauta_genero(aluno.nome) == "f"})


@login_required
@never_cache
def funcionario_faltas_direcao(request, pk):
    import datetime
    from .models import PresencaFuncionario
    funcionario = get_object_or_404(Funcionario, pk=pk, ativo=True)
    data_txt = request.POST.get("data") or request.GET.get("data") or ""
    try:
        data = datetime.date.fromisoformat(data_txt)
    except ValueError:
        data = timezone.localdate()
    if request.method == "POST":
        estado = request.POST.get("estado")
        obs = request.POST.get("obs", "").strip()[:200]
        if estado in ("P", "F", "J"):
            ant = PresencaFuncionario.objects.filter(funcionario=funcionario, data=data).first()
            if not (ant and ant.estado == estado and ant.observacao == obs):
                PresencaFuncionario.objects.update_or_create(
                    funcionario=funcionario, data=data,
                    defaults={"estado": estado, "observacao": obs, "visto": estado == "P"},
                )
            messages.success(request, "Registo gravado.")
        return redirect(f"{request.path}?data={data.isoformat()}")
    atual = PresencaFuncionario.objects.filter(funcionario=funcionario, data=data).first()
    registos = list(PresencaFuncionario.objects.filter(funcionario=funcionario)[:30])
    return render(request, "escola/funcionario_faltas_direcao.html", {
        "funcionario": funcionario, "data": data, "atual": atual, "registos": registos,
        "total_f": sum(1 for r in registos if r.estado == "F"),
        "total_j": sum(1 for r in registos if r.estado == "J"),
    })


def _cor_nota(c, val):
    try:
        n = float(val.replace(",", "."))
    except ValueError:
        c.setFillColorRGB(0, 0, 0)
        return
    if n < 5:
        c.setFillColorRGB(0.85, 0, 0)
    else:
        c.setFillColorRGB(0.03, 0.27, 0.68)


@never_cache
def encarregado_pauta_pdf(request):
    import os
    from django.conf import settings
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas
    from .models import PautaLinha
    aluno = _aluno_publico(request)
    if not aluno:
        return redirect("/contributo/")
    l = PautaLinha.objects.filter(aluno=aluno).select_related("pauta").order_by("-pauta__ano_inicio").first()
    if not l:
        return redirect("escola:encarregado_pauta")
    pa = l.pauta
    resp = HttpResponse(content_type="application/pdf")
    nome = aluno.nome.replace(" ", "_")
    resp["Content-Disposition"] = 'attachment; filename="pauta_%s.pdf"' % nome
    W, H = A4
    c = canvas.Canvas(resp, pagesize=A4)
    y = H - 1.5 * cm
    try:
        img = ImageReader(os.path.join(settings.BASE_DIR, "escola", "static", "escola", "insignia.png"))
        c.drawImage(img, W / 2 - 20, y - 40, 40, 40, mask="auto")
    except Exception:
        pass
    y -= 54
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(W / 2, y, "REPÚBLICA DE ANGOLA")
    c.setFont("Helvetica", 9)
    for linha in ("GOVERNO PROVINCIAL DO UÍGE", "ADMINISTRAÇÃO MUNICIPAL DE QUIMBELE", "DIRECÇÃO DA EDUCAÇÃO"):
        y -= 12
        c.drawCentredString(W / 2, y, linha)
    y -= 22
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(W / 2, y, "ESCOLA PRIMÁRIA Nº %s DE %s" % (pa.escola_numero, pa.escola_nome.upper()))
    y -= 14
    c.setFont("Helvetica", 9)
    c.drawCentredString(W / 2, y, "PAUTA PARA CLASSES DE EXAME - FORMAÇÃO GERAL")
    y -= 13
    c.drawCentredString(W / 2, y, "CLASSE %sª   SALA %s   TURMA %s   ANO LECTIVO 20%s / 20%s" % (pa.classe, pa.sala, pa.turma, pa.ano_inicio, pa.ano_fim))
    y -= 26
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y, "Aluno: %s" % aluno.nome)
    y -= 22
    larg = [6.4 * cm, 3.2 * cm, 3.2 * cm, 3.2 * cm]
    x0 = 2 * cm
    c.setFont("Helvetica-Bold", 9)
    x = x0
    for txt, w in zip(("DISCIPLINA", "MFD", "NE", "MF"), larg):
        c.setFillColorRGB(0.81, 0.89, 0.97)
        c.rect(x, y - 16, w, 18, stroke=1, fill=1)
        c.setFillColorRGB(0, 0, 0)
        c.drawCentredString(x + w / 2, y - 11, txt)
        x += w
    y -= 16
    for cod, rot, cols in PAUTA_DISC:
        x = x0
        c.setFillColorRGB(0.81, 0.89, 0.97)
        c.rect(x, y - 18, larg[0], 18, stroke=1, fill=1)
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 9)
        c.drawString(x + 4, y - 12, rot)
        x += larg[0]
        for col, w in zip(("med", "ne", "nf"), larg[1:]):
            val = getattr(l, cod + "_" + col) or "-"
            if col == "med":
                c.setFillColorRGB(0.80, 0.93, 0.80)
                c.rect(x, y - 18, w, 18, stroke=1, fill=1)
            else:
                c.rect(x, y - 18, w, 18)
            _cor_nota(c, val)
            c.setFont("Helvetica-Bold", 9)
            c.drawCentredString(x + w / 2, y - 12, val)
            c.setFillColorRGB(0, 0, 0)
            x += w
        y -= 18
    y -= 22
    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, y, "Comportamento: %s" % (l.comportamento or "-"))
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, y, "Resultado final: %s" % (_pauta_res_txt(l.resultado, aluno.nome) or "ainda não publicado"))
    c.setFont("Helvetica", 8)
    y -= 18
    c.drawString(2 * cm, y, "MFD: média final da disciplina; NE: nota do exame; MF: média final.")
    try:
        img = ImageReader(os.path.join(settings.BASE_DIR, "escola", "static", "escola", "carimbo.jpg"))
        iw, ih = img.getSize()
        w = 130.0
        cl = 0.09
        wf = w / (1 - cl)
        h = wf * ih / iw
        xr = W - 2 * cm - w
        top = y - 24
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(xr + w / 2, top + 8, "O Director")
        c.saveState()
        cp = c.beginPath()
        cp.rect(xr, top - h, w, h)
        c.clipPath(cp, stroke=0, fill=0)
        c.drawImage(img, xr - cl * wf, top - h, wf, h, mask=[165, 255, 165, 255, 165, 255])
        c.restoreState()
    except Exception:
        pass
    c.showPage()
    c.save()
    return resp
