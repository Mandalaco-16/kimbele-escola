p = "escola/templates/escola/_cartao_aluno.html"
s = open(p, encoding="utf-8").read()
trocas = [
 ("max-width:100%;margin:0 auto 14px;", "max-width:340px;margin:0 auto 14px;"),
 ("font-size:12px;line-height:2;", "font-size:11px;line-height:1.9;"),
 ("display:flex;align-items:flex-start;gap:8px", "display:flex;align-items:flex-start;justify-content:center;gap:3px"),
 ("flex:1;text-align:center;line-height:1.35", "flex:1 1 auto;min-width:0;text-align:center;line-height:1.3;font-size:10px"),
 ("width:72px;height:92px;", "width:62px;height:80px;"),
]
for a, b in trocas:
    assert s.count(a) == 1, a
    s = s.replace(a, b)
open(p, "w", encoding="utf-8").write(s)
