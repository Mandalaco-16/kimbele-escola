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

    titulo = models.CharField("Título", max_length=200)
    categoria = models.CharField("Categoria", max_length=20, choices=Categoria.choices)
    ficheiro = models.FileField("Ficheiro", upload_to="documentos/%Y/%m/", storage=RawMediaCloudinaryStorage())
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

    titulo = models.CharField("Título", max_length=200)
    categoria = models.CharField("Categoria", max_length=20, choices=Categoria.choices)
    imagem = models.ImageField("Imagem", upload_to="galeria/%Y/%m/")
    publicado_em = models.DateTimeField("Publicado em", auto_now_add=True)
    ativo = models.BooleanField("Ativo", default=True)

    class Meta:
        verbose_name = "Imagem"
        verbose_name_plural = "Imagens"
        ordering = ["-publicado_em"]

    def __str__(self):
        return self.titulo


class Trabalhador(models.Model):
    nome = models.CharField("Nome", max_length=200)
    telefone = models.CharField("Telefone", max_length=30)

    class Meta:
        verbose_name = "Trabalhador"
        verbose_name_plural = "Trabalhadores"

    def __str__(self):
        return f"{self.nome} ({self.telefone})"


class Comunicado(models.Model):
    corpo_mensagem = models.TextField(
        "Corpo da mensagem",
        max_length=459,
        help_text="Texto que informa a falta. O link individual é acrescentado automaticamente.",
    )
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    ip_criacao = models.GenericIPAddressField("IP de origem", null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Comunicado de falta"
        verbose_name_plural = "Comunicados de falta"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"Comunicado #{self.pk} - {self.criado_em:%d/%m/%Y %H:%M}"


class Destinatario(models.Model):
    class Estado(models.TextChoices):
        PENDENTE = "PENDENTE", "Pendente"
        ENVIADO = "ENVIADO", "Enviado"
        FALHOU = "FALHOU", "Falhou"

    comunicado = models.ForeignKey(
        Comunicado, on_delete=models.CASCADE, related_name="destinatarios"
    )
    trabalhador = models.ForeignKey(
        Trabalhador, on_delete=models.SET_NULL, null=True, blank=True
    )
    telefone = models.CharField(max_length=20)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    estado_envio = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.PENDENTE
    )
    resposta_gateway = models.CharField(max_length=2000, blank=True)
    enviado_em = models.DateTimeField(null=True, blank=True)
    acedido_em = models.DateTimeField(null=True, blank=True)
    ip_acesso = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = "Destinatário"
        verbose_name_plural = "Destinatários"

    def __str__(self):
        return f"{self.telefone} - {self.get_estado_envio_display()}"


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

    class Meta:
        verbose_name = "Contributo"
        verbose_name_plural = "Contributos"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"Contributo de {self.nome or 'Anónimo'} - {self.criado_em:%d/%m/%Y}"


class DesenvolvidorSite(models.Model):
    nome = models.CharField("Nome", max_length=200, default="Desenvolvidor do site")
    informacoes = models.TextField("Informações do desenvolvedor", blank=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Desenvolvidor do site"
        verbose_name_plural = "Desenvolvidor do site"

    def __str__(self):
        return self.nome
