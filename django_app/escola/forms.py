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
        label="Senha (até 20 caracteres)",
        max_length=20,
        widget=forms.PasswordInput(
            attrs={"maxlength": "20"}
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


class RecuperarSenhaForm(forms.Form):
    telefone = forms.CharField(
        label="Digite o seu número telefónico",
        max_length=30,
        widget=forms.TextInput(),
    )


class AlterarSenhaForm(forms.Form):
    senha_atual = forms.CharField(
        label="Senha atual",
        max_length=20,
        widget=forms.PasswordInput(attrs={"maxlength": "20"}),
    )
    nova_senha = forms.CharField(
        label="Nova senha",
        max_length=20,
        min_length=3,
        widget=forms.PasswordInput(attrs={"maxlength": "20"}),
        help_text="Entre 3 e 20 caracteres.",
    )
    confirmar_senha = forms.CharField(
        label="Confirme a nova senha",
        max_length=20,
        widget=forms.PasswordInput(attrs={"maxlength": "20"}),
    )

    def clean(self):
        dados = super().clean()
        nova = dados.get("nova_senha")
        confirmar = dados.get("confirmar_senha")
        if nova and confirmar and nova != confirmar:
            raise forms.ValidationError("As senhas novas não coincidem.")
        return dados
