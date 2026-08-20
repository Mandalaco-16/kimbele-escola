from django import forms
from django.contrib.auth.forms import AuthenticationForm


class ContributoForm(forms.Form):
    nome = forms.CharField(
        label="O seu nome (opcional)",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Podes deixar em branco"}),
    )
    mensagem = forms.CharField(
        label="A sua mensagem, opinião ou contributo",
        widget=forms.Textarea,
    )


class LoginAdminForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Senha incorreta. Tenta novamente.",
        "inactive": "Esta conta está inactiva.",
    }


class SenhaFuncionarioForm(forms.Form):
    senha = forms.CharField(
        label="Senha (3 dígitos)",
        max_length=3,
        widget=forms.PasswordInput(
            attrs={"inputmode": "numeric", "maxlength": "3"}
        ),
        help_text="So quem sabe a senha ve o historico e envia mensagens a direcao.",
    )


class MensagemFuncionarioForm(forms.Form):
    nome = forms.CharField(
        label="O seu nome (opcional)",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Podes deixar em branco"}),
    )
    mensagem = forms.CharField(
        label="A sua mensagem, opinião ou contributo",
        widget=forms.Textarea,
        required=False,
    )
    anexo = forms.FileField(
        label="Anexar foto ou documento (PDF)",
        required=False,
        help_text="Opcional. Aceita imagens (JPG, PNG) ou PDF.",
    )

    def clean(self):
        dados = super().clean()
        mensagem = dados.get("mensagem", "").strip()
        anexo = dados.get("anexo")
        if not mensagem and not anexo:
            raise forms.ValidationError(
                "Escreva uma mensagem ou anexe uma foto/documento antes de enviar."
            )
        return dados


class MensagemInternaForm(forms.Form):
    mensagem = forms.CharField(
        label="Mensagem",
        widget=forms.Textarea,
        required=False,
    )
    anexo = forms.FileField(
        label="Anexar foto ou documento",
        required=False,
        help_text="Opcional. Aceita imagens (JPG, PNG) ou PDF.",
    )

    def clean(self):
        dados = super().clean()
        mensagem = dados.get("mensagem", "").strip()
        anexo = dados.get("anexo")
        if not mensagem and not anexo:
            raise forms.ValidationError(
                "Escreva uma mensagem ou anexe uma foto/documento antes de enviar."
            )
        return dados


class PortaoDirecaoForm(forms.Form):
    senha = forms.CharField(
        label="Senha de acesso",
        widget=forms.PasswordInput(
            attrs={"placeholder": "Introduza a senha"}
        ),
        help_text="Acesso reservado ao Administrador da escola.",
    )

    def clean_senha(self):
        senha = self.cleaned_data["senha"].strip()
        if senha != "927889999":
            raise forms.ValidationError("Senha incorrecta. Tente novamente.")
        return senha
