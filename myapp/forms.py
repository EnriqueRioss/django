from django import forms
from django.utils import timezone
from django.forms import ModelForm, Select, DateInput, ClearableFileInput, formset_factory
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import datetime



from .models import (
    HistoriasClinicas, Propositos, InformacionPadres, PeriodoNeonatal,
    AntecedentesFamiliaresPreconcepcionales, DesarrolloPsicomotor,
    AntecedentesPersonales, ExamenFisico, Parejas, EvaluacionGenetica, Genetistas
    # DiagnosticoPresuntivo, PlanEstudio are used for formsets but not direct form fields here
)

# --- General Purpose Forms ---

class CreateNewTask(forms.Form):
    title = forms.CharField(label="Title", max_length=200, strip=True)
    description = forms.CharField(label="Description", widget=forms.Textarea, strip=True)

class CreateNewProject(forms.Form):
    name = forms.CharField(label="Nombre Del Proyecto", max_length=200, strip=True)

class LoginForm(forms.Form):
    username = forms.CharField(
        label="Username",
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        strip=True
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        strip=True
    )

class ExtendedUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, help_text='Required.', strip=True)
    last_name = forms.CharField(max_length=30, required=True, help_text='Required.', strip=True)
    email = forms.EmailField(max_length=254, required=True, help_text='Required. Inform a valid email address.') # strip=True removed
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

# --- Clinical History Related Forms ---

class HistoriasForm(ModelForm):
    class Meta:
        model = HistoriasClinicas
        fields = ['numero_historia', 'motivo_tipo_consulta', 'cursante_postgrado', 'medico', 'especialidad', 'centro_referencia']
        widgets = {
            'motivo_tipo_consulta': Select(attrs={'onchange': 'toggleForms()'}),
            'cursante_postgrado': forms.TextInput(attrs={'placeholder': 'Opcional'}),
            'medico': forms.TextInput(attrs={'placeholder': 'Opcional'}),
            'especialidad': forms.TextInput(attrs={'placeholder': 'Opcional'}),
            'centro_referencia': forms.TextInput(attrs={'placeholder': 'Opcional'}),
        }
        labels = {
            'numero_historia': "Número de Historia Único",
            'motivo_tipo_consulta': "Motivo/Tipo de Consulta",
            'cursante_postgrado': "Cursante de Postgrado (Si aplica)",
            'medico': "Médico Referente",
            'especialidad': "Especialidad del Médico Referente",
            'centro_referencia': "Centro de Referencia (Si aplica)",
        }

    def clean_numero_historia(self):
        numero_historia = self.cleaned_data.get('numero_historia')
        if numero_historia is not None and numero_historia <= 0:
            raise forms.ValidationError("El número de historia debe ser un valor positivo.")
        # Model already enforces uniqueness for numero_historia
        return numero_historia

class PadresPropositoForm(forms.Form):
    # Datos del padre
    padre_nombres = forms.CharField(max_length=100, label="Nombres del Padre", strip=True)
    padre_apellidos = forms.CharField(max_length=100, label="Apellidos del Padre", strip=True)
    padre_escolaridad = forms.CharField(max_length=100, required=False, label="Escolaridad del Padre", strip=True)
    padre_ocupacion = forms.CharField(max_length=100, required=False, label="Ocupación del Padre", strip=True)
    padre_lugar_nacimiento = forms.CharField(max_length=100, required=False, label="Lugar de Nacimiento del Padre", strip=True)
    padre_fecha_nacimiento = forms.DateField(
        required=False,
        widget=DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Fecha de Nacimiento del Padre"
    )
    padre_edad = forms.IntegerField(required=False, label="Edad del Padre (años)", widget=forms.NumberInput(attrs={'min': '0', 'max': '120'}))
    padre_identificacion = forms.CharField(max_length=20, required=False, label="Identificación del Padre", strip=True)
    padre_grupo_sanguineo = forms.ChoiceField(
        choices=[('', 'Seleccione')] + InformacionPadres._meta.get_field('grupo_sanguineo').choices, # Keep existing choices, add empty
        required=False, label="Grupo Sanguíneo del Padre"
    )
    padre_factor_rh = forms.ChoiceField(
        choices=[('', 'Seleccione')] + InformacionPadres._meta.get_field('factor_rh').choices,
        required=False, label="Factor RH del Padre"
    )
    padre_telefono = forms.CharField(max_length=15, required=False, label="Teléfono del Padre", strip=True)
    padre_email = forms.EmailField(max_length=100, required=False, label="Email del Padre") # strip=True is default
    padre_direccion = forms.CharField(max_length=200, required=False, label="Dirección del Padre", strip=True)

    # Datos de la madre
    madre_nombres = forms.CharField(max_length=100, label="Nombres de la Madre", strip=True)
    madre_apellidos = forms.CharField(max_length=100, label="Apellidos de la Madre", strip=True)
    madre_escolaridad = forms.CharField(max_length=100, required=False, label="Escolaridad de la Madre", strip=True)
    madre_ocupacion = forms.CharField(max_length=100, required=False, label="Ocupación de la Madre", strip=True)
    madre_lugar_nacimiento = forms.CharField(max_length=100, required=False, label="Lugar de Nacimiento de la Madre", strip=True)
    madre_fecha_nacimiento = forms.DateField(
        required=False,
        widget=DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Fecha de Nacimiento de la Madre"
    )
    madre_edad = forms.IntegerField(required=False, label="Edad de la Madre (años)", widget=forms.NumberInput(attrs={'min': '0', 'max': '120'}))
    madre_identificacion = forms.CharField(max_length=20, required=False, label="Identificación de la Madre", strip=True)
    madre_grupo_sanguineo = forms.ChoiceField(
        choices=[('', 'Seleccione')] + InformacionPadres._meta.get_field('grupo_sanguineo').choices,
        required=False, label="Grupo Sanguíneo de la Madre"
    )
    madre_factor_rh = forms.ChoiceField(
        choices=[('', 'Seleccione')] + InformacionPadres._meta.get_field('factor_rh').choices,
        required=False, label="Factor RH de la Madre"
    )
    madre_telefono = forms.CharField(max_length=15, required=False, label="Teléfono de la Madre", strip=True)
    madre_email = forms.EmailField(max_length=100, required=False, label="Email de la Madre") # strip=True is default
    madre_direccion = forms.CharField(max_length=200, required=False, label="Dirección de la Madre", strip=True)

    def clean_padre_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('padre_fecha_nacimiento')
        if fecha and fecha > timezone.now().date():
            raise forms.ValidationError("La fecha de nacimiento no puede ser en el futuro.")
        return fecha

    def clean_madre_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('madre_fecha_nacimiento')
        if fecha and fecha > timezone.now().date():
            raise forms.ValidationError("La fecha de nacimiento no puede ser en el futuro.")
        return fecha

    def clean_padre_edad(self):
        edad = self.cleaned_data.get('padre_edad')
        if edad is not None and (edad < 0 or edad > 120): # Plausible age range
            raise forms.ValidationError("Por favor, ingrese una edad válida (0-120 años).")
        return edad

    def clean_madre_edad(self):
        edad = self.cleaned_data.get('madre_edad')
        if edad is not None and (edad < 0 or edad > 120): # Plausible age range
            raise forms.ValidationError("Por favor, ingrese una edad válida (0-120 años).")
        return edad

    def clean(self):
        cleaned_data = super().clean()
        padre_id = cleaned_data.get('padre_identificacion', '').strip() # Ensure strip if it's optional
        madre_id = cleaned_data.get('madre_identificacion', '').strip()

        if padre_id and madre_id and padre_id == madre_id:
            self.add_error('madre_identificacion', "La identificación de la madre no puede ser igual a la del padre.")
        return cleaned_data

class PropositosForm(forms.Form):
    nombres = forms.CharField(max_length=100, label="Nombres", strip=True)
    apellidos = forms.CharField(max_length=100, label="Apellidos", strip=True)
    lugar_nacimiento = forms.CharField(max_length=100, required=False, label="Lugar de Nacimiento", strip=True)
    escolaridad = forms.CharField(max_length=100, required=False, label="Escolaridad", strip=True)
    ocupacion = forms.CharField(max_length=100, required=False, label="Ocupación", strip=True)
    edad = forms.IntegerField(required=False, label="Edad (años)", widget=forms.NumberInput(attrs={'min': '0', 'max': '120'}))
    fecha_nacimiento = forms.DateField(
        required=False,
        widget=DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Fecha de Nacimiento"
    )
    identificacion = forms.CharField(max_length=20, label="Identificación (Cédula/Pasaporte)", strip=True)
    # documento_nacimiento = forms.FileField(required=False, label="Documento de Nacimiento (Opcional)")
    direccion = forms.CharField(max_length=200, required=False, label="Dirección", strip=True)
    telefono = forms.CharField(max_length=15, required=False, label="Teléfono", strip=True)
    email = forms.EmailField(max_length=100, required=False, label="Email")
    grupo_sanguineo = forms.ChoiceField(
        choices=[('', 'Seleccione')] + Propositos._meta.get_field('grupo_sanguineo').choices, # Using model choices
        required=False, label="Grupo Sanguíneo"
    )
    factor_rh = forms.ChoiceField(
        choices=[('', 'Seleccione')] + Propositos._meta.get_field('factor_rh').choices, # Using model choices
        required=False, label="Factor RH"
    )
    foto = forms.ImageField(
        required=False,
        widget=ClearableFileInput(attrs={'accept': 'image/*'}),
        label='Foto del Propósito (Opcional)'
    )

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None) # Get instance if passed (for editing)
        super().__init__(*args, **kwargs)
        if self.instance: # Pre-fill form if instance is provided
            for field_name in self.fields:
                if hasattr(self.instance, field_name):
                    self.fields[field_name].initial = getattr(self.instance, field_name)
            if self.instance.foto: # Special handling for ImageField/FileField
                 self.fields['foto'].initial = self.instance.foto


    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_nacimiento')
        if fecha and fecha > timezone.now().date():
            raise forms.ValidationError("La fecha de nacimiento no puede ser en el futuro.")
        return fecha

    def clean_edad(self):
        edad = self.cleaned_data.get('edad')
        if edad is not None and (edad < 0 or edad > 120):
            raise forms.ValidationError("Por favor, ingrese una edad válida (0-120 años).")
        return edad

    def clean_identificacion(self):
        identificacion = self.cleaned_data.get('identificacion')
        if not identificacion: # Ensure identification is provided
            raise forms.ValidationError("La identificación es obligatoria.")

        # Check for uniqueness, excluding self if editing
        query = Propositos.objects.filter(identificacion=identificacion)
        if self.instance and self.instance.pk: # If we are editing an existing instance
            query = query.exclude(pk=self.instance.pk)
        if query.exists():
            raise forms.ValidationError("Ya existe un propósito con esta identificación.")
        return identificacion

    def save(self, historia): # This is a custom save method for forms.Form
        cleaned_data = self.cleaned_data
        identificacion = cleaned_data['identificacion']

        # Prepare defaults for update_or_create
        proposito_defaults = {
            'historia': historia, # Always associate with the given historia
            'nombres': cleaned_data['nombres'],
            'apellidos': cleaned_data['apellidos'],
            'lugar_nacimiento': cleaned_data.get('lugar_nacimiento'),
            'fecha_nacimiento': cleaned_data.get('fecha_nacimiento'),
            'escolaridad': cleaned_data.get('escolaridad'),
            'ocupacion': cleaned_data.get('ocupacion'),
            'edad': cleaned_data.get('edad'),
            'direccion': cleaned_data.get('direccion'),
            'telefono': cleaned_data.get('telefono'),
            'email': cleaned_data.get('email'),
            'grupo_sanguineo': cleaned_data.get('grupo_sanguineo') or None, # Ensure empty string becomes None
            'factor_rh': cleaned_data.get('factor_rh') or None,
            # Foto is handled separately due to ClearableFileInput behavior
        }
        # Filter out None values from defaults unless it's a required field that somehow became None
        # or specifically allowed Nones (like historia can be None initially if not passed but set here)
        proposito_defaults = {k: v for k, v in proposito_defaults.items() if v is not None or k == 'historia'}


        proposito, created = Propositos.objects.update_or_create(
            identificacion=identificacion, # Unique key for lookup
            defaults=proposito_defaults
        )

        # Handle foto separately because ClearableFileInput has special behavior
        # cleaned_data['foto'] will be:
        # - The UploadedFile object if a new file is uploaded.
        # - None if the field was not changed and no file was previously present or if it was cleared and not re-uploaded.
        # - False if the "Clear" checkbox was checked.
        foto_val = cleaned_data.get('foto')
        if foto_val is not None: # Check if field was submitted (i.e., not absent from POST data)
            if foto_val: # A new file was uploaded
                proposito.foto = foto_val
            elif foto_val is False: # ClearableFileInput: False means clear the existing file
                proposito.foto = None
            # If foto_val is None here, it means no new file and clear was not checked.
            # We only save if there was a change (new file or clear).
            proposito.save(update_fields=['foto']) # Save only foto field to avoid overwriting other fields
        elif created and proposito.foto is not None: # If created and no photo submitted, but instance somehow had one
            proposito.foto = None
            proposito.save(update_fields=['foto'])


        return proposito

class ParejaPropositosForm(forms.Form):
    # Campos para el primer cónyuge (proposito 1)
    nombres_1 = forms.CharField(max_length=100, label="Nombres (Primer Cónyuge)", strip=True)
    apellidos_1 = forms.CharField(max_length=100, label="Apellidos (Primer Cónyuge)", strip=True)
    lugar_nacimiento_1 = forms.CharField(max_length=100, required=False, label="Lugar de Nacimiento", strip=True)
    fecha_nacimiento_1 = forms.DateField(required=False, widget=DateInput(attrs={'type': 'date', 'class': 'form-control'}), label="Fecha de Nacimiento")
    escolaridad_1 = forms.CharField(max_length=100, required=False, label="Escolaridad", strip=True)
    ocupacion_1 = forms.CharField(max_length=100, required=False, label="Ocupación", strip=True)
    edad_1 = forms.IntegerField(required=False, label="Edad (años)", widget=forms.NumberInput(attrs={'min':'0', 'max':'120'}))
    identificacion_1 = forms.CharField(max_length=20, label="Identificación", strip=True)
    direccion_1 = forms.CharField(max_length=200, required=False, label="Dirección", strip=True)
    telefono_1 = forms.CharField(max_length=15, required=False, label="Teléfono", strip=True)
    email_1 = forms.EmailField(max_length=100, required=False, label="Email")
    grupo_sanguineo_1 = forms.ChoiceField(choices=[('', 'Seleccione')] + Propositos._meta.get_field('grupo_sanguineo').choices, required=False, label="Grupo Sanguíneo")
    factor_rh_1 = forms.ChoiceField(choices=[('', 'Seleccione')] + Propositos._meta.get_field('factor_rh').choices, required=False, label="Factor RH")
    foto_1 = forms.ImageField(required=False, widget=ClearableFileInput(attrs={'accept': 'image/*'}), label="Foto (Opcional)")

    # Campos para el segundo cónyuge (proposito 2)
    nombres_2 = forms.CharField(max_length=100, label="Nombres (Segundo Cónyuge)", strip=True)
    apellidos_2 = forms.CharField(max_length=100, label="Apellidos (Segundo Cónyuge)", strip=True)
    lugar_nacimiento_2 = forms.CharField(max_length=100, required=False, label="Lugar de Nacimiento", strip=True)
    fecha_nacimiento_2 = forms.DateField(required=False, widget=DateInput(attrs={'type': 'date', 'class': 'form-control'}), label="Fecha de Nacimiento")
    escolaridad_2 = forms.CharField(max_length=100, required=False, label="Escolaridad", strip=True)
    ocupacion_2 = forms.CharField(max_length=100, required=False, label="Ocupación", strip=True)
    edad_2 = forms.IntegerField(required=False, label="Edad (años)", widget=forms.NumberInput(attrs={'min':'0', 'max':'120'}))
    identificacion_2 = forms.CharField(max_length=20, label="Identificación", strip=True)
    direccion_2 = forms.CharField(max_length=200, required=False, label="Dirección", strip=True)
    telefono_2 = forms.CharField(max_length=15, required=False, label="Teléfono", strip=True)
    email_2 = forms.EmailField(max_length=100, required=False, label="Email")
    grupo_sanguineo_2 = forms.ChoiceField(choices=[('', 'Seleccione')] + Propositos._meta.get_field('grupo_sanguineo').choices, required=False, label="Grupo Sanguíneo")
    factor_rh_2 = forms.ChoiceField(choices=[('', 'Seleccione')] + Propositos._meta.get_field('factor_rh').choices, required=False, label="Factor RH")
    foto_2 = forms.ImageField(required=False, widget=ClearableFileInput(attrs={'accept': 'image/*'}), label="Foto (Opcional)")

    def clean_fecha_nacimiento_1(self):
        fecha = self.cleaned_data.get('fecha_nacimiento_1')
        if fecha and fecha > timezone.now().date():
            raise forms.ValidationError("La fecha de nacimiento no puede ser en el futuro.")
        return fecha

    def clean_fecha_nacimiento_2(self):
        fecha = self.cleaned_data.get('fecha_nacimiento_2')
        if fecha and fecha > timezone.now().date():
            raise forms.ValidationError("La fecha de nacimiento no puede ser en el futuro.")
        return fecha

    def clean_edad_1(self):
        edad = self.cleaned_data.get('edad_1')
        if edad is not None and (edad < 0 or edad > 120):
            raise forms.ValidationError("Por favor, ingrese una edad válida (0-120 años).")
        return edad

    def clean_edad_2(self):
        edad = self.cleaned_data.get('edad_2')
        if edad is not None and (edad < 0 or edad > 120):
            raise forms.ValidationError("Por favor, ingrese una edad válida (0-120 años).")
        return edad

    def clean_identificacion_1(self):
        ident = self.cleaned_data.get('identificacion_1')
        if not ident:
            raise forms.ValidationError("La identificación del primer cónyuge es obligatoria.")
        # Uniqueness check (if these propositos might exist independently)
        # if Propositos.objects.filter(identificacion=ident).exists():
        #     pass # Decide if this is an error or if we link to existing
        return ident

    def clean_identificacion_2(self):
        ident = self.cleaned_data.get('identificacion_2')
        if not ident:
            raise forms.ValidationError("La identificación del segundo cónyuge es obligatoria.")
        # if Propositos.objects.filter(identificacion=ident).exists():
        #     pass
        return ident

    def clean(self):
        cleaned_data = super().clean()
        id_1 = cleaned_data.get('identificacion_1')
        id_2 = cleaned_data.get('identificacion_2')

        if id_1 and id_2 and id_1 == id_2:
            self.add_error('identificacion_2', "Las identificaciones de los cónyuges deben ser diferentes.")
        return cleaned_data

class AntecedentesDesarrolloNeonatalForm(forms.Form):
    # Campos de AntecedentesPersonales
    fur = forms.DateField(required=False, widget=DateInput(attrs={'type': 'date', 'class':'form-control'}), label="Fecha de Última Regla (FUR)")
    edad_gestacional = forms.IntegerField(required=False, label="Edad Gestacional (semanas)", widget=forms.NumberInput(attrs={'min':'0'})) # 0 is unlikely but for min range
    controles_prenatales = forms.CharField(max_length=100, required=False, label="Controles Prenatales", strip=True)
    numero_partos = forms.IntegerField(required=False, label="Número de Partos", widget=forms.NumberInput(attrs={'min':'0'}))
    numero_gestas = forms.IntegerField(required=False, label="Número de Gestas", widget=forms.NumberInput(attrs={'min':'0'}))
    numero_cesareas = forms.IntegerField(required=False, label="Número de Cesáreas", widget=forms.NumberInput(attrs={'min':'0'}))
    numero_abortos = forms.IntegerField(required=False, label="Número de Abortos", widget=forms.NumberInput(attrs={'min':'0'}))
    numero_mortinatos = forms.IntegerField(required=False, label="Número de Mortinatos", widget=forms.NumberInput(attrs={'min':'0'}))
    numero_malformaciones = forms.IntegerField(required=False, label="Número de Hijos con Malformaciones", widget=forms.NumberInput(attrs={'min':'0'}))
    complicaciones_embarazo = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}), label="Complicaciones en Embarazo(s)", strip=True)
    exposicion_teratogenos = forms.ChoiceField(
        choices=[('', '---------')] + AntecedentesPersonales._meta.get_field('exposicion_teratogenos').choices,
        required=False, label="Exposición a Teratógenos"
    )
    descripcion_exposicion = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}), label="Descripción de Exposición", strip=True)
    enfermedades_maternas = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}), label="Enfermedades Maternas", strip=True)
    complicaciones_parto = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}), label="Complicaciones en Parto(s)", strip=True)
    otros_antecedentes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}), label="Otros Antecedentes Personales", strip=True)
    observaciones = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}), label="Observaciones Generales (Personales)", strip=True)

    # Campos de DesarrolloPsicomotor
    sostener_cabeza = forms.CharField(max_length=100, required=False, label="Sostén Cefálico (edad)", strip=True)
    sonrisa_social = forms.CharField(max_length=100, required=False, label="Sonrisa Social (edad)", strip=True)
    sentarse = forms.CharField(max_length=100, required=False, label="Sedestación (edad)", strip=True)
    gatear = forms.CharField(max_length=100, required=False, label="Gateo (edad)", strip=True)
    pararse = forms.CharField(max_length=100, required=False, label="Bipedestación (edad)", strip=True)
    caminar = forms.CharField(max_length=100, required=False, label="Marcha (edad)", strip=True)
    primeras_palabras = forms.CharField(max_length=100, required=False, label="Primeras Palabras (edad)", strip=True)
    primeros_dientes = forms.CharField(max_length=100, required=False, label="Primeros Dientes (edad)", strip=True)
    progreso_escuela = forms.CharField(max_length=100, required=False, label="Progreso Escolar", strip=True) # Widget change in template to Textarea if needed
    progreso_peso = forms.CharField(max_length=100, required=False, label="Progreso Ponderal (Peso)", strip=True)
    progreso_talla = forms.CharField(max_length=100, required=False, label="Progreso Estatural (Talla)", strip=True)

    # Campos de PeriodoNeonatal
    peso_nacer = forms.DecimalField(required=False, max_digits=5, decimal_places=2, label="Peso al Nacer (kg)", widget=forms.NumberInput(attrs={'step': '0.01', 'min':'0'}))
    talla_nacer = forms.DecimalField(required=False, max_digits=5, decimal_places=2, label="Talla al Nacer (cm)", widget=forms.NumberInput(attrs={'step': '0.01', 'min':'0'}))
    circunferencia_cefalica = forms.DecimalField(required=False, max_digits=5, decimal_places=2, label="Circunferencia Cefálica (cm)", widget=forms.NumberInput(attrs={'step': '0.01', 'min':'0'}))
    cianosis = forms.CharField(max_length=100, required=False, label="Cianosis Neonatal", strip=True)
    ictericia = forms.CharField(max_length=100, required=False, label="Ictericia Neonatal", strip=True)
    hemorragia = forms.CharField(max_length=100, required=False, label="Hemorragia Neonatal", strip=True)
    infecciones = forms.CharField(max_length=100, required=False, label="Infecciones Neonatales", strip=True)
    convulsiones = forms.CharField(max_length=100, required=False, label="Convulsiones Neonatales", strip=True)
    vomitos = forms.CharField(max_length=100, required=False, label="Vómitos Neonatales", strip=True)
    observacion_complicaciones = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}), label="Observaciones (Complicaciones Neonatales)", strip=True)
    otros_complicaciones = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}), label="Otras Complicaciones Neonatales", strip=True)
    tipo_alimentacion = forms.ChoiceField(
        choices=[('', '---------')] + PeriodoNeonatal._meta.get_field('tipo_alimentacion').choices,
        required=False, label="Tipo de Alimentación Inicial"
    )
    observaciones_alimentacion = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}), label="Observaciones (Alimentación)", strip=True)
    evolucion = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}), label="Evolución General Neonatal", strip=True)
    observaciones_habitos_psicologicos = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}), label="Observaciones (Hábitos Psicobiológicos)", strip=True)

    def clean_fur(self):
        fecha = self.cleaned_data.get('fur')
        if fecha and fecha > timezone.now().date():
            raise forms.ValidationError("La FUR no puede ser una fecha futura.")
        return fecha

    def clean_edad_gestacional(self):
        edad_g = self.cleaned_data.get('edad_gestacional')
        if edad_g is not None and (edad_g < 18 or edad_g > 45): # Plausible range
            raise forms.ValidationError("Ingrese una edad gestacional válida (ej: 18-45 semanas).")
        return edad_g

    def _clean_non_negative_integer(self, field_name):
        value = self.cleaned_data.get(field_name)
        if value is not None and value < 0:
            self.add_error(field_name, "Este valor no puede ser negativo.") # Use add_error for field-specific
        return value

    def clean_numero_partos(self): return self._clean_non_negative_integer('numero_partos')
    def clean_numero_gestas(self): return self._clean_non_negative_integer('numero_gestas')
    def clean_numero_cesareas(self): return self._clean_non_negative_integer('numero_cesareas')
    def clean_numero_abortos(self): return self._clean_non_negative_integer('numero_abortos')
    def clean_numero_mortinatos(self): return self._clean_non_negative_integer('numero_mortinatos')
    def clean_numero_malformaciones(self): return self._clean_non_negative_integer('numero_malformaciones')

    def clean_peso_nacer(self):
        peso = self.cleaned_data.get('peso_nacer')
        if peso is not None and (peso <= 0 or peso > 10): # Plausible range in kg
             raise forms.ValidationError("Ingrese un peso válido (ej: 0.1 - 10 kg).")
        return peso

    def clean_talla_nacer(self):
        talla = self.cleaned_data.get('talla_nacer')
        if talla is not None and (talla <= 20 or talla > 70): # Plausible range in cm
             raise forms.ValidationError("Ingrese una talla válida (ej: 20 - 70 cm).")
        return talla

    def clean_circunferencia_cefalica(self):
        cc = self.cleaned_data.get('circunferencia_cefalica')
        if cc is not None and (cc <= 15 or cc > 50): # Plausible range in cm
             raise forms.ValidationError("Ingrese una circunferencia cefálica válida (ej: 15 - 50 cm).")
        return cc

    def clean(self):
        cleaned_data = super().clean()
        exposicion = cleaned_data.get('exposicion_teratogenos')
        descripcion_exp = cleaned_data.get('descripcion_exposicion')
        if exposicion and not descripcion_exp:
            self.add_error('descripcion_exposicion', "Debe describir la exposición si seleccionó un tipo.")

        # Validate that #cesareas <= #partos <= #gestas
        num_gestas = cleaned_data.get('numero_gestas')
        num_partos = cleaned_data.get('numero_partos')
        num_cesareas = cleaned_data.get('numero_cesareas')

        if num_partos is not None and num_gestas is not None and num_partos > num_gestas:
            self.add_error('numero_partos', "El número de partos no puede exceder el número de gestas.")
        if num_cesareas is not None and num_partos is not None and num_cesareas > num_partos:
            self.add_error('numero_cesareas', "El número de cesáreas no puede exceder el número de partos.")

        return cleaned_data

    def save(self, proposito=None, pareja=None): # Custom save, handles update_or_create
        if not proposito and not pareja:
            raise ValueError("Debe proporcionar un propósito o una pareja para guardar los antecedentes.")
        if proposito and pareja:
            raise ValueError("No puede proporcionar tanto un propósito como una pareja simultáneamente.")

        # Antecedentes Personales
        ap_defaults = {
            'fur': self.cleaned_data.get('fur'),
            'edad_gestacional': self.cleaned_data.get('edad_gestacional'),
            'controles_prenatales': self.cleaned_data.get('controles_prenatales', ''), # Default to empty string
            'numero_partos': self.cleaned_data.get('numero_partos'),
            'numero_gestas': self.cleaned_data.get('numero_gestas'),
            'numero_cesareas': self.cleaned_data.get('numero_cesareas'),
            'numero_abortos': self.cleaned_data.get('numero_abortos'),
            'numero_mortinatos': self.cleaned_data.get('numero_mortinatos'),
            'numero_malformaciones': self.cleaned_data.get('numero_malformaciones'),
            'complicaciones_embarazo': self.cleaned_data.get('complicaciones_embarazo'),
            'exposicion_teratogenos': self.cleaned_data.get('exposicion_teratogenos') or None, # Ensure empty becomes None
            'descripcion_exposicion': self.cleaned_data.get('descripcion_exposicion'),
            'enfermedades_maternas': self.cleaned_data.get('enfermedades_maternas'),
            'complicaciones_parto': self.cleaned_data.get('complicaciones_parto'),
            'otros_antecedentes': self.cleaned_data.get('otros_antecedentes'),
            'observaciones': self.cleaned_data.get('observaciones')
        }
        ap_defaults = {k:v for k,v in ap_defaults.items() if v is not None or k=='controles_prenatales'} # Keep empty string for controles


        if proposito:
            antecedentes, _ = AntecedentesPersonales.objects.update_or_create(
                proposito=proposito, defaults=ap_defaults
            )
        else: # pareja
            antecedentes, _ = AntecedentesPersonales.objects.update_or_create(
                pareja=pareja, defaults=ap_defaults
            )

        # Desarrollo Psicomotor
        dp_defaults = {
            'sostener_cabeza': self.cleaned_data.get('sostener_cabeza'),
            'sonrisa_social': self.cleaned_data.get('sonrisa_social'),
            'sentarse': self.cleaned_data.get('sentarse'),
            'gatear': self.cleaned_data.get('gatear'),
            'pararse': self.cleaned_data.get('pararse'),
            'caminar': self.cleaned_data.get('caminar'),
            'primeras_palabras': self.cleaned_data.get('primeras_palabras'),
            'primeros_dientes': self.cleaned_data.get('primeros_dientes'),
            'progreso_escuela': self.cleaned_data.get('progreso_escuela'),
            'progreso_peso': self.cleaned_data.get('progreso_peso'),
            'progreso_talla': self.cleaned_data.get('progreso_talla')
        }
        dp_defaults = {k:v for k,v in dp_defaults.items() if v is not None}


        if proposito:
            desarrollo, _ = DesarrolloPsicomotor.objects.update_or_create(
                proposito=proposito, defaults=dp_defaults
            )
        else: # pareja
            desarrollo, _ = DesarrolloPsicomotor.objects.update_or_create(
                pareja=pareja, defaults=dp_defaults
            )

        # Periodo Neonatal
        pn_defaults = {
            'peso_nacer': self.cleaned_data.get('peso_nacer'),
            'talla_nacer': self.cleaned_data.get('talla_nacer'),
            'circunferencia_cefalica': self.cleaned_data.get('circunferencia_cefalica'),
            'cianosis': self.cleaned_data.get('cianosis'),
            'ictericia': self.cleaned_data.get('ictericia'),
            'hemorragia': self.cleaned_data.get('hemorragia'),
            'infecciones': self.cleaned_data.get('infecciones'),
            'convulsiones': self.cleaned_data.get('convulsiones'),
            'vomitos': self.cleaned_data.get('vomitos'),
            'observacion_complicaciones': self.cleaned_data.get('observacion_complicaciones'),
            'otros_complicaciones': self.cleaned_data.get('otros_complicaciones'),
            'tipo_alimentacion': self.cleaned_data.get('tipo_alimentacion') or None, # Ensure empty becomes None
            'observaciones_alimentacion': self.cleaned_data.get('observaciones_alimentacion'),
            'evolucion': self.cleaned_data.get('evolucion'),
            'observaciones_habitos_psicologicos': self.cleaned_data.get('observaciones_habitos_psicologicos')
        }
        pn_defaults = {k:v for k,v in pn_defaults.items() if v is not None}


        if proposito:
            neonatal, _ = PeriodoNeonatal.objects.update_or_create(
                proposito=proposito, defaults=pn_defaults
            )
        else: # pareja
            neonatal, _ = PeriodoNeonatal.objects.update_or_create(
                pareja=pareja, defaults=pn_defaults
            )
        return antecedentes, desarrollo, neonatal

class AntecedentesPreconcepcionalesForm(forms.Form):
    antecedentes_padre = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}), label="Antecedentes Familiares Paternos Relevantes", strip=True)
    antecedentes_madre = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}), label="Antecedentes Familiares Maternos Relevantes", strip=True)
    estado_salud_padre = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}), label="Estado de Salud Actual del Padre", strip=True)
    estado_salud_madre = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}), label="Estado de Salud Actual de la Madre", strip=True)
    fecha_union_pareja = forms.DateField(required=False, widget=DateInput(attrs={'type': 'date', 'class':'form-control'}), label="Fecha de Unión de la Pareja (si aplica)")
    consanguinidad = forms.ChoiceField(
        choices=[('', '---------'), ('Sí', 'Sí'), ('No', 'No')], # Model choices are ('Sí', 'Sí'), ('No', 'No')
        required=False, label="Consanguinidad entre los padres"
    )
    grado_consanguinidad = forms.CharField(max_length=50, required=False, label="Grado de Consanguinidad (si aplica)", strip=True)

    def clean_fecha_union_pareja(self):
        fecha = self.cleaned_data.get('fecha_union_pareja')
        if fecha and fecha > timezone.now().date():
            raise forms.ValidationError("La fecha de unión no puede ser en el futuro.")
        return fecha

    def clean(self):
        cleaned_data = super().clean()
        consanguinidad_val = cleaned_data.get('consanguinidad')
        grado_consanguinidad_val = cleaned_data.get('grado_consanguinidad')

        if consanguinidad_val == 'Sí' and not grado_consanguinidad_val:
            self.add_error('grado_consanguinidad', "Debe especificar el grado si existe consanguinidad.")
        elif consanguinidad_val == 'No' and grado_consanguinidad_val:
            # self.add_error('grado_consanguinidad', "No debe especificar grado si no hay consanguinidad.")
            # Instead of error, clear it if 'No' is selected and a grade was entered by mistake
            cleaned_data['grado_consanguinidad'] = ''
        return cleaned_data

    def save(self, proposito=None, pareja=None, tipo=None): # Custom save, handles update_or_create
        if tipo not in ['proposito', 'pareja']:
            raise ValueError("Tipo debe ser 'proposito' o 'pareja'")

        if tipo == 'proposito' and not proposito:
            raise ValueError("Debe proporcionar un propósito para el tipo 'proposito'")
        if tipo == 'pareja' and not pareja:
            raise ValueError("Debe proporcionar una pareja para el tipo 'pareja'")

        afp_defaults = {
            'antecedentes_padre': self.cleaned_data.get('antecedentes_padre'),
            'antecedentes_madre': self.cleaned_data.get('antecedentes_madre'),
            'estado_salud_padre': self.cleaned_data.get('estado_salud_padre'),
            'estado_salud_madre': self.cleaned_data.get('estado_salud_madre'),
            'fecha_union_pareja': self.cleaned_data.get('fecha_union_pareja'),
            'consanguinidad': self.cleaned_data.get('consanguinidad') or None, # Ensure empty string becomes None
            'grado_consanguinidad': self.cleaned_data.get('grado_consanguinidad')
        }
        # Ensure grado_consanguinidad is empty if consanguinidad is not 'Sí'
        if afp_defaults['consanguinidad'] != 'Sí':
            afp_defaults['grado_consanguinidad'] = ''

        # Filter out None values, except for grado_consanguinidad if consanguinidad is 'Sí' (it might be an empty string then)
        afp_defaults_clean = {k:v for k,v in afp_defaults.items() if v is not None or (k == 'grado_consanguinidad' and afp_defaults['consanguinidad'] == 'Sí')}


        if tipo == 'proposito':
            antecedentespre, _ = AntecedentesFamiliaresPreconcepcionales.objects.update_or_create(
                proposito=proposito, defaults=afp_defaults_clean
            )
        else: # pareja
            antecedentespre, _ = AntecedentesFamiliaresPreconcepcionales.objects.update_or_create(
                pareja=pareja, defaults=afp_defaults_clean
            )
        return antecedentespre

class ExamenFisicoForm(ModelForm):
    class Meta:
        model = ExamenFisico
        fields = '__all__'
        exclude = ['fecha_examen', 'proposito'] # fecha_examen is auto_now_add, proposito set in view
        widgets = {
            # Numeric fields with step for decimal input
            'medida_abrazada': forms.NumberInput(attrs={'step': '0.01'}),
            'segmento_inferior': forms.NumberInput(attrs={'step': '0.01'}),
            'segmento_superior': forms.NumberInput(attrs={'step': '0.01'}),
            'circunferencia_cefalica': forms.NumberInput(attrs={'step': '0.01'}),
            'talla': forms.NumberInput(attrs={'step': '0.01'}),
            'distancia_intermamilar': forms.NumberInput(attrs={'step': '0.01'}),
            'distancia_interc_interna': forms.NumberInput(attrs={'step': '0.01'}),
            'distancia_interpupilar': forms.NumberInput(attrs={'step': '0.01'}),
            'longitud_mano_derecha': forms.NumberInput(attrs={'step': '0.01'}),
            'longitud_mano_izquierda': forms.NumberInput(attrs={'step': '0.01'}),
            'peso': forms.NumberInput(attrs={'step': '0.01'}),
            'ss_si': forms.NumberInput(attrs={'step': '0.01'}), # Relación SS/SI
            'distancia_interc_externa': forms.NumberInput(attrs={'step': '0.01'}),
            'ct': forms.NumberInput(attrs={'step': '0.01'}), # Circunferencia Torácica
            'pabellones_auriculares': forms.NumberInput(attrs={'step': '0.01'}),
            'tension_arterial_sistolica': forms.NumberInput(attrs={'step': '1'}), # Usually integer
            'tension_arterial_diastolica': forms.NumberInput(attrs={'step': '1'}), # Usually integer
            # Textarea fields for observations
            'observaciones_cabeza': forms.Textarea(attrs={'rows': 1}),
            'observaciones_cuello': forms.Textarea(attrs={'rows': 1}),
            'observaciones_torax': forms.Textarea(attrs={'rows': 1}),
            'observaciones_abdomen': forms.Textarea(attrs={'rows': 1}),
            'observaciones_genitales': forms.Textarea(attrs={'rows': 1}),
            'observaciones_espalda': forms.Textarea(attrs={'rows': 1}),
            'observaciones_miembros_superiores': forms.Textarea(attrs={'rows': 1}),
            'observaciones_miembros_inferiores': forms.Textarea(attrs={'rows': 1}),
            'observaciones_piel': forms.Textarea(attrs={'rows': 1}),
            'observaciones_osteomioarticular': forms.Textarea(attrs={'rows': 1}),
            'observaciones_neurologico': forms.Textarea(attrs={'rows': 1}),
            'observaciones_pliegues': forms.Textarea(attrs={'rows': 1}),
        }

    def _clean_positive_decimal(self, field_name, max_val=None, min_val=0): # Allow min_val to be passed
        value = self.cleaned_data.get(field_name)
        if value is not None:
            if value < min_val:
                raise forms.ValidationError(f"Este valor debe ser mayor o igual a {min_val}.")
            if max_val and value > max_val:
                raise forms.ValidationError(f"Este valor no debe exceder {max_val}.")
        return value

    def clean_medida_abrazada(self): return self._clean_positive_decimal('medida_abrazada', 300) # Max 3m
    def clean_segmento_inferior(self): return self._clean_positive_decimal('segmento_inferior', 200)
    def clean_segmento_superior(self): return self._clean_positive_decimal('segmento_superior', 200)
    def clean_circunferencia_cefalica(self): return self._clean_positive_decimal('circunferencia_cefalica', 100)
    def clean_talla(self): return self._clean_positive_decimal('talla', 300) # Max 3m
    def clean_peso(self): return self._clean_positive_decimal('peso', 500, min_val=0.1) # Peso should be > 0
    def clean_tension_arterial_sistolica(self): return self._clean_positive_decimal('tension_arterial_sistolica', 300, min_val=10)
    def clean_tension_arterial_diastolica(self): return self._clean_positive_decimal('tension_arterial_diastolica', 200, min_val=10)

    def save(self, commit=True):
        # This instance is assigned a 'proposito_instance' attribute in the view before save is called.
        examenfisico = super().save(commit=False)

        if hasattr(self, 'proposito_instance') and self.proposito_instance: # Ensure attribute name is consistent
            examenfisico.proposito = self.proposito_instance
        elif not examenfisico.proposito_id and not self.instance: # If creating new and no proposito_instance set
             raise ValueError("El propósito debe estar asignado para guardar el Examen Físico.")

        # fecha_examen is auto_now_add, so Django handles it on first save.
        # If you want to *always* update it on every save (less common for auto_now_add):
        # examenfisico.fecha_examen = timezone.now().date()

        if commit:
            examenfisico.save()
            # self.save_m2m() # Important for ModelForms with M2M fields, though not present here.

        return examenfisico

class SignosClinicosForm(ModelForm):
    class Meta:
        model = EvaluacionGenetica
        fields = ['signos_clinicos']
        widgets = {
            'signos_clinicos': forms.Textarea(attrs={
                'rows': 3, # Increased for more space
                'class': 'form-control',
                'placeholder': 'Ej: Microcefalia, hipotonía, fisura palpebral, cardiopatía congénita...'
            })
        }
        labels = {
            'signos_clinicos': "Signos Clínicos Relevantes"
        }

class DiagnosticoPresuntivoForm(forms.Form):
    # id = forms.IntegerField(widget=forms.HiddenInput(), required=False) # Uncomment if needed for specific update logic
    descripcion = forms.CharField(
        label="Diagnóstico Presuntivo",
        widget=forms.Textarea(attrs={
            'rows': 1,
            'class': 'form-control diagnostico-descripcion',
            'placeholder': 'Ej: Síndrome de Down, Acondroplasia'
        }),
        strip=True
    )
    orden = forms.IntegerField(
        label="Prioridad",
        widget=forms.NumberInput(attrs={
            'class': 'form-control diagnostico-orden',
            'min': '0',
        }),
        required=False, # Default to 0 if not provided
        initial=0
    )

    def clean_descripcion(self):
        descripcion = self.cleaned_data.get('descripcion')
        # If the form is part of a formset and not marked for deletion, and it's not an "empty" extra form,
        # then description should be required. This is usually handled in the view by checking form.has_changed().
        # For simplicity here, if 'orden' is provided or the form has some data, then description is needed.
        if self.has_changed() and not descripcion: # self.has_changed() checks if data is different from initial
             pass # This might be too aggressive for empty extra forms. View logic is better.
        return descripcion


    def clean_orden(self):
        orden = self.cleaned_data.get('orden')
        if orden is not None and orden < 0:
            raise forms.ValidationError("La prioridad no puede ser negativa.")
        return orden if orden is not None else 0 # Ensure a value

DiagnosticoPresuntivoFormSet = formset_factory(
    DiagnosticoPresuntivoForm,
    extra=0, # Show one empty form by default
    can_delete=True,
)

class PlanEstudioForm(forms.Form):
    # id = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    accion = forms.CharField(
        label="Acción/Estudio a Realizar",
        widget=forms.TextInput(attrs={
            'class': 'form-control plan-accion',
            'placeholder': 'Ej: Cariotipo en sangre periférica, Ecocardiograma, Array CGH'
        }),
        strip=True
    )
    fecha_limite = forms.DateField(
        label="Fecha Límite (Opcional)",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control plan-fecha_limite'
        }),
        required=False
    )
    completado = forms.BooleanField(
        label="Completado",
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input plan-completado'
        })
    )

    def clean_accion(self):
        accion = self.cleaned_data.get('accion')
        # Similar to DiagnosticoPresuntivoForm's descripcion, view logic for formsets is more robust.
        if self.has_changed() and not accion:
            pass
        return accion

    def clean_fecha_limite(self):
        fecha = self.cleaned_data.get('fecha_limite')
        # This check needs 'completado' from cleaned_data, which might not be available if 'fecha_limite' is cleaned first.
        # It's better to do this kind of cross-field validation in the main clean() method or view.
        # For now, a simpler check:
        # if fecha and fecha < timezone.now().date():
        #     is_completado = self.data.get(self.prefix + '-completado', False) # Access raw data for 'completado'
        #     if not is_completado: # Check if checkbox was ticked
        #        raise forms.ValidationError("La fecha límite no puede ser en el pasado para un plan no completado.")
        return fecha

PlanEstudioFormSet = formset_factory(
    PlanEstudioForm,
    extra=0, # Show one empty form by default
    can_delete=True,
)
class ReportSearchForm(forms.Form):
    buscar_paciente = forms.CharField(
        required=False,
        label="Buscar Paciente",
        widget=forms.TextInput(attrs={
            'placeholder': 'Nombre o ID del paciente',
            'id': 'buscar-paciente-input' # Ensure this ID is unique if 'buscar-paciente' is used elsewhere
        })
    )
    date_range = forms.CharField(
        required=False,
        label="Rango de Fechas",
        widget=forms.TextInput(attrs={
            'id': 'date-range-flatpickr', # This ID will be targeted by Flatpickr
            'class': 'date-range-input', # Keep existing class if needed for styling
            'placeholder': 'Seleccionar rango de fechas'
        })
    )
    tipo_registro = forms.ChoiceField(
        choices=[('', 'Todos los Tipos'), ('proposito', 'Propósito (Individual)'), ('pareja', 'Pareja')],
        required=False,
        label="Tipo de Registro",
        widget=forms.Select(attrs={'id': 'tipo-registro-select'})
    )
    genetista = forms.ModelChoiceField(
        queryset=Genetistas.objects.all().select_related('user').order_by('user__last_name', 'user__first_name'),
        required=False,
        label="Genetista",
        empty_label="Todos los Genetistas",
        widget=forms.Select(attrs={'id': 'genetista-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['genetista'].label_from_instance = lambda obj: obj.user.get_full_name() or obj.user.username

    def clean_date_range(self):
        date_range_str = self.cleaned_data.get('date_range')
        if date_range_str:
            try:
                parts = date_range_str.split(' a ')
                if len(parts) == 2:
                    fecha_desde_str, fecha_hasta_str = parts
                    # Flatpickr default format "d/m/Y"
                    fecha_desde = datetime.strptime(fecha_desde_str.strip(), '%d/%m/%Y').date()
                    fecha_hasta = datetime.strptime(fecha_hasta_str.strip(), '%d/%m/%Y').date()
                    if fecha_desde > fecha_hasta:
                        raise forms.ValidationError("La fecha 'desde' no puede ser posterior a la fecha 'hasta'.")
                    return {'desde': fecha_desde, 'hasta': fecha_hasta}
                elif len(parts) == 1 and parts[0].strip(): # Single date selected in range mode
                    fecha = datetime.strptime(parts[0].strip(), '%d/%m/%Y').date()
                    return {'desde': fecha, 'hasta': fecha}
            except ValueError:
                raise forms.ValidationError("Formato de rango de fecha inválido. Use DD/MM/YYYY o DD/MM/YYYY a DD/MM/YYYY.")
        return None

