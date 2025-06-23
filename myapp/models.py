from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import date

# Create your models here.

class Project(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Task(models.Model):
    title =models.CharField(max_length=200)
    description = models.TextField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    done = models.BooleanField(default =False)

    def __str__(self):
        return self.title + "-" + self.project.name


class ExamenFisico(models.Model):
    examen_id = models.AutoField(primary_key=True)
    proposito = models.ForeignKey('Propositos', on_delete=models.CASCADE, unique=True)
    fecha_examen = models.DateField(auto_now_add=True)
    medida_abrazada = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    segmento_inferior = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    segmento_superior = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    circunferencia_cefalica = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    talla = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    distancia_intermamilar = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    distancia_interc_interna = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    distancia_interpupilar = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    longitud_mano_derecha = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    longitud_mano_izquierda = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    peso = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    ss_si = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    distancia_interc_externa = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    ct = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    pabellones_auriculares = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    tension_arterial_sistolica = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    tension_arterial_diastolica = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    observaciones_cabeza = models.TextField(blank=True, null=True)
    observaciones_cuello = models.TextField(blank=True, null=True)
    observaciones_torax = models.TextField(blank=True, null=True)
    observaciones_abdomen = models.TextField(blank=True, null=True)
    observaciones_genitales = models.TextField(blank=True, null=True)
    observaciones_espalda = models.TextField(blank=True, null=True)
    observaciones_miembros_superiores = models.TextField(blank=True, null=True)
    observaciones_miembros_inferiores = models.TextField(blank=True, null=True)
    observaciones_piel = models.TextField(blank=True, null=True)
    observaciones_osteomioarticular = models.TextField(blank=True, null=True)
    observaciones_neurologico = models.TextField(blank=True, null=True)
    observaciones_pliegues = models.TextField(blank=True, null=True)

    def __str__(self):
        proposito_nombre = "N/A"
        if self.proposito:
            proposito_nombre = f"{self.proposito.nombres} {self.proposito.apellidos}"
        return f"Examen Físico {self.examen_id} para {proposito_nombre}"

class Parejas(models.Model):
    pareja_id = models.AutoField(primary_key=True)
    proposito_id_1 = models.ForeignKey('Propositos', on_delete=models.CASCADE, related_name='parejas_como_1')
    proposito_id_2 = models.ForeignKey('Propositos', on_delete=models.CASCADE, related_name='parejas_como_2')

    class Meta:
        unique_together = (('proposito_id_1', 'proposito_id_2'),)

    def clean(self):
        if self.proposito_id_1_id and self.proposito_id_2_id:
            if self.proposito_id_1_id == self.proposito_id_2_id:
                raise ValidationError("Un propósito no puede formar una pareja consigo mismo.")
            if self.proposito_id_1_id > self.proposito_id_2_id:
                self.proposito_id_1, self.proposito_id_2 = self.proposito_id_2, self.proposito_id_1
        super().clean()

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        p1_nombre = "N/A"
        p2_nombre = "N/A"
        if self.proposito_id_1:
            p1_nombre = f"{self.proposito_id_1.nombres} {self.proposito_id_1.apellidos}"
        if self.proposito_id_2:
            p2_nombre = f"{self.proposito_id_2.nombres} {self.proposito_id_2.apellidos}"
        return f"Pareja {self.pareja_id}: {p1_nombre} y {p2_nombre}"


class AntecedentesFamiliaresPreconcepcionales(models.Model):
    antecedente_familiar_id = models.AutoField(primary_key=True)
    proposito = models.ForeignKey(
        'Propositos',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        unique=False
    )
    pareja = models.ForeignKey(
        'Parejas',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        unique=False
    )
    antecedentes_padre = models.TextField(null=True, blank=True)
    antecedentes_madre = models.TextField(null=True, blank=True)
    estado_salud_padre = models.TextField(null=True, blank=True)
    estado_salud_madre = models.TextField(null=True, blank=True)
    fecha_union_pareja = models.DateField(null=True, blank=True)
    consanguinidad = models.CharField(max_length=2, choices=[('Sí', 'Sí'), ('No', 'No')], null=True, blank=True)
    grado_consanguinidad = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(proposito__isnull=False, pareja__isnull=True) |
                    models.Q(proposito__isnull=True, pareja__isnull=False)
                ),
                name='check_proposito_or_pareja_familiares'
            ),
            models.UniqueConstraint(
                fields=['proposito'],
                name='unique_antecedente_familiar_proposito',
                condition=models.Q(proposito__isnull=False)
            ),
            models.UniqueConstraint(
                fields=['pareja'],
                name='unique_antecedente_familiar_pareja',
                condition=models.Q(pareja__isnull=False)
            )
        ]

    def clean(self):
        if self.proposito and self.pareja:
            raise ValidationError("Los antecedentes familiares no pueden estar relacionados con un propósito y una pareja al mismo tiempo.")
        if not self.proposito and not self.pareja:
            raise ValidationError("Los antecedentes familiares deben estar relacionados con un propósito o una pareja.")
        if self.consanguinidad == 'No' and self.grado_consanguinidad:
            self.grado_consanguinidad = "" # Clear it if 'No'
        if self.consanguinidad == 'Sí' and not self.grado_consanguinidad:
             raise ValidationError("Debe especificar el grado de consanguinidad si seleccionó 'Sí'.")


    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.proposito:
            return f"Antecedentes Familiares de {self.proposito}"
        elif self.pareja:
            return f"Antecedentes Familiares de Pareja {self.pareja_id}"
        return f"Antecedente Familiar {self.antecedente_familiar_id}"

class AntecedentesPersonales(models.Model):
    antecedente_id = models.AutoField(primary_key=True)
    proposito = models.ForeignKey(
        'Propositos',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    pareja = models.ForeignKey(
        'Parejas',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    fur = models.DateField(null=True, blank=True)
    edad_gestacional = models.IntegerField(null=True, blank=True)
    controles_prenatales = models.CharField(max_length=100, blank=True, default='')
    numero_partos = models.IntegerField(null=True, blank=True)
    numero_gestas = models.IntegerField(null=True, blank=True)
    numero_cesareas = models.IntegerField(null=True, blank=True)
    numero_abortos = models.IntegerField(null=True, blank=True)
    numero_mortinatos = models.IntegerField(null=True, blank=True)
    numero_malformaciones = models.IntegerField(null=True, blank=True)
    complicaciones_embarazo = models.TextField(null=True, blank=True)
    exposicion_teratogenos = models.CharField(
        max_length=20,
        choices=[('Físicos', 'Físicos'), ('Químicos', 'Químicos'), ('Biológicos', 'Biológicos')],
        null=True,
        blank=True
    )
    descripcion_exposicion = models.TextField(null=True, blank=True)
    enfermedades_maternas = models.TextField(null=True, blank=True)
    complicaciones_parto = models.TextField(null=True, blank=True)
    otros_antecedentes = models.TextField(null=True, blank=True)
    observaciones = models.TextField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(proposito__isnull=False, pareja__isnull=True) |
                    models.Q(proposito__isnull=True, pareja__isnull=False)
                ),
                name='check_proposito_or_pareja_personales'
            ),
            models.UniqueConstraint(
                fields=['proposito'],
                name='unique_antecedente_personal_proposito',
                condition=models.Q(proposito__isnull=False)
            ),
            models.UniqueConstraint(
                fields=['pareja'],
                name='unique_antecedente_personal_pareja',
                condition=models.Q(pareja__isnull=False)
            )
        ]

    def clean(self):
        if self.proposito and self.pareja:
            raise ValidationError("Los antecedentes personales no pueden estar relacionados con un propósito y una pareja al mismo tiempo.")
        if not self.proposito and not self.pareja:
            raise ValidationError("Los antecedentes personales deben estar relacionados con un propósito o una pareja.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.proposito:
            return f"Antecedentes Personales de {self.proposito}"
        elif self.pareja:
            return f"Antecedentes Personales de Pareja {self.pareja_id}"
        return f"Antecedente Personal {self.antecedente_id}"

class Autorizaciones(models.Model):
    autorizacion_id = models.AutoField(primary_key=True)
    proposito = models.OneToOneField(
        'Propositos', 
        on_delete=models.CASCADE, 
        related_name='autorizacion'
    )
    autorizacion_examenes = models.BooleanField(
        default=False,
        verbose_name="¿Autoriza la realización de exámenes genéticos?"
    )
    archivo_autorizacion = models.FileField(
        upload_to='autorizaciones/', 
        null=True, 
        blank=True,
        verbose_name="Archivo de Autorización Firmado"
    )
    representante_padre = models.ForeignKey(
        'InformacionPadres',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="El padre/madre que autoriza, solo si el propósito es menor de edad."
    )
    fecha_autorizacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        autoriza = "Nadie"
        if self.representante_padre:
            autoriza = f"Representante: {self.representante_padre.nombres}"
        else:
            autoriza = f"El mismo paciente"

        return f"Autorización para {self.proposito.nombres} (Autoriza: {autoriza})"

    def clean(self):
        super().clean()
        if self.representante_padre and self.representante_padre.proposito != self.proposito:
            raise ValidationError("El representante seleccionado no corresponde a los padres de este propósito.")
class DesarrolloPsicomotor(models.Model):
    desarrollo_id = models.AutoField(primary_key=True)
    proposito = models.ForeignKey(
        'Propositos',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    pareja = models.ForeignKey(
        'Parejas',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    sostener_cabeza = models.CharField(max_length=100, null=True, blank=True)
    sonrisa_social = models.CharField(max_length=100, null=True, blank=True)
    sentarse = models.CharField(max_length=100, null=True, blank=True)
    gatear = models.CharField(max_length=100, null=True, blank=True)
    pararse = models.CharField(max_length=100, null=True, blank=True)
    caminar = models.CharField(max_length=100, null=True, blank=True)
    primeras_palabras =models.CharField(max_length=100, null=True, blank=True)
    primeros_dientes = models.CharField(max_length=100, null=True, blank=True)
    progreso_escuela = models.CharField(max_length=100, null=True, blank=True)
    progreso_peso = models.CharField(max_length=100, null=True, blank=True)
    progreso_talla = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(proposito__isnull=False, pareja__isnull=True) |
                    models.Q(proposito__isnull=True, pareja__isnull=False)
                ),
                name='check_desarrollo_proposito_or_pareja'
            ),
            models.UniqueConstraint(
                fields=['proposito'],
                name='unique_desarrollo_proposito',
                condition=models.Q(proposito__isnull=False)
            ),
            models.UniqueConstraint(
                fields=['pareja'],
                name='unique_desarrollo_pareja',
                condition=models.Q(pareja__isnull=False)
            )
        ]

    def clean(self):
        if self.proposito and self.pareja:
            raise ValidationError("El desarrollo psicomotor no puede estar relacionado con un propósito y una pareja al mismo tiempo.")
        if not self.proposito and not self.pareja:
            raise ValidationError("El desarrollo psicomotor debe estar relacionado con un propósito o una pareja.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.proposito:
            return f"Desarrollo Psicomotor de {self.proposito}"
        elif self.pareja:
            return f"Desarrollo Psicomotor de Pareja {self.pareja_id}"
        return f"Desarrollo Psicomotor {self.desarrollo_id}"


class EvaluacionGenetica(models.Model):
    evaluacion_id = models.AutoField(primary_key=True)
    proposito = models.ForeignKey(
        'Propositos',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    pareja = models.ForeignKey(
        'Parejas',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    signos_clinicos = models.TextField(
        verbose_name="Signos Clínicos Relevantes",
        blank=True,
        null=True,
        help_text="Describa los signos clínicos más relevantes que inician esta evaluación."
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # Regla 1: Debe estar asociado a un propósito O a una pareja, pero no a ambos.
            
            # Regla 2: Un propósito solo puede tener UNA evaluación genética.
            models.UniqueConstraint(
                fields=['proposito'],
                name='unique_evaluacion_proposito',
                condition=models.Q(proposito__isnull=False)
            ),
            # Regla 3: Una pareja solo puede tener UNA evaluación genética.
            models.UniqueConstraint(
                fields=['pareja'],
                name='unique_evaluacion_pareja',
                condition=models.Q(pareja__isnull=False)
            )
        ]
        verbose_name = "Evaluación Genética"
        verbose_name_plural = "Evaluaciones Genéticas"

    def clean(self):
        # Validación a nivel de aplicación para mensajes de error claros
        if self.proposito and self.pareja:
            raise ValidationError("La evaluación genética no puede estar relacionada con un propósito y una pareja al mismo tiempo.")
        if not self.proposito and not self.pareja:
            raise ValidationError("La evaluación genética debe estar relacionada con un propósito o una pareja.")
        super().clean()

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.proposito:
            return f"Evaluación Genética de {self.proposito}"
        elif self.pareja:
            return f"Evaluación Genética de Pareja {self.pareja.pareja_id if self.pareja else 'N/A'}"
        return f"Evaluación Genética ID: {self.evaluacion_id}"


# 2. NUEVO MODELO 'DETALLE' PARA DIAGNÓSTICOS
class DiagnosticoPresuntivo(models.Model):
    diagnostico_id = models.AutoField(primary_key=True)
    evaluacion = models.ForeignKey(
        EvaluacionGenetica,
        on_delete=models.CASCADE, # Si se borra la evaluación, se borran sus diagnósticos.
        related_name='diagnosticos_presuntivos' # Permite acceder desde una evaluacion: `eval.diagnosticos_presuntivos.all()`
    )
    descripcion = models.TextField(
        verbose_name="Diagnóstico Presuntivo",
        help_text="Ingrese un diagnóstico presuntivo"
    )
    orden = models.PositiveIntegerField(
        default=0,
        help_text="Orden de importancia (0=más probable, 1=segundo, etc.)"
    )

    class Meta:
        ordering = ['orden'] # Por defecto se mostrarán ordenados por importancia.
        verbose_name = "Diagnóstico Presuntivo"
        verbose_name_plural = "Diagnósticos Presuntivos"

    def __str__(self):
        return f"Diagnóstico #{self.orden + 1}: {self.descripcion[:50]}..."


# 3. NUEVO MODELO 'DETALLE' PARA PLANES DE ESTUDIO / CONSULTAS
class PlanEstudio(models.Model):
    plan_id = models.AutoField(primary_key=True)
    evaluacion = models.ForeignKey(
        EvaluacionGenetica,
        on_delete=models.CASCADE, # Si se borra la evaluación, se borra su historial de planes.
        related_name='planes_estudio' # Permite acceder desde una evaluacion: `eval.planes_estudio.all()`
    )
    accion = models.TextField(
        verbose_name="Acción a realizar / Exámenes solicitados",
        help_text="Describa el plan de estudio, exámenes o pasos a seguir para la próxima consulta."
    )
    completado = models.BooleanField(
        default=False,
        verbose_name="Plan Completado"
    )
    fecha_visita = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de Próxima Visita / Límite"
    )
    asesoramiento_evoluciones = models.TextField(
        verbose_name="Asesoramiento y Evoluciones (Resultados de la consulta)",
        null=True,
        blank=True,
        help_text="Llenar este campo cuando el paciente regrese y el plan se marque como completado."
    )

    class Meta:
        ordering = ['-fecha_visita', '-plan_id'] # Muestra los más recientes primero.
        verbose_name = "Plan de Estudio / Consulta"
        verbose_name_plural = "Planes de Estudio / Consultas"

    def __str__(self):
        estado = 'Completado' if self.completado else 'Pendiente'
        fecha = f" (Visita: {self.fecha_visita})" if self.fecha_visita else ""
        return f"Plan: {self.accion[:40]}... [{estado}]{fecha}"

class EvolucionDesarrollo(models.Model):
    evolucion_id = models.AutoField(primary_key=True)
    proposito = models.ForeignKey('Propositos', on_delete=models.CASCADE, null=True, blank=True)
    fecha = models.DateField(blank=True, null=True)
    historial_enfermedades = models.TextField(null=True, blank=True)
    hospitalizaciones = models.TextField(null=True, blank=True)
    cirugias = models.TextField(null=True, blank=True)
    convulsiones = models.TextField(null=True, blank=True)
    otros_antecedentes = models.TextField(null=True, blank=True)
    resultados_examenes = models.FileField(null=True, blank=True)

    def __str__(self):
        return f"Evolucion Desarrollo {self.evolucion_id} para {self.proposito if self.proposito else 'N/A'}"

class Genealogia(models.Model):
    TIPO_FAMILIAR_CHOICES = [
        ('proposito', 'Propósito'),
        ('pareja', 'Pareja'),
        ('padre', 'Padre'),
        ('madre', 'Madre'),
        ('abuelo_paterno', 'Abuelo Paterno'),
        ('abuela_paterna', 'Abuela Paterna'),
        ('abuelo_materno', 'Abuelo Materno'),
        ('abuela_materna', 'Abuela Materna'),
        ('hermano', 'Hermano/a'),
        ('hijo', 'Hijo/a'),
    ]

    genealogia_id = models.AutoField(primary_key=True)
    proposito = models.ForeignKey(
        'Propositos',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='genealogia_proposito'
    )
    pareja = models.ForeignKey(
        'Parejas',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='genealogia_pareja'
    )
    tipo_familiar = models.CharField(max_length=20, choices=TIPO_FAMILIAR_CHOICES)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    fecha_fallecimiento = models.DateField(null=True, blank=True)
    estado_salud = models.TextField(null=True, blank=True)
    consanguinidad = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    notas = models.TextField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(proposito__isnull=False, pareja__isnull=True) |
                    models.Q(proposito__isnull=True, pareja__isnull=False)
                ),
                name='genealogia_proposito_or_pareja'
            )
        ]

    def __str__(self):
        return f"{self.nombres} {self.apellidos} ({self.get_tipo_familiar_display()})"

    def clean(self):
        super().clean()
        if self.proposito and self.pareja:
            raise ValidationError("Un registro de genealogía debe estar relacionado con un propósito O una pareja, no ambos.")
        if not self.proposito and not self.pareja:
            raise ValidationError("Un registro de genealogía debe estar relacionado con un propósito o una pareja.")

        if self.tipo_familiar == 'pareja' and not self.pareja:
            raise ValidationError("El tipo 'pareja' debe estar asociado a un registro de Pareja.")

class Genetistas(models.Model):
    ROL_CHOICES = [
        ('GEN', 'Genetista'),
        ('ADM', 'Administrador'),
        ('LEC', 'Lector')
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='genetistas')
    genetista_id = models.AutoField(primary_key=True) # This is not standard if user is OneToOneField, user.pk would be the ID. Keeping if it's your convention.
    rol = models.CharField(max_length=3, choices=ROL_CHOICES, default='GEN', verbose_name="Rol del Usuario")
    associated_genetista = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lectores_asociados',
        help_text="Si el rol es Lector, genetista (con rol 'Genetista') al que está asociado."
    )

    def clean(self):
        super().clean()
        if self.rol == 'LEC': # Lector
            if not self.associated_genetista:
                raise ValidationError({'associated_genetista': "Un Lector debe estar asociado a un Genetista."})
            if self.associated_genetista == self:
                raise ValidationError({'associated_genetista': "Un Lector no puede estar asociado a sí mismo."})
            if self.associated_genetista and self.associated_genetista.rol != 'GEN':
                raise ValidationError({'associated_genetista': "El Lector solo puede asociarse a un perfil con rol 'Genetista'."})
        elif self.rol in ['GEN', 'ADM']: # Not a Lector
            if self.associated_genetista:
                # Clear it if role changed from Lector, or raise error
                self.associated_genetista = None
                # raise ValidationError({'associated_genetista': "Solo los Lectores pueden tener un genetista asociado."})
        
        # Ensure a User cannot be their own associated_genetista through a chain if that's a concern
        # (e.g. A is GEN, B is LEC for A, C is LEC for B. If B's role changes to GEN, C's association to B is fine)
        # The current checks are direct.

    def save(self, *args, **kwargs):
        self.full_clean() # Ensure clean is called before saving
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_rol_display()}: {self.user.username}"

@receiver(post_save, sender=User)
def create_or_update_genetista_profile(sender, instance, created, **kwargs):
    if created:
        Genetistas.objects.get_or_create(user=instance) # Defaults to 'GEN' rol
    elif not hasattr(instance, 'genetistas'): # If user exists but profile somehow missing
        Genetistas.objects.get_or_create(user=instance)


class HistorialCambios(models.Model):

    cambio_id = models.AutoField(primary_key=True)
    historia = models.ForeignKey('HistoriasClinicas', on_delete=models.CASCADE, null=True, blank=True)
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    descripcion_cambio = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Historial Cambio {self.cambio_id} para Historia {self.historia_id if self.historia else 'N/A'}"

class HistoriasClinicas(models.Model):

    ESTADO_BORRADOR = 'borrador'
    ESTADO_FINALIZADA = 'finalizada'
    
    ESTADO_CHOICES = [
        (ESTADO_BORRADOR, 'Borrador'),
        (ESTADO_FINALIZADA, 'Finalizada'),
    ]

    historia_id = models.AutoField(primary_key=True)
    numero_historia = models.IntegerField(unique=True)
    fecha_ingreso = models.DateTimeField(auto_now_add=True)
    motivo_tipo_consulta = models.CharField(max_length=35, choices=[('Pareja-Asesoramiento Prenupcial', 'Pareja-Asesoramiento Prenupcial'), ('Pareja-Preconcepcional', 'Pareja-Preconcepcional'), ('Pareja-Prenatal', 'Pareja-Prenatal'), ('Proposito-Diagnóstico', 'Proposito-Diagnóstico')])
    genetista = models.ForeignKey('Genetistas', on_delete=models.SET_NULL, null=True, blank=True) # Changed to SET_NULL
    cursante_postgrado = models.CharField(max_length=100, null=True, blank=True)
    centro_referencia = models.CharField(max_length=100, null=True, blank=True)
    medico = models.CharField(max_length=100, null=True, blank=True)
    especialidad = models.CharField(max_length=100, null=True, blank=True)

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default=ESTADO_BORRADOR,
        verbose_name="Estado de la Historia"
    )

    def get_paciente_display(self):
        """
        Devuelve el nombre del paciente o de la pareja asociado a esta historia.
        Este método asume que has usado .prefetch_related('propositos') en tu queryset para eficiencia.
        """
        # La relación inversa desde Propositos es 'propositos_set' por defecto, pero como la ForeignKey
        # se llama 'historia', el related_name por defecto es 'propositos_set'.
        # Si lo cambiaste en el modelo Propositos, ajusta esto.
        propositos = self.propositos_set.all()

        if not propositos:
            return "Sin Paciente Asignado"

        if len(propositos) == 1:
            return f"{propositos[0].nombres} {propositos[0].apellidos}"
        
        # Para más de un propósito, asumimos que son una pareja.
        # La lógica robusta buscaría el objeto Pareja, pero esto es más directo.
        if len(propositos) > 1:
            names = " y ".join([f"{p.nombres}" for p in propositos])
            return f"Pareja: {names}"
        
        return "Información de paciente inconsistente"


    def __str__(self):
        # MODIFICADO: Se añade el estado al string
        return f"Historia Clinica N° {self.numero_historia} ({self.get_estado_display()})"


class InformacionPadres(models.Model):
    padre_id = models.AutoField(primary_key=True)
    proposito = models.ForeignKey('Propositos', on_delete=models.CASCADE, null=True, blank=True)
    tipo = models.CharField(max_length=10, choices=[('Padre', 'Padre'), ('Madre', 'Madre')])
    escolaridad = models.CharField(max_length=100, null=True, blank=True)
    ocupacion = models.CharField(max_length=100, null=True, blank=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    lugar_nacimiento = models.CharField(max_length=100, null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    edad = models.IntegerField(null=True, blank=True)
    identificacion = models.CharField(max_length=20, null=True, blank=True,unique=True)
    grupo_sanguineo = models.CharField(max_length=2, choices=[('A', 'A'), ('B', 'B'), ('AB', 'AB'), ('O', 'O')], null=True, blank=True)
    factor_rh = models.CharField(max_length=10, choices=[('Positivo', 'Positivo'), ('Negativo', 'Negativo')], null=True, blank=True)
    telefono = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    direccion = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['proposito', 'tipo'],
                name='unique_tipo_por_proposito'
            ),
            models.CheckConstraint(
                check=models.Q(tipo__in=['Padre', 'Madre']),
                name='tipo_valido'
            )
        ]

    def clean(self):
        if self.proposito and self.tipo:
            existing = InformacionPadres.objects.filter(proposito=self.proposito, tipo=self.tipo)
            if self.pk:
                existing = existing.exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError(f'Ya existe un registro de "{self.tipo}" para este propósito.')
        super().clean()


    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        proposito_str = self.proposito_id if not self.proposito else self.proposito.identificacion
        return f"Informacion {self.tipo}: {self.nombres} {self.apellidos} (Propósito: {proposito_str})"


class PeriodoNeonatal(models.Model):
    TIPO_ALIMENTACION_CHOICES = [
        ('Lactancia Materna', 'Lactancia Materna'),
        ('Artificial', 'Artificial'),
        ('Mixta', 'Mixta')
    ]

    neonatal_id = models.AutoField(primary_key=True)
    proposito = models.ForeignKey(
        'Propositos',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    pareja = models.ForeignKey(
        'Parejas',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    peso_nacer = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    talla_nacer = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    circunferencia_cefalica = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cianosis = models.CharField(max_length=100, null=True, blank=True)
    ictericia = models.CharField(max_length=100, null=True, blank=True)
    hemorragia = models.CharField(max_length=100, null=True, blank=True)
    infecciones = models.CharField(max_length=100, null=True, blank=True)
    convulsiones = models.CharField(max_length=100, null=True, blank=True)
    vomitos = models.CharField(max_length=100, null=True, blank=True)
    observacion_complicaciones = models.TextField(null=True, blank=True)
    otros_complicaciones = models.TextField(null=True, blank=True)
    tipo_alimentacion = models.CharField(
        max_length=20,
        choices=TIPO_ALIMENTACION_CHOICES,
        null=True,
        blank=True
    )
    observaciones_alimentacion = models.TextField(null=True, blank=True)
    evolucion = models.TextField(null=True, blank=True)
    observaciones_habitos_psicologicos = models.TextField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(proposito__isnull=False, pareja__isnull=True) |
                    models.Q(proposito__isnull=True, pareja__isnull=False)
                ),
                name='check_periodo_proposito_or_pareja'
            ),
            models.UniqueConstraint(
                fields=['proposito'],
                name='unique_periodo_proposito',
                condition=models.Q(proposito__isnull=False)
            ),
            models.UniqueConstraint(
                fields=['pareja'],
                name='unique_periodo_pareja',
                condition=models.Q(pareja__isnull=False)
            )
        ]

    def clean(self):
        if self.proposito and self.pareja:
            raise ValidationError("El periodo neonatal no puede estar relacionado con un propósito y una pareja al mismo tiempo.")
        if not self.proposito and not self.pareja:
            raise ValidationError("El periodo neonatal debe estar relacionado con un propósito o una pareja.")
        super().clean()

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.proposito:
            return f"Periodo Neonatal de {self.proposito}"
        elif self.pareja:
            return f"Periodo Neonatal de Pareja {self.pareja_id}"
        return f"Periodo Neonatal {self.neonatal_id}"

class Propositos(models.Model):
    # Opciones para el campo de estado
    ESTADO_ACTIVO = 'activo'
    ESTADO_INACTIVO = 'inactivo'
    ESTADO_SEGUIMIENTO = 'en_seguimiento'
    
    ESTADO_CHOICES = [
        (ESTADO_ACTIVO, 'Activo'),
        (ESTADO_INACTIVO, 'Inactivo'),
        (ESTADO_SEGUIMIENTO, 'En Seguimiento'),
    ]

    # Opciones para el campo de sexo
    SEXO_MASCULINO = 'M'
    SEXO_FEMENINO = 'F'
    SEXO_CHOICES = [
        (SEXO_MASCULINO, 'Masculino'),
        (SEXO_FEMENINO, 'Femenino'),
    ]

    proposito_id = models.AutoField(primary_key=True)
    historia = models.ForeignKey('HistoriasClinicas', on_delete=models.CASCADE, null=True, blank=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    sexo = models.CharField(
        max_length=1,
        choices=SEXO_CHOICES,
        verbose_name="Sexo",
        null=True, blank=True # Nullable para registros existentes, se hará requerido en los forms.
    )
    lugar_nacimiento = models.CharField(max_length=100, null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    escolaridad = models.CharField(max_length=100, null=True, blank=True)
    ocupacion = models.CharField(max_length=100, null=True, blank=True)
    edad = models.IntegerField(null=True, blank=True)
    identificacion = models.CharField(max_length=20, unique=True)
    direccion = models.CharField(max_length=200, null=True, blank=True)
    telefono = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    grupo_sanguineo = models.CharField(max_length=2, choices=[('A', 'A'), ('B', 'B'), ('AB', 'AB'), ('O', 'O')], null=True, blank=True)
    factor_rh = models.CharField(max_length=10, choices=[('Positivo', 'Positivo'), ('Negativo', 'Negativo')], null=True, blank=True)
    foto = models.ImageField(upload_to='propositos_fotos/', null=True, blank=True)
    
    # --- CAMPO AÑADIDO ---
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default=ESTADO_ACTIVO, # Por defecto se crea como 'Activo'
        verbose_name="Estado del Propósito"
    )

    def is_minor(self):
        """
        Verifica si el propósito es menor de 18 años.
        Retorna True si es menor, False si es mayor o igual, None si no hay fecha de nacimiento.
        """
        if not self.fecha_nacimiento:
            return None 
        today = date.today()
        age = today.year - self.fecha_nacimiento.year - ((today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))
        return age < 18

    def __str__(self):
        # Actualizamos el __str__ para que muestre el estado
        return f"{self.nombres} {self.apellidos} (ID: {self.identificacion}) - {self.get_estado_display()}"