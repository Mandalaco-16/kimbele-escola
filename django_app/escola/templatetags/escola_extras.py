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
