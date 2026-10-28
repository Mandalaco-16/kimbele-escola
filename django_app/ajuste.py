p = "escola/models.py"
s = open(p, encoding="utf-8").read()
assert "class Presenca" not in s
s = s.rstrip("\n") + '''


class Presenca(models.Model):
    ESTADOS = [
        ("P", "Presente"),
        ("F", "Faltou"),
        ("J", "Falta justificada"),
    ]
    aluno = models.ForeignKey(
        Aluno, verbose_name="Aluno", on_delete=models.CASCADE, related_name="presencas"
    )
    data = models.DateField("Data")
    estado = models.CharField("Estado", max_length=1, choices=ESTADOS, default="P")
    observacao = models.CharField("Observação", max_length=200, blank=True)
    marcado_por = models.ForeignKey(
        Funcionario, verbose_name="Marcado por", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="presencas_marcadas",
    )

    class Meta:
        verbose_name = "Presença"
        verbose_name_plural = "Faltas e Presenças"
        ordering = ["-data", "aluno__nome"]
        unique_together = [("aluno", "data")]

    def __str__(self):
        return f"{self.aluno.nome} - {self.data:%d/%m/%Y} - {self.get_estado_display()}"
'''
open(p, "w", encoding="utf-8").write(s)

p = "escola/admin.py"
s = open(p, encoding="utf-8").read()
s = s.rstrip("\n") + '''


from .models import Presenca


@admin.register(Presenca)
class PresencaAdmin(admin.ModelAdmin):
    list_display = ("aluno", "data", "estado", "observacao", "marcado_por")
    list_filter = ("estado", "data")
    search_fields = ("aluno__nome", "aluno__matricula")
    date_hierarchy = "data"
'''
open(p, "w", encoding="utf-8").write(s)
