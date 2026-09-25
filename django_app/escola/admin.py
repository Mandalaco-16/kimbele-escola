from django.contrib import admin
from .models import (
    Contributo,
    Documento,
    Funcionario,
    ImagemGaleria,
    MensagemInterna,
    MensagemDirecao,
    DesenvolvidorSite,
)


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ("nome", "cargo", "desde", "turma", "classe", "sala", "periodo", "ativo", "ordem")
    list_filter = ("ativo", "cargo")
    search_fields = ("nome", "cargo", "disciplinas")
    list_editable = ("ordem",)
    fieldsets = (
        ("Identificação", {"fields": ("nome", "cargo", "desde", "foto", "ativo", "ordem")}),
        ("Ensino", {"fields": ("disciplinas", "turma", "classe", "sala", "periodo", "entrada", "saida")}),
        ("Contactos", {"fields": ("telefone", "whatsapp", "email")}),
        ("Segurança", {"fields": ("senha_pin",)}),
    )


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "categoria", "publicado_em", "ativo")
    list_filter = ("categoria", "ativo")
    search_fields = ("titulo",)


@admin.register(ImagemGaleria)
class ImagemGaleriaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "categoria", "publicado_em", "ativo")
    list_filter = ("categoria", "ativo")
    search_fields = ("titulo",)


@admin.register(MensagemInterna)
class MensagemInternaAdmin(admin.ModelAdmin):
    list_display = ("remetente", "destinatario", "criado_em")
    list_filter = ("remetente", "destinatario")
    readonly_fields = ("remetente", "destinatario", "mensagem", "anexo", "criado_em")
    search_fields = ("mensagem",)


@admin.register(MensagemDirecao)
class MensagemDirecaoAdmin(admin.ModelAdmin):
    list_display = ("funcionario", "criado_em", "lida")
    list_filter = ("funcionario", "lida")
    search_fields = ("mensagem",)


@admin.register(DesenvolvidorSite)
class DesenvolvidorSiteAdmin(admin.ModelAdmin):
    list_display = ("nome", "atualizado_em")
    fields = ("nome", "informacoes")

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["informacoes"].widget.attrs["rows"] = 25
        form.base_fields["informacoes"].widget.attrs["style"] = "width: 100%;"
        return form




