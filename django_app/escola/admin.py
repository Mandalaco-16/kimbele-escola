from django.contrib import admin
from .models import (
    Contributo,
    Documento,
    Funcionario,
    ImagemGaleria,
    MensagemInterna,
    MensagemDirecao,
    Aluno,
    DesenvolvidorSite,
)


from django import forms as _forms
from django.contrib.auth.hashers import make_password as _make_password


class FuncionarioAdminForm(_forms.ModelForm):
    nova_senha = _forms.CharField(
        label="Nova senha (3 a 20 caracteres)",
        required=False, min_length=3, max_length=20,
        widget=_forms.PasswordInput(render_value=False),
        help_text="Deixe em branco para manter a senha atual. A senha guardada nunca é mostrada.",
    )

    class Meta:
        model = Funcionario
        exclude = ("senha_pin",)


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    form = FuncionarioAdminForm
    list_display = ("nome", "cargo", "desde", "turma", "classe", "sala", "periodo", "ativo", "ordem")
    list_filter = ("ativo", "cargo")
    search_fields = ("nome", "cargo", "disciplinas")
    list_editable = ("ordem",)
    fieldsets = (
        ("Identificação", {"fields": ("nome", "cargo", "desde", "foto", "ativo", "ordem")}),
        ("Ensino", {"fields": ("disciplinas", "turma", "classe", "sala", "periodo", "entrada", "saida")}),
        ("Contactos", {"fields": ("telefone", "whatsapp", "email")}),
        ("Segurança", {"fields": ("nova_senha",)}),
    )

    def save_model(self, request, obj, form, change):
        nova = form.cleaned_data.get("nova_senha")
        if nova:
            obj.senha_pin = _make_password(nova)
        super().save_model(request, obj, form, change)


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
    list_display = ("nome", "criado_em", "lido", "tem_resposta")
    list_display_links = ("nome",)
    list_filter = ("lido",)
    list_editable = ("lido",)
    search_fields = ("nome", "mensagem", "resposta")
    readonly_fields = ("nome", "mensagem", "anexo", "criado_em")
    fields = ("nome", "mensagem", "anexo", "criado_em", "lido", "resposta", "resposta_anexo")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(funcionario__isnull=True, aluno__isnull=True)

    def tem_resposta(self, obj):
        return bool(obj.resposta)
    tem_resposta.boolean = True
    tem_resposta.short_description = "Respondido"

    def save_model(self, request, obj, form, change):
        if obj.resposta and not obj.respondido_em:
            from django.utils import timezone
            obj.respondido_em = timezone.now()
        super().save_model(request, obj, form, change)


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






@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ("nome", "matricula", "turma", "classe", "professor", "ativo")
    list_filter = ("ativo", "turma", "classe")
    search_fields = ("nome", "matricula", "professor")
    fieldsets = (
        (None, {"fields": (
            ("foto",),
            ("cartao_numero", "cartao_ano"),
            ("nome",),
            ("filho_de", "mae"),
            ("nascimento", "anos"),
            ("natural_de", "municipio", "provincia"),
            ("classe", "turma", "sala", "periodo"),
            ("entrada", "saida"),
            ("matricula", "emitido_em"),
            ("professor",),
            ("ativo",),
        )}),
    )





from .models import MensagemEncarregado


@admin.register(MensagemEncarregado)
class MensagemEncarregadoAdmin(admin.ModelAdmin):
    list_display = ("aluno", "professor", "do_professor", "criado_em")
    list_filter = ("professor",)


from .models import Presenca


@admin.register(Presenca)
class PresencaAdmin(admin.ModelAdmin):
    list_display = ("aluno", "data", "estado", "observacao", "marcado_por")
    list_filter = ("estado", "data")
    search_fields = ("aluno__nome", "aluno__matricula")
    date_hierarchy = "data"


from .models import Aviso


@admin.register(Aviso)
class AvisoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "data_evento", "classe", "publicado")
    list_filter = ("publicado", "classe")
    search_fields = ("titulo", "texto")


from .models import Disciplina, Nota


@admin.register(Disciplina)
class DisciplinaAdmin(admin.ModelAdmin):
    list_display = ("nome", "ordem")
    list_editable = ("ordem",)


@admin.register(Nota)
class NotaAdmin(admin.ModelAdmin):
    list_display = ("aluno", "disciplina", "trimestre", "valor", "marcado_por")
    list_filter = ("trimestre", "disciplina")
    search_fields = ("aluno__nome", "aluno__matricula")


from .models import BoletimPagamento


@admin.register(BoletimPagamento)
class BoletimPagamentoAdmin(admin.ModelAdmin):
    list_display = ("aluno", "ano", "valor_1", "valor_2", "valor_3")
    list_filter = ("ano",)
    search_fields = ("aluno__nome", "aluno__matricula")
    autocomplete_fields = ("aluno",)
