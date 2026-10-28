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
