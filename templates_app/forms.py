from django import forms

def generate_template_form(fields):
    class TemplateForm(forms.Form):
        for field in fields:
            locals()[field] = forms.CharField(
                label=field,
                required=True,
                widget=forms.TextInput(attrs={
                    'class': 'form-control mb-2',
                    'style': 'max-width: 600px; width: 100%;'
                })
            )
    return TemplateForm