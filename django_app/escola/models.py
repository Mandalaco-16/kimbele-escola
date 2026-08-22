import uuid
from django.conf import settings
from django.db import models
from cloudinary_storage.storage import RawMediaCloudinaryStorage

class Funcionario(models.Model):
    nome = models.CharField("Nome", max_length=200)
    cargo = models.CharField("Cargo", max_length=150)
    desde = models.DateField("Desde")
    foto = models.ImageField("Foto", upload_to="funcionarios/", blank=True, null=True)
    ativo = models.BooleanField("Ativo", default=True)
    ordem = models.PositiveIntegerField("Ordem", default=0)

    disciplinas = models.CharField("Disciplinas", max_length=200, blank=True)
    turma = models.CharField("Turma", max_length=100, blank=True)
    classe = models.CharField("Classe", max_length=100, blank=True)
    sala = models.CharField("Sala", max_length=100, blank=True)
    periodo = models.CharField("Período", max_length=100, blank=True)
    entrada = models.CharField("Entrada", max_length=20, blank=True)
    saida = models.CharField("Saída", max_length=20, blank=True)

    telefone = models.CharField("Telefone", max_length=30, blank=True)
    whatsapp = models.CharField("WhatsApp", max_length=30, blank=True)
    email = models.EmailField("E-mail", blank=True)

    senha_pin = models.CharField(
        "Senha (3 dígitos)",
        max_length=3,
        blank=True,
        default="",
        help_text="Senha de 3 dígitos que o funcionário usa para confirmar identidade antes de enviar mensagens à direção.",
    )

    class Meta:
        verbose_name = "Funcionário"
        verbose_name_plural = "Funcionários"
        ordering = ["ordem", "nome"]

    def __str__(self):
        return self.nome


class Documento(models.Model):
    class Categoria(models.TextChoices):
        REGULAMENTO = "REGULAMENTO", "Regulamento"
        VITRINE = "VITRINE", "Vitrine / Novidades"
        MUSEU = "MUSEU", "Museu da Escola"

    titulo = models.CharField("Título", max_length=200)
    categoria = models.CharField("Categoria", max_length=20, choices=Categoria.choices)
    ficheiro = models.FileField("Ficheiro", upload_to="documentos/%Y/%m/", storage=RawMediaCloudinaryStorage())
    mensagem = models.TextField(
        "Mensagem sobre o documento",
        blank=True,
        help_text="Opcional. Explica o contexto do documento para quem for ver.",
    )
    publicado_em = models.DateTimeField("Publicado em", auto_now_add=True)
    ativo = models.BooleanField("Ativo", default=True)

    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        ordering = ["-publicado_em"]

    def __str__(self):
        return self.titulo


class ImagemGaleria(models.Model):
    class Categoria(models.TextChoices):
        LAZER = "LAZER", "Lazer"
        HORARIO = "HORARIO", "Horário"
        MUSEU = "MUSEU", "Museu da Escola"

    titulo = models.CharField("Título", max_length=200)
    categoria = models.CharField("Categoria", max_length=20, choices=Categoria.choices)
    imagem = models.ImageField("Imagem", upload_to="galeria/%Y/%m/")
    mensagem = models.TextField(
        "Mensagem sobre a foto",
        blank=True,
        help_text="Opcional. Explica o contexto da foto para quem for ver.",
    )
    publicado_em = models.DateTimeField("Publicado em", auto_now_add=True)
    ativo = models.BooleanField("Ativo", default=True)

    class Meta:
        verbose_name = "Imagem"
        verbose_name_plural = "Imagens"
        ordering = ["-publicado_em"]

    def __str__(self):
        return self.titulo


class Contributo(models.Model):
    nome = models.CharField("Nome", max_length=150, blank=True, help_text="Opcional")
    mensagem = models.TextField("Mensagem", blank=True)
    anexo = models.FileField(
        "Foto ou documento (PDF)",
        upload_to="contributos/%Y/%m/",
        blank=True,
        null=True,
        help_text="Opcional. Aceita fotos ou ficheiros PDF.",
    )
    criado_em = models.DateTimeField("Enviado em", auto_now_add=True)
    lido = models.BooleanField("Lido", default=False)
    funcionario = models.ForeignKey(
        "Funcionario", verbose_name="Enviado a partir do perfil de",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="contributos"
    )
    resposta = models.TextField("Resposta do administrador", blank=True)
    respondido_em = models.DateTimeField("Respondido em", null=True, blank=True)
    resposta_vista = models.BooleanField("Resposta vista pelo funcionário", default=False)

    class Meta:
        verbose_name = "Contributo"
        verbose_name_plural = "Contributos"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"Contributo de {self.nome or 'Anónimo'} - {self.criado_em:%d/%m/%Y}"


class MensagemInterna(models.Model):
    remetente = models.ForeignKey(
        Funcionario, verbose_name="De", on_delete=models.CASCADE, related_name="mensagens_enviadas"
    )
    destinatario = models.ForeignKey(
        Funcionario, verbose_name="Para", on_delete=models.CASCADE, related_name="mensagens_recebidas"
    )
    mensagem = models.TextField("Mensagem", blank=True)
    anexo = models.FileField(
        "Foto ou documento",
        upload_to="mensagens_internas/%Y/%m/",
        blank=True,
        null=True,
        help_text="Opcional. Aceita fotos ou ficheiros PDF.",
    )
    criado_em = models.DateTimeField("Enviado em", auto_now_add=True)
    lida = models.BooleanField("Lida pelo destinatário", default=False)

    class Meta:
        verbose_name = "Mensagem entre Funcionários"
        verbose_name_plural = "Mensagens entre Funcionários"
        ordering = ["criado_em"]

    def __str__(self):
        return f"{self.remetente.nome} -> {self.destinatario.nome} ({self.criado_em:%d/%m/%Y %H:%M})"


class DesenvolvidorSite(models.Model):
    nome = models.CharField("Nome", max_length=200, default="Desenvolvidor do site")
    informacoes = models.TextField("Informações do desenvolvedor", blank=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Histórico da Escola"
        verbose_name_plural = "Histórico da Escola"

    def __str__(self):
        return self.nome
