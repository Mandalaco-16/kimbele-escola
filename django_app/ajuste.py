import re, os

# models: cortar Disciplina e Nota
p = "escola/models.py"
s = open(p, encoding="utf-8").read()
a = s.index("class Disciplina(")
b = s.index("class BoletimPagamento(")
assert "class Nota(" in s[a:b]
open(p, "w", encoding="utf-8").write(s[:a] + s[b:])

# admin: cortar os registos e os unregister
p = "escola/admin.py"
s = open(p, encoding="utf-8").read()
a = s.index("from .models import Disciplina, Nota")
b = s.index("from .models import BoletimPagamento")
s = s[:a] + s[b:]
s = "\n".join(l for l in s.split("\n") if "unregister(Nota)" not in l and "unregister(Disciplina)" not in l)
open(p, "w", encoding="utf-8").write(s)

# views: cortar as funcoes
p = "escola/views.py"
s = open(p, encoding="utf-8").read()
for nome in ("funcionario_notas", "_dados_boletim", "encarregado_boletim_pdf", "encarregado_boletim"):
    padrao = re.compile(r'(?:^@.*\n)*^def ' + nome + r'\(.*?(?=^(?:@|def |class |from |import )|\Z)', re.M | re.S)
    s, n = padrao.subn("", s, count=1)
    assert n == 1, nome
open(p, "w", encoding="utf-8").write(s)

# urls
p = "escola/urls.py"
linhas = open(p, encoding="utf-8").read().split("\n")
novas = [l for l in linhas if "funcionario_notas" not in l and "encarregado_boletim" not in l]
assert len(linhas) - len(novas) == 3, len(linhas) - len(novas)
open(p, "w", encoding="utf-8").write("\n".join(novas))

# filtro da bolinha
p = "escola/templatetags/escola_extras.py"
s = open(p, encoding="utf-8").read()
s, n = re.subn(r'@register\.filter\ndef nota_nova\(.*?(?=^@|\Z)', "", s, flags=re.M | re.S)
assert n == 1
open(p, "w", encoding="utf-8").write(s)

# templates
for f in ("funcionario_notas.html", "encarregado_boletim.html"):
    os.remove("escola/templates/escola/" + f)
