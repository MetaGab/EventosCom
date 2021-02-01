from .models import *
from django import forms

class FuncionForm(forms.ModelForm):
    fecha = forms.DateTimeField(input_formats=['%Y/%m/%d %H:%M'], widget=forms.TextInput(attrs={'autocomplete':'off'}))
    class Meta:
        model = Funcion
        exclude = ('id', 'activo')