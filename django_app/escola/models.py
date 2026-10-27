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
        "Senha (até 20 caracteres)",
        max_length=20,
        blank=True,
        default="",
        help_text="Senha de até 20 caracteres que o funcionário usa para confirmar identidade antes de enviar mensagens à direção.",
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
    aluno = models.ForeignKey(
        "Aluno", verbose_name="Enviado para o aluno",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="contributos"
    )
    resposta = models.TextField("Resposta do administrador", blank=True)
    resposta_anexo = models.FileField(
        "Foto ou documento da resposta",
        upload_to="respostas_contributos/%Y/%m/",
        blank=True,
        null=True,
        help_text="Opcional. Aceita fotos ou ficheiros PDF para enviar junto com a resposta.",
    )
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


class MensagemDirecao(models.Model):
    funcionario = models.ForeignKey(
        Funcionario, verbose_name="Para", on_delete=models.CASCADE, related_name="mensagens_direcao"
    )
    mensagem = models.TextField("Mensagem", blank=True)
    anexo = models.FileField(
        "Foto ou documento (PDF)",
        upload_to="mensagens_direcao/%Y/%m/",
        blank=True,
        null=True,
        help_text="Opcional. Aceita fotos ou ficheiros PDF.",
    )
    criado_em = models.DateTimeField("Enviado em", auto_now_add=True)
    lida = models.BooleanField("Lida pelo funcionário", default=False)

    class Meta:
        verbose_name = "Mensagem da Direção"
        verbose_name_plural = "Mensagens da Direção"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"Direção -> {self.funcionario.nome} ({self.criado_em:%d/%m/%Y %H:%M})"


class Aluno(models.Model):
    nome = models.CharField("Nome completo", max_length=200)
    matricula = models.CharField("Número de matrícula", max_length=50, unique=True)
    turma = models.CharField("Turma", max_length=100, blank=True)
    classe = models.CharField("Classe", max_length=100, blank=True)
    sala = models.CharField("Sala", max_length=100, blank=True)
    periodo = models.CharField("Período", max_length=100, blank=True)
    entrada = models.CharField("Entrada", max_length=20, blank=True)
    saida = models.CharField("Saída", max_length=20, blank=True)
    professor = models.CharField("Nome do professor/a", max_length=200, blank=True)
    cartao_numero = models.CharField("Cartão de Estudante n°", max_length=30, blank=True)
    cartao_ano = models.CharField("Ano (20__)", max_length=4, blank=True)
    filho_de = models.CharField("Filho de", max_length=150, blank=True)
    mae = models.CharField("e de", max_length=150, blank=True)
    nascimento = models.DateField("Nascido aos", null=True, blank=True)
    anos = models.PositiveSmallIntegerField("Anos", null=True, blank=True)
    natural_de = models.CharField("Natural de", max_length=100, blank=True)
    municipio = models.CharField("Município de", max_length=100, blank=True)
    provincia = models.CharField("Província de", max_length=100, blank=True)
    emitido_em = models.DateField("Emitido aos", null=True, blank=True)
    foto = models.FileField("Foto do aluno", upload_to="alunos_fotos/", blank=True, null=True)
    ativo = models.BooleanField("Ativo", default=True)

    class Meta:
        verbose_name = "Aluno"
        verbose_name_plural = "Matricular Alunos"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} ({self.matricula})"


class MensagemDirecaoAluno(models.Model):
    aluno = models.ForeignKey(
        Aluno, verbose_name="Para", on_delete=models.CASCADE, related_name="mensagens_direcao"
    )
    mensagem = models.TextField("Mensagem", blank=True)
    anexo = models.FileField(
        "Foto ou documento (PDF)",
        upload_to="mensagens_direcao_aluno/%Y/%m/",
        blank=True,
        null=True,
        help_text="Opcional. Aceita fotos ou ficheiros PDF.",
    )
    criado_em = models.DateTimeField("Enviado em", auto_now_add=True)

    class Meta:
        verbose_name = "Mensagem da Direção ao Aluno"
        verbose_name_plural = "Mensagens da Direção aos Alunos"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"Direção -> {self.aluno.nome} ({self.criado_em:%d/%m/%Y %H:%M})"


class ConfiguracaoAcesso(models.Model):
    senha_portao = models.CharField("Senha do Acesso Reservado à Direção", max_length=50, default="927889999")

    class Meta:
        verbose_name = "Configuração de Acesso"
        verbose_name_plural = "Configuração de Acesso"

    def __str__(self):
        return "Configuração de Acesso"
