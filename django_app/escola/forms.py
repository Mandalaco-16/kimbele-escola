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
    pass


class EnvioSMSForm(forms.Form):
    numero_1 = forms.CharField(label="Número de telefone 1", max_length=20, required=True)
    numero_2 = forms.CharField(label="Número de telefone 2", max_length=20, required=False)
    numero_3 = forms.CharField(label="Número de telefone 3", max_length=20, required=False)
    numero_4 = forms.CharField(label="Número de telefone 4", max_length=20, required=False)
    numero_5 = forms.CharField(label="Número de telefone 5", max_length=20, required=False)
    corpo_mensagem = forms.CharField(label="Texto da mensagem", widget=forms.Textarea, max_length=459)

    def limpar_numeros(self):
        numeros = []
        for i in range(1, 6):
            valor = self.cleaned_data.get(f"numero_{i}")
            if valor:
                numeros.append(valor.strip())
        return numeros
