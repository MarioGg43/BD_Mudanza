from django import forms

from .permisos import CATALOGO


class RolForm(forms.Form):
    nombre = forms.CharField(max_length=100, label='Nombre del rol')
    descripcion = forms.CharField(max_length=100, required=False, label='Descripción')
    permisos = forms.MultipleChoiceField(required=False, label='Permisos',
                                         choices=[(c, c) for _, c, _ in CATALOGO],
                                         widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre in ('nombre', 'descripcion'):
            self.fields[nombre].widget.attrs['class'] = 'form-control'

    def grupos(self):
        """[(área, [(código, descripción, marcado)])] para dibujar las casillas agrupadas."""
        marcados = set(self['permisos'].value() or [])
        salida = []
        for area, codigo, descripcion in CATALOGO:
            if not salida or salida[-1][0] != area:
                salida.append((area, []))
            salida[-1][1].append((codigo, descripcion, codigo in marcados))
        return salida
