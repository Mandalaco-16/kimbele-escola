# Projeto Kimbele Escola — versão RECONSTRUÍDA

⚠️ **Leia isto antes de usar.**

O servidor original (Contabo) ficou inacessível porque o acesso foi
revogado pela instituição que fornecia as credenciais. Como nenhum
backup tinha sido descarregado antes disso, **os dados reais**
(funcionários cadastrados, fotos, documentos enviados, sugestões
recebidas, histórico de SMS) **foram perdidos** e não podem ser
recuperados por mim nem por si.

Este projeto foi reconstruído a partir de tudo o que apareceu nos
prints e comandos partilhados ao longo da nossa conversa. **Não é uma
cópia perfeita** — está longe disso. Ficheiros inteiros nunca foram
mostrados (parte do CSS, alguns templates, o `services.py` da
Infobip, `requirements.txt`, etc.) e foram recriados como esqueleto,
marcados com comentários `# TODO` ou `<!-- TODO -->` explicando o que
precisa de revisão.

## O que está razoavelmente completo
- `models.py` — Contributo e DesenvolvidorSite (100% confirmados);
  Funcionario, Documento, ImagemGaleria, Comunicado, Destinatario
  reconstruídos com boa confiança
- `admin.py` — Contributo e DesenvolvidorSite completos
- `views.py` — funcionario_detail, contributo_view, vitrine,
  desenvolvidor_view confirmados; painel_sms e login aproximados
- Templates: `funcionarios_lista.html`, `funcionario_detail.html`,
  `contributo.html`, `desenvolvidor.html` — vistos por completo
- `core/urls.py`, `context_processors.py` — confirmados

## O que precisa de trabalho seu
- `style.css` — só uma fração do CSS original foi vista; o visual
  completo (cores do menu verde, fundo creme, etc.) precisa de ser
  refeito ou ajustado
- `services.py` (integração Infobip) — nunca foi visto, é apenas um
  exemplo genérico
- `login.html`, `galeria_lista.html`, `documentos_lista.html`,
  `falta_detail.html` — nunca vistos em detalhe, são reconstruções
  genéricas
- `requirements.txt` — lista inferida, não confirmada
- Logotipo e fotos da escola — precisam ser adicionados de novo em
  `django_app/escola/static/escola/img/`

## Antes de publicar este projeto num servidor novo
1. **Gere uma SECRET_KEY nova** em `core/settings.py` (nunca reutilize)
2. **Defina senhas novas** para o PostgreSQL e para o admin do Django
3. Preencha o ficheiro `.env` (copie de `.env.example`) com dados reais
4. Desta vez, **use uma conta de hospedagem que só você controla** —
   evite depender de acesso emprestado/temporário de terceiros
5. Configure **backups automáticos regulares** (ex: `pg_dump` agendado
   com `cron`, enviado para o Google Drive) desde o primeiro dia

## Próximo passo sugerido
Escolher onde hospedar (ex: um VPS próprio, ou uma plataforma como o
Render) e recriar o banco de dados e o conteúdo (funcionários,
documentos, fotos) manualmente a partir do zero.
