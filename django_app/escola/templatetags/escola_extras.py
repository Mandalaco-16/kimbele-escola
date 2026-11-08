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
def pagamento_novo(aluno):
    from escola.models import BoletimPagamento
    if not aluno:
        return False
    return BoletimPagamento.objects.filter(aluno=aluno, visto=False).exists()


@register.simple_tag(takes_context=True)
def pauta_nova(context):
    from escola.models import PautaLinha
    request = context.get("request")
    aluno = context.get("aluno")
    if request is None or not aluno:
        return False
    l = PautaLinha.objects.filter(aluno=aluno).order_by("-pauta__ano_inicio").first()
    if not l or not l.resultado:
        return False
    return request.session.get("pauta_vista_%s" % l.pk) != l.resultado


@register.simple_tag
def alunos_com_mensagem():
    from escola.models import Contributo
    return Contributo.objects.filter(aluno__isnull=False, lido=False).exists()


@register.simple_tag(takes_context=True)
def novidade_escola(context, chave):
    import time
    import unicodedata
    from datetime import datetime
    from django.utils import timezone
    request = context.get("request")
    if request is None:
        return False
    k = "visto_" + chave
    visto = request.session.get(k)
    if visto is None:
        request.session[k] = time.time()
        return False
    try:
        desde = datetime.fromtimestamp(visto, tz=timezone.get_current_timezone())
        from escola.models import Documento, ImagemGaleria, DesenvolvidorSite
        if chave == "historia":
            return DesenvolvidorSite.objects.filter(atualizado_em__gt=desde).exists()
        def norm(t):
            return "".join(ch for ch in unicodedata.normalize("NFD", str(t).lower()) if unicodedata.category(ch) != "Mn")
        vd = [v for v, r in Documento.Categoria.choices if chave in norm(v) or chave in norm(r)]
        vi = [v for v, r in ImagemGaleria.Categoria.choices if chave in norm(v) or chave in norm(r)]
        return (Documento.objects.filter(categoria__in=vd, ativo=True, publicado_em__gt=desde).exists()
                or ImagemGaleria.objects.filter(categoria__in=vi, ativo=True, publicado_em__gt=desde).exists())
    except Exception:
        return False
