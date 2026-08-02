from django.contrib import admin
from django.contrib.admin import AdminSite
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


@admin.register(Trabalhador)
class TrabalhadorAdmin(admin.ModelAdmin):
    list_display = ("nome", "telefone")
    search_fields = ("nome", "telefone")


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ("nome", "cargo", "desde", "turma", "periodo", "ativo", "ordem")
    list_filter = ("ativo", "cargo")
    search_fields = ("nome", "cargo", "disciplinas")
    list_editable = ("ordem",)
    fieldsets = (
        ("Identificação", {"fields": ("nome", "cargo", "desde", "foto", "ativo", "ordem")}),
        ("Ensino", {"fields": ("disciplinas", "turma", "periodo", "entrada", "saida")}),
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


@admin.register(Contributo)
class ContributoAdmin(admin.ModelAdmin):
    list_display = ("nome", "funcionario", "criado_em", "lido", "tem_resposta")
    list_filter = ("lido",)
    list_editable = ("lido",)
    search_fields = ("nome", "mensagem", "resposta")
    readonly_fields = ("nome", "funcionario", "mensagem", "anexo", "criado_em")
    fields = ("nome", "funcionario", "mensagem", "anexo", "criado_em", "lido", "resposta")

    def tem_resposta(self, obj):
        return bool(obj.resposta)
    tem_resposta.boolean = True
    tem_resposta.short_description = "Respondido"

    def save_model(self, request, obj, form, change):
        if obj.resposta and not obj.respondido_em:
            from django.utils import timezone
            obj.respondido_em = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(DesenvolvidorSite)
class DesenvolvidorSiteAdmin(admin.ModelAdmin):
    list_display = ("nome", "atualizado_em")
    fields = ("nome", "informacoes")

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["informacoes"].widget.attrs["rows"] = 25
        form.base_fields["informacoes"].widget.attrs["style"] = "width: 100%;"
        return form


@admin.register(Comunicado)
class ComunicadoAdmin(admin.ModelAdmin):
    list_display = ("id", "criado_por", "criado_em")
    readonly_fields = ("criado_por", "ip_criacao", "criado_em")


@admin.register(Destinatario)
class DestinatarioAdmin(admin.ModelAdmin):
    list_display = ("telefone", "trabalhador", "comunicado", "estado_envio", "enviado_em")
    list_filter = ("estado_envio",)
    readonly_fields = ("token", "resposta_gateway", "enviado_em", "acedido_em", "ip_acesso")


# --- Sinal de sugestões/mensagens não lidas no menu do admin ---
_get_app_list_original = AdminSite.get_app_list

def _get_app_list_com_sinal(self, request, app_label=None):
    app_list = _get_app_list_original(self, request, app_label)
    nao_lidos = Contributo.objects.filter(lido=False).count()
    if nao_lidos:
        for app in app_list:
            for model in app["models"]:
                if model["object_name"] == "Contributo":
                    model["name"] = f'🔴 {model["name"]} ({nao_lidos} nova{"s" if nao_lidos != 1 else ""})'
    return app_list

AdminSite.get_app_list = _get_app_list_com_sinal
