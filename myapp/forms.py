from django import forms
from django.utils import timezone
from django.forms import ModelForm, Select,DateInput
from .models import ExamenFisico, HistoriasClinicas, Propositos, InformacionPadres, PeriodoNeonatal,AntecedentesFamiliaresPreconcepcionales,DesarrolloPsicomotor,AntecedentesPersonales, ExamenFisico, Parejas
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CreateNewTask(forms.Form):
    title = forms.CharField(label="title",max_length=200)
    description = forms.CharField(label= "description", widget=forms.Textarea)

class CreateNewProject(forms.Form):
    name = forms.CharField(label="Nombre Del Proyecto", max_length=200)

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )


class ExtendedUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, help_text='Required.')
    last_name = forms.CharField(max_length=30, required=True, help_text='Required.')
    email = forms.EmailField(max_length=254, required=True, help_text='Required. Inform a valid email address.')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')



class HistoriasForm(ModelForm):
    class Meta:
        model = HistoriasClinicas
        fields = ['numero_historia','motivo_tipo_consulta','cursante_postgrado', 'medico', 'especialidad','centro_referencia']
        widgets = {
            'motivo_tipo_consulta': Select(attrs={'onchange': 'toggleForms()'}),
        }
class PadresPropositoForm(forms.Form):
    # Datos del padre
    padre_nombres = forms.CharField(max_length=100, label="Nombres del Padre")
    padre_apellidos = forms.CharField(max_length=100, label="Apellidos del Padre")
    padre_escolaridad = forms.CharField(max_length=100, required=False, label="Escolaridad del Padre")
    padre_ocupacion = forms.CharField(max_length=100, required=False, label="Ocupación del Padre")
    padre_lugar_nacimiento = forms.CharField(max_length=100, required=False, label="Lugar de Nacimiento del Padre")
    padre_fecha_nacimiento = forms.DateField (required=False,
        widget=DateInput(attrs={'type': 'date'}), label="Fecha de Nacimiento del Padre" # Usar DateInput con type='date'
    ) 
    padre_edad = forms.IntegerField(required=False, label="Edad del Padre")
    padre_identificacion = forms.CharField(max_length=20, required=False, label="Identificación del Padre")
    padre_grupo_sanguineo = forms.ChoiceField(choices=[('A', 'A'), ('B', 'B'), ('AB', 'AB'), ('O', 'O')], required=False, label="Grupo Sanguíneo del Padre")
    padre_factor_rh = forms.ChoiceField(choices=[('Positivo', 'Positivo'), ('Negativo', 'Negativo')], required=False, label="Factor RH del Padre")
    padre_telefono = forms.CharField(max_length=15, required=False, label="Teléfono del Padre")
    padre_email = forms.EmailField(max_length=100, required=False, label="Email del Padre")
    padre_direccion = forms.CharField(max_length=200, required=False, label="Dirección del Padre")

    # Datos de la madre
    madre_nombres = forms.CharField(max_length=100, label="Nombres de la Madre")
    madre_apellidos = forms.CharField(max_length=100, label="Apellidos de la Madre")
    madre_escolaridad = forms.CharField(max_length=100, required=False, label="Escolaridad de la Madre")
    madre_ocupacion = forms.CharField(max_length=100, required=False, label="Ocupación de la Madre")
    madre_lugar_nacimiento = forms.CharField(max_length=100, required=False, label="Lugar de Nacimiento de la Madre")
    madre_fecha_nacimiento = forms.DateField(
        required=False,
        widget=DateInput(attrs={'type': 'date'}), label="Fecha de Nacimiento de la madre"  # Usar DateInput con type='date'
    )
    madre_edad = forms.IntegerField(required=False, label="Edad de la Madre")
    madre_identificacion = forms.CharField(max_length=20, required=False, label="Identificación de la Madre")
    madre_grupo_sanguineo = forms.ChoiceField(choices=[('A', 'A'), ('B', 'B'), ('AB', 'AB'), ('O', 'O')], required=False, label="Grupo Sanguíneo de la Madre")
    madre_factor_rh = forms.ChoiceField(choices=[('Positivo', 'Positivo'), ('Negativo', 'Negativo')], required=False, label="Factor RH de la Madre")
    madre_telefono = forms.CharField(max_length=15, required=False, label="Teléfono de la Madre")
    madre_email = forms.EmailField(max_length=100, required=False, label="Email de la Madre")
    madre_direccion = forms.CharField(max_length=200, required=False, label="Dirección de la Madre")
    
class PropositosForm(forms.Form):
    nombres = forms.CharField(max_length=100)
    apellidos = forms.CharField(max_length=100)
    lugar_nacimiento = forms.CharField(max_length=100, required=False)
    escolaridad = forms.CharField(max_length=100, required=False)
    ocupacion = forms.CharField(max_length=100, required=False)
    edad = forms.IntegerField(required=False)
    fecha_nacimiento = forms.DateField(
        required=False,
        widget=DateInput(attrs={'type': 'date'})  # Usar DateInput con type='date'
    )
    identificacion = forms.CharField(max_length=20)

    # documento_nacimiento = forms.FileField(required=False )  # Campo para la carga de archivos
    direccion = forms.CharField(max_length=200, required=False)
    telefono = forms.CharField(max_length=15, required=False)
    email = forms.EmailField(max_length=100, required=False)
    grupo_sanguineo = forms.ChoiceField(choices=[('A', 'A'), ('B', 'B'), ('AB', 'AB'), ('O', 'O')], required=False)
    factor_rh = forms.ChoiceField(choices=[('Positivo', 'Positivo'), ('Negativo', 'Negativo')], required=False)
    foto = forms.ImageField(
        required=False,  # Para que no sea obligatorio subir una foto
        widget=forms.ClearableFileInput(attrs={
            'accept': 'image/*'  # Aceptar solo archivos de imagen
        }),
        label='Foto del Propósito'  # Etiqueta personalizada
    )
    def save(self, historia):
        proposito = Propositos(
            historia=historia,  # Asociar el propósito a la historia clínica
            nombres=self.cleaned_data['nombres'],
            apellidos=self.cleaned_data['apellidos'],
            lugar_nacimiento=self.cleaned_data['lugar_nacimiento'],
            fecha_nacimiento=self.cleaned_data['fecha_nacimiento'],
            escolaridad=self.cleaned_data['escolaridad'],
            ocupacion=self.cleaned_data['ocupacion'],
            edad=self.cleaned_data['edad'],
            identificacion=self.cleaned_data['identificacion'],
            direccion=self.cleaned_data['direccion'],
            telefono=self.cleaned_data['telefono'],
            email=self.cleaned_data['email'],
            grupo_sanguineo=self.cleaned_data['grupo_sanguineo'],
            factor_rh=self.cleaned_data['factor_rh']
        )
        
        # Manejar el documento de nacimiento (si existe)
        if 'documento_nacimiento' in self.cleaned_data and self.cleaned_data['documento_nacimiento']:
            proposito.documento_nacimiento = self.cleaned_data['documento_nacimiento'].read()
        
        # Manejar la foto (si existe)
        if 'foto' in self.cleaned_data and self.cleaned_data['foto']:
            proposito.foto = self.cleaned_data['foto']
        
        # Guardar el propósito en la base de datos
        proposito.save()
        return proposito

class ParejaPropositosForm(forms.Form):
    # Campos para el primer conyugue (proposito 1)
    nombres_1 = forms.CharField(max_length=100, label="Nombres (Primer Conyugue)")
    apellidos_1 = forms.CharField(max_length=100, label="Apellidos (Primer Conyugue)")
    lugar_nacimiento_1 = forms.CharField(max_length=100, required=False, label="Lugar de Nacimiento")
    fecha_nacimiento_1 = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Fecha de Nacimiento"
    )
    escolaridad_1 = forms.CharField(max_length=100, required=False)
    ocupacion_1 = forms.CharField(max_length=100, required=False)
    edad_1 = forms.IntegerField(required=False)
    identificacion_1 = forms.CharField(max_length=20, label="Identificación")
    # documento_nacimiento_1 = forms.FileField(required=False)
    direccion_1 = forms.CharField(max_length=200, required=False)
    telefono_1 = forms.CharField(max_length=15, required=False)
    email_1 = forms.EmailField(max_length=100, required=False)
    grupo_sanguineo_1 = forms.ChoiceField(
        choices=[('', 'Seleccione'), ('A', 'A'), ('B', 'B'), ('AB', 'AB'), ('O', 'O')], 
        required=False
    )
    factor_rh_1 = forms.ChoiceField(
        choices=[('', 'Seleccione'), ('Positivo', 'Positivo'), ('Negativo', 'Negativo')], 
        required=False
    )
    foto_1 = forms.ImageField(required=False)
    
    # Campos para el segundo conyugue (proposito 2)
    nombres_2 = forms.CharField(max_length=100, label="Nombres (Segundo Conyugue)")
    apellidos_2 = forms.CharField(max_length=100, label="Apellidos (Segundo Conyugue)")
    lugar_nacimiento_2 = forms.CharField(max_length=100, required=False)
    fecha_nacimiento_2 = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    escolaridad_2 = forms.CharField(max_length=100, required=False)
    ocupacion_2 = forms.CharField(max_length=100, required=False)
    edad_2 = forms.IntegerField(required=False)
    identificacion_2 = forms.CharField(max_length=20, label="Identificación")
    # documento_nacimiento_2 = forms.FileField(required=False)
    direccion_2 = forms.CharField(max_length=200, required=False)
    telefono_2 = forms.CharField(max_length=15, required=False)
    email_2 = forms.EmailField(max_length=100, required=False)
    grupo_sanguineo_2 = forms.ChoiceField(
        choices=[('', 'Seleccione'), ('A', 'A'), ('B', 'B'), ('AB', 'AB'), ('O', 'O')], 
        required=False
    )
    factor_rh_2 = forms.ChoiceField(
        choices=[('', 'Seleccione'), ('Positivo', 'Positivo'), ('Negativo', 'Negativo')], 
        required=False
    )
    foto_2 = forms.ImageField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        # Validar que las identificaciones sean diferentes
        if cleaned_data.get('identificacion_1') == cleaned_data.get('identificacion_2'):
            raise forms.ValidationError("Las identificaciones de los conyugues deben ser diferentes")
        return cleaned_data

     
class AntecedentesDesarrolloNeonatalForm(forms.Form):
    # Campos de AntecedentesPersonales
    fur = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    edad_gestacional = forms.IntegerField(required=False)
    controles_prenatales = forms.CharField(max_length=100, required=False)
    numero_partos = forms.IntegerField(required=False)
    numero_gestas = forms.IntegerField(required=False)
    numero_cesareas = forms.IntegerField(required=False)
    numero_abortos = forms.IntegerField(required=False)
    numero_mortinatos = forms.IntegerField(required=False)
    numero_malformaciones = forms.IntegerField(required=False)
    complicaciones_embarazo = forms.CharField(required=False, widget=forms.Textarea (attrs={'rows': 2}))
    exposicion_teratogenos = forms.ChoiceField(
        choices=[('', '---------')] + AntecedentesPersonales._meta.get_field('exposicion_teratogenos').choices,
        required=False
    )
    descripcion_exposicion = forms.CharField(required=False, widget=forms.Textarea (attrs={'rows': 2}))
    enfermedades_maternas = forms.CharField(required=False, widget=forms.Textarea (attrs={'rows': 2}))
    complicaciones_parto = forms.CharField(required=False, widget=forms.Textarea (attrs={'rows': 2}))
    otros_antecedentes = forms.CharField(required=False, widget=forms.Textarea (attrs={'rows': 2}))
    observaciones = forms.CharField(required=False, widget=forms.Textarea (attrs={'rows': 2}))

    # Campos de DesarrolloPsicomotor
    sostener_cabeza = forms.CharField(max_length=100, required=False)
    sonrisa_social = forms.CharField(max_length=100, required=False)
    sentarse =forms.CharField(max_length=100, required=False)
    gatear = forms.CharField(max_length=100, required=False)
    pararse = forms.CharField(max_length=100, required=False)
    caminar = forms.CharField(max_length=100, required=False)
    primeras_palabras = forms.CharField(max_length=100, required=False)
    primeros_dientes = forms.CharField(max_length=100, required=False)
    progreso_escuela = forms.CharField(required=False, widget=forms.Textarea (attrs={'rows': 2}))
    progreso_peso = forms.CharField(required=False, widget=forms.Textarea (attrs={'rows': 2}))
    progreso_talla = forms.CharField(required=False, widget=forms.Textarea (attrs={'rows': 2}))

    # Campos de PeriodoNeonatal
    peso_nacer = forms.DecimalField(required=False, max_digits=5, decimal_places=2)
    talla_nacer = forms.DecimalField(required=False, max_digits=5, decimal_places=2)
    circunferencia_cefalica = forms.DecimalField(required=False, max_digits=5, decimal_places=2)
    cianosis =forms.CharField(max_length=100, required=False)
    ictericia = forms.CharField(max_length=100, required=False)
    hemorragia = forms.CharField(max_length=100, required=False)
    infecciones = forms.CharField(max_length=100, required=False)
    convulsiones = forms.CharField(max_length=100, required=False)
    vomitos = forms.CharField(max_length=100, required=False)
    observacion_complicaciones = forms.CharField(required=False, widget=forms.Textarea (attrs={'rows': 2}))
    otros_complicaciones = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))
    tipo_alimentacion = forms.ChoiceField(
        choices=[('', '---------')] + PeriodoNeonatal._meta.get_field('tipo_alimentacion').choices,
        required=False
    )
    observaciones_alimentacion = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))
    evolucion = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))
    observaciones_habitos_psicologicos = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))

    def save(self, proposito=None, pareja=None):
        if not proposito and not pareja:
            raise ValueError("Debe proporcionar un propósito o una pareja")
        if proposito and pareja:
            raise ValueError("No puede proporcionar tanto un propósito como una pareja")

        # Guardar AntecedentesPersonales
        antecedentes = AntecedentesPersonales(
            proposito=proposito,
            pareja=pareja,
            fur=self.cleaned_data.get('fur'),
            edad_gestacional=self.cleaned_data.get('edad_gestacional'),
            controles_prenatales=self.cleaned_data.get('controles_prenatales'),
            numero_partos=self.cleaned_data.get('numero_partos'),
            numero_gestas=self.cleaned_data.get('numero_gestas'),
            numero_cesareas=self.cleaned_data.get('numero_cesareas'),
            numero_abortos=self.cleaned_data.get('numero_abortos'),
            numero_mortinatos=self.cleaned_data.get('numero_mortinatos'),
            numero_malformaciones=self.cleaned_data.get('numero_malformaciones'),
            complicaciones_embarazo=self.cleaned_data.get('complicaciones_embarazo'),
            exposicion_teratogenos=self.cleaned_data.get('exposicion_teratogenos'),
            descripcion_exposicion=self.cleaned_data.get('descripcion_exposicion'),
            enfermedades_maternas=self.cleaned_data.get('enfermedades_maternas'),
            complicaciones_parto=self.cleaned_data.get('complicaciones_parto'),
            otros_antecedentes=self.cleaned_data.get('otros_antecedentes')
        )
        antecedentes.save()

        # Guardar DesarrolloPsicomotor
        desarrollo = DesarrolloPsicomotor(
            proposito=proposito,
            pareja=pareja,
            sostener_cabeza=self.cleaned_data.get('sostener_cabeza'),
            sonrisa_social=self.cleaned_data.get('sonrisa_social'),
            sentarse=self.cleaned_data.get('sentarse'),
            gatear=self.cleaned_data.get('gatear'),
            pararse=self.cleaned_data.get('pararse'),
            caminar=self.cleaned_data.get('caminar'),
            primeras_palabras=self.cleaned_data.get('primeras_palabras'),
            primeros_dientes=self.cleaned_data.get('primeros_dientes'),
            progreso_escuela=self.cleaned_data.get('progreso_escuela'),
            progreso_peso=self.cleaned_data.get('progreso_peso'),
            progreso_talla=self.cleaned_data.get('progreso_talla')
        )
        desarrollo.save()

        # Guardar PeriodoNeonatal
        neonatal = PeriodoNeonatal(
            proposito=proposito,
            pareja=pareja,
            peso_nacer=self.cleaned_data.get('peso_nacer'),
            talla_nacer=self.cleaned_data.get('talla_nacer'),
            circunferencia_cefalica=self.cleaned_data.get('circunferencia_cefalica'),
            cianosis=self.cleaned_data.get('cianosis'),
            ictericia=self.cleaned_data.get('ictericia'),
            hemorragia=self.cleaned_data.get('hemorragia'),
            infecciones=self.cleaned_data.get('infecciones'),
            convulsiones=self.cleaned_data.get('convulsiones'),
            vomitos=self.cleaned_data.get('vomitos'),
            observacion_complicaciones=self.cleaned_data.get('observacion_complicaciones'),
            otros_complicaciones=self.cleaned_data.get('otros_complicaciones'),
            tipo_alimentacion=self.cleaned_data.get('tipo_alimentacion'),
            observaciones_alimentacion=self.cleaned_data.get('observaciones_alimentacion'),
            evolucion=self.cleaned_data.get('evolucion'),
            observaciones_habitos_psicologicos=self.cleaned_data.get('observaciones_habitos_psicologicos')
        )
        neonatal.save()

        return antecedentes, desarrollo, neonatal
    

class AntecedentesPreconcepcionalesForm(forms.Form):
    # Campos de AntecedentesPersonales
    antecedentes_padre = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))
    antecedentes_madre = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))
    estado_salud_padre = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))
    estado_salud_madre = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))
    fecha_union_pareja = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    consanguinidad = forms.ChoiceField(choices=[('si', 'Si'), ('no', 'No')], required=False)
    grado_consanguinidad = forms.CharField(max_length=30, required=False)

    def save(self, proposito=None, pareja=None, tipo=None):
        if tipo not in ['proposito', 'pareja']:
            raise ValueError("Tipo debe ser 'proposito' o 'pareja'")
        
        # Crear el objeto según el tipo
        if tipo == 'proposito':
            antecedentespre = AntecedentesFamiliaresPreconcepcionales(
                proposito=proposito,
                antecedentes_padre=self.cleaned_data.get('antecedentes_padre'),
                antecedentes_madre=self.cleaned_data.get('antecedentes_madre'),
                estado_salud_padre=self.cleaned_data.get('estado_salud_padre'),
                estado_salud_madre=self.cleaned_data.get('estado_salud_madre'),
                fecha_union_pareja=self.cleaned_data.get('fecha_union_pareja'),
                consanguinidad=self.cleaned_data.get('consanguinidad'),
                grado_consanguinidad=self.cleaned_data.get('grado_consanguinidad'),
            )
        else:  # tipo == 'pareja'
            antecedentespre = AntecedentesFamiliaresPreconcepcionales(
                pareja=pareja,
                antecedentes_padre=self.cleaned_data.get('antecedentes_padre'),
                antecedentes_madre=self.cleaned_data.get('antecedentes_madre'),
                estado_salud_padre=self.cleaned_data.get('estado_salud_padre'),
                estado_salud_madre=self.cleaned_data.get('estado_salud_madre'),
                fecha_union_pareja=self.cleaned_data.get('fecha_union_pareja'),
                consanguinidad=self.cleaned_data.get('consanguinidad'),
                grado_consanguinidad=self.cleaned_data.get('grado_consanguinidad'),
            )
        
        antecedentespre.save()
        return antecedentespre

class ExamenFisicoForm(forms.ModelForm):
    class Meta:
        model = ExamenFisico
        fields = '__all__'
        exclude = ['fecha_examen', 'proposito']  # Estos campos se manejarán en la vista
        widgets = {
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
            'ss_si': forms.NumberInput(attrs={'step': '0.01'}),
            'distancia_interc_externa': forms.NumberInput(attrs={'step': '0.01'}),
            'ct': forms.NumberInput(attrs={'step': '0.01'}),
            'pabellones_auriculares': forms.NumberInput(attrs={'step': '0.01'}),
            'tension_arterial_sistolica': forms.NumberInput(attrs={'step': '0.01'}),
            'tension_arterial_diastolica': forms.NumberInput(attrs={'step': '0.01'}),
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

    def save(self, commit=True):
        examenfisico = super().save(commit=False)
        
        if hasattr(self, 'proposito') and self.proposito:
            examenfisico.proposito = self.proposito
        
        examenfisico.fecha_examen = timezone.now()
        
        if commit:
            examenfisico.save()
            self.save_m2m()
        
        return examenfisico

        

