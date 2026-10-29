from django import template

register = template.Library()


@register.filter
def somente_digitos(valor):
    """Remove tudo que não for número. Usado para o link do WhatsApp (wa.me)."""
    if not valor:
        return ""
    return "".join(c for c in valor if c.isdigit())


@register.filter
def tel_limpo(valor):
    """Remove espaços e parênteses, mas mantém o + no início. Usado para o link tel:."""
    if not valor:
        return ""
    limpo = "".join(c for c in valor if c.isdigit() or c == "+")
    return limpo


@register.filter
def falta_nova(aluno):
    from escola.models import Presenca
    return Presenca.objects.filter(aluno=aluno, visto=False).exclude(estado="P").exists()


@register.simple_tag(takes_context=True)
def aviso_novo(context):
    from django.db.models import Q
    from django.utils import timezone
    from escola.models import Aviso
    request = context.get("request")
    aluno = context.get("aluno")
    if request is None:
        return False
    visto = request.session.get("avisos_visto_id", 0)
    qs = Aviso.objects.filter(publicado=True, id__gt=visto, data_evento__gte=timezone.localdate())
    if aluno and aluno.classe.strip():
        qs = qs.filter(Q(classe="") | Q(classe__iexact=aluno.classe.strip()))
    else:
        qs = qs.filter(classe="")
    return qs.exists()


@register.filter
def direcao_nova(aluno):
    from django.db.models import Q
    from escola.models import Contributo, MensagemDirecaoAluno
    if not aluno:
        return False
    if MensagemDirecaoAluno.objects.filter(aluno=aluno, vista_aluno=False).exists():
        return True
    return Contributo.objects.filter(aluno=aluno, resposta_vista=False).filter(
        ~Q(resposta="") | ~Q(resposta_anexo="")
    ).exists()


@register.filter
def professor_novo(aluno):
    from escola.models import MensagemEncarregado
    if not aluno:
        return False
    return MensagemEncarregado.objects.filter(aluno=aluno, do_professor=True, lida=False).exists()


@register.filter
def nota_nova(aluno):
    from escola.models import Nota
    if not aluno:
        return False
    return Nota.objects.filter(aluno=aluno, visto=False).exists()
