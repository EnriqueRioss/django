from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User

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
        return f"Examen Físico {self.examen_id} para {self.proposito_id}"

class Parejas(models.Model):
    pareja_id = models.AutoField(primary_key=True)
    proposito_id_1 = models.ForeignKey('Propositos', on_delete=models.CASCADE, related_name='proposito_1')
    proposito_id_2 = models.ForeignKey('Propositos', on_delete=models.CASCADE, related_name='proposito_2')

    class Meta:
        # Esto asegura que no se puedan crear parejas duplicadas con los mismos proposito_id_1 y proposito_id_2
        unique_together = (('proposito_id_1', 'proposito_id_2'),)

    def __str__(self):
        return f"Pareja {self.pareja_id}: {self.proposito_id_1} y {self.proposito_id_2}"


class AntecedentesFamiliaresPreconcepcionales(models.Model):
    antecedente_familiar_id = models.AutoField(primary_key=True)
    
    # Relación con Proposito (individual)
    proposito = models.ForeignKey(
        'Propositos', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        unique=False  # Quitamos unique aquí porque lo manejaremos con constraints
    )
    
    # Relación con Pareja
    pareja = models.ForeignKey(
        'Parejas',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        unique=False  # Quitamos unique aquí porque lo manejaremos con constraints
    )
    
    # Campos del modelo
    antecedentes_padre = models.TextField(null=True, blank=True)
    antecedentes_madre = models.TextField(null=True, blank=True)
    estado_salud_padre = models.TextField(null=True, blank=True)
    estado_salud_madre = models.TextField(null=True, blank=True)
    fecha_union_pareja = models.DateField(null=True, blank=True)
    consanguinidad = models.CharField(max_length=2, choices=[('Sí', 'Sí'), ('No', 'No')], null=True, blank=True)
    grado_consanguinidad = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        constraints = [
            # Asegura que solo se relacione con un Proposito o una Pareja, no ambos
            models.CheckConstraint(
                check=(
                    models.Q(proposito__isnull=False, pareja__isnull=True) | 
                    models.Q(proposito__isnull=True, pareja__isnull=False)
                ),
                name='check_proposito_or_pareja'
            ),
            # Asegura que no haya duplicados para un Proposito
            models.UniqueConstraint(
                fields=['proposito'],
                name='unique_antecedente_proposito',
                condition=models.Q(proposito__isnull=False)
            ),
            # Asegura que no haya duplicados para una Pareja
            models.UniqueConstraint(
                fields=['pareja'],
                name='unique_antecedente_pareja',
                condition=models.Q(pareja__isnull=False)
            )
        ]

    def clean(self):
        # Validación adicional a nivel de modelo
        if self.proposito and self.pareja:
            raise ValidationError("Los antecedentes no pueden estar relacionados con un propósito y una pareja al mismo tiempo.")
        if not self.proposito and not self.pareja:
            raise ValidationError("Los antecedentes deben estar relacionados con un propósito o una pareja.")

    def save(self, *args, **kwargs):
        self.clean()  # Ejecuta las validaciones
        super().save(*args, **kwargs)

    def __str__(self):
        if self.proposito:
            return f"Antecedentes Familiares de {self.proposito}"
        elif self.pareja:
            return f"Antecedentes Familiares de Pareja {self.pareja}"
        return f"Antecedente Familiar {self.antecedente_familiar_id}"

class AntecedentesPersonales(models.Model):
    antecedente_id = models.AutoField(primary_key=True)
    
    # Relación con Proposito (individual)
    proposito = models.ForeignKey(
        'Propositos', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    
    # Relación con Pareja
    pareja = models.ForeignKey(
        'Parejas',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    
    # Campos del modelo
    fur = models.DateField(null=True, blank=True)
    edad_gestacional = models.IntegerField(null=True, blank=True)
    controles_prenatales = models.CharField(max_length=100)
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
            # Asegura que solo se relacione con un Proposito o una Pareja, no ambos
            models.CheckConstraint(
                check=(
                    models.Q(proposito__isnull=False, pareja__isnull=True) | 
                    models.Q(proposito__isnull=True, pareja__isnull=False)
                ),
                name='check_proposito_or_pareja_personales'
            ),
            # Asegura que no haya duplicados para un Proposito
            models.UniqueConstraint(
                fields=['proposito'],
                name='unique_antecedente_personal_proposito',
                condition=models.Q(proposito__isnull=False)
            ),
            # Asegura que no haya duplicados para una Pareja
            models.UniqueConstraint(
                fields=['pareja'],
                name='unique_antecedente_personal_pareja',
                condition=models.Q(pareja__isnull=False)
            )
        ]

    def clean(self):
        # Validación adicional a nivel de modelo
        if self.proposito and self.pareja:
            raise ValidationError("Los antecedentes personales no pueden estar relacionados con un propósito y una pareja al mismo tiempo.")
        if not self.proposito and not self.pareja:
            raise ValidationError("Los antecedentes personales deben estar relacionados con un propósito o una pareja.")

    def save(self, *args, **kwargs):
        self.clean()  # Ejecuta las validaciones
        super().save(*args, **kwargs)

    def __str__(self):
        if self.proposito:
            return f"Antecedentes Personales de {self.proposito}"
        elif self.pareja:
            return f"Antecedentes Personales de Pareja {self.pareja}"
        return f"Antecedente Personal {self.antecedente_id}"

class Autorizaciones(models.Model):
    autorizacion_id = models.AutoField(primary_key=True)
    proposito = models.ForeignKey('Propositos', on_delete=models.CASCADE, null=True, blank=True, unique=True)
    autorizacion_examenes = models.BooleanField(null=True, blank=True)
    archivo_autorizacion = models.FileField(null=True, blank=True)
    padre = models.ForeignKey('InformacionPadres', on_delete=models.CASCADE, null=True, blank=True, unique=True)

    def __str__(self):
        return f"Autorizacion {self.autorizacion_id}"

class DesarrolloPsicomotor(models.Model):
    desarrollo_id = models.AutoField(primary_key=True)
    
    # Relación con Proposito (individual)
    proposito = models.ForeignKey(
        'Propositos', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    
    # Relación con Pareja
    pareja = models.ForeignKey(
        'Parejas',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    
    # Campos del modelo
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
            # Asegura que solo se relacione con un Proposito o una Pareja, no ambos
            models.CheckConstraint(
                check=(
                    models.Q(proposito__isnull=False, pareja__isnull=True) | 
                    models.Q(proposito__isnull=True, pareja__isnull=False)
                ),
                name='check_desarrollo_proposito_or_pareja'
            ),
            # Asegura que no haya duplicados para un Proposito
            models.UniqueConstraint(
                fields=['proposito'],
                name='unique_desarrollo_proposito',
                condition=models.Q(proposito__isnull=False)
            ),
            # Asegura que no haya duplicados para una Pareja
            models.UniqueConstraint(
                fields=['pareja'],
                name='unique_desarrollo_pareja',
                condition=models.Q(pareja__isnull=False)
            )
        ]

    def clean(self):
        # Validación adicional a nivel de modelo
        if self.proposito and self.pareja:
            raise ValidationError("El desarrollo psicomotor no puede estar relacionado con un propósito y una pareja al mismo tiempo.")
        if not self.proposito and not self.pareja:
            raise ValidationError("El desarrollo psicomotor debe estar relacionado con un propósito o una pareja.")

    def save(self, *args, **kwargs):
        self.clean()  # Ejecuta las validaciones
        super().save(*args, **kwargs)

    def __str__(self):
        if self.proposito:
            return f"Desarrollo Psicomotor de {self.proposito}"
        elif self.pareja:
            return f"Desarrollo Psicomotor de Pareja {self.pareja}"
        return f"Desarrollo Psicomotor {self.desarrollo_id}"

class DiagnosticosPlanEstudio(models.Model):
    diagnostico_id = models.AutoField(primary_key=True)
    proposito = models.ForeignKey('Propositos', on_delete=models.CASCADE, null=True, blank=True,unique=True)
    signos_clinicos = models.TextField(null=True, blank=True)
    enfermedad_actual = models.TextField(null=True, blank=True)
    diagnostico_presuntivo_1 = models.TextField(null=True, blank=True)
    diagnostico_presuntivo_2 = models.TextField(null=True, blank=True)
    diagnostico_presuntivo_3 = models.TextField(null=True, blank=True)
    plan_estudio = models.TextField(null=True, blank=True)
    diagnostico_confirmado = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Diagnostico {self.diagnostico_id}"



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
        return f"Evolucion Desarrollo {self.evolucion_id}"

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
        # otros según necesidad
    ]
    
    genealogia_id = models.AutoField(primary_key=True)
    
    # Relación con Proposito (puede ser null si está relacionado con pareja)
    proposito = models.ForeignKey(
        'Propositos', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='genealogia_proposito'
    )
    
    # Relación con Pareja (puede ser null si está relacionado con proposito individual)
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
            # Asegura que cada registro esté relacionado con un propósito O una pareja, pero no ambos
            models.CheckConstraint(
                check=(
                    models.Q(proposito__isnull=False, pareja__isnull=True) | 
                    models.Q(proposito__isnull=True, pareja__isnull=False)
                ),
                name='proposito_or_pareja'
            )
        ]
    
    def __str__(self):
        return f"{self.nombres} {self.apellidos} ({self.get_tipo_familiar_display()})"
    
    def clean(self):
        """
        Validación adicional para asegurar que solo un tipo de relación esté establecido
        """
        super().clean()
        if self.proposito and self.pareja:
            raise ValidationError("Un registro de genealogía debe estar relacionado con un propósito O una pareja, no ambos.")
        if not self.proposito and not self.pareja:
            raise ValidationError("Un registro de genealogía debe estar relacionado con un propósito o una pareja.")
        
        # Validación adicional para el tipo_familiar
        if self.tipo_familiar == 'pareja' and not self.pareja:
            raise ValidationError("El tipo 'pareja' debe estar asociado a un registro de Pareja.")
        if self.tipo_familiar == 'proposito' and not self.proposito:
            raise ValidationError("El tipo 'proposito' debe estar asociado a un Proposito individual.")

class Genetistas(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    genetista_id = models.AutoField(primary_key=True)

    def __str__(self):
        return f"Genetista de {self.genetista_id}"

class HistorialCambios(models.Model):
    cambio_id = models.AutoField(primary_key=True)
    historia = models.ForeignKey('HistoriasClinicas', on_delete=models.CASCADE, null=True, blank=True)
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    descripcion_cambio = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Historial Cambio {self.cambio_id}"

class HistoriasClinicas(models.Model):
    historia_id = models.AutoField(primary_key=True)
    numero_historia = models.IntegerField(unique=True)
    fecha_ingreso = models.DateTimeField(auto_now_add=True)
    motivo_tipo_consulta = models.CharField(max_length=35, choices=[('Pareja-Asesoramiento Prenupcial', 'Pareja-Asesoramiento Prenupcial'), ('Pareja-Preconcepcional', 'Pareja-Preconcepcional'), ('Pareja-Prenatal', 'Pareja-Prenatal'), ('Proposito-Diagnóstico', 'Proposito-Diagnóstico')])  # Cambiado a 24
    genetista = models.ForeignKey('Genetistas', on_delete=models.CASCADE, null=True, blank=True)
    cursante_postgrado = models.CharField(max_length=100, null=True, blank=True)
    centro_referencia = models.CharField(max_length=100, null=True, blank=True)
    medico = models.CharField(max_length=100, null=True, blank=True)
    especialidad = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Historia Clinica {self.historia_id}"

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
    identificacion = models.CharField(max_length=20, null=True, blank=True)
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
        # Validación para asegurar que solo haya un padre y una madre por propósito
        padres = InformacionPadres.objects.filter(proposito=self.proposito)
        
        # Verificar si ya existe un padre o una madre del mismo tipo
        if self.tipo == 'Padre' and padres.filter(tipo='Padre').exists():
            raise ValidationError('Ya existe un padre para este propósito.')
        if self.tipo == 'Madre' and padres.filter(tipo='Madre').exists():
            raise ValidationError('Ya existe una madre para este propósito.')
        
        # Verificar que no haya más de dos padres (un papá y una mamá)
        if padres.count() >= 2:
            raise ValidationError('Un propósito solo puede tener dos padres (un papá y una mamá).')

    def save(self, *args, **kwargs):
        # Ejecutar la validación antes de guardar
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Informacion Padre {self.padre_id}"


class PeriodoNeonatal(models.Model):
    TIPO_ALIMENTACION_CHOICES = [
        ('Lactancia Materna', 'Lactancia Materna'),
        ('Artificial', 'Artificial'),
        ('Mixta', 'Mixta')
    ]
    
    neonatal_id = models.AutoField(primary_key=True)
    
    # Relación con Proposito (individual)
    proposito = models.ForeignKey(
        'Propositos',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    
    # Relación con Pareja
    pareja = models.ForeignKey(
        'Parejas',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    
    # Campos del modelo
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
            # Asegura que solo se relacione con un Proposito o una Pareja, no ambos
            models.CheckConstraint(
                check=(
                    models.Q(proposito__isnull=False, pareja__isnull=True) | 
                    models.Q(proposito__isnull=True, pareja__isnull=False)
                ),
                name='check_periodo_proposito_or_pareja'
            ),
            # Asegura que no haya duplicados para un Proposito
            models.UniqueConstraint(
                fields=['proposito'],
                name='unique_periodo_proposito',
                condition=models.Q(proposito__isnull=False)
            ),
            # Asegura que no haya duplicados para una Pareja
            models.UniqueConstraint(
                fields=['pareja'],
                name='unique_periodo_pareja',
                condition=models.Q(pareja__isnull=False)
            )
        ]

    def clean(self):
        # Validación adicional a nivel de modelo
        if self.proposito and self.pareja:
            raise ValidationError("El periodo neonatal no puede estar relacionado con un propósito y una pareja al mismo tiempo.")
        if not self.proposito and not self.pareja:
            raise ValidationError("El periodo neonatal debe estar relacionado con un propósito o una pareja.")

    def save(self, *args, **kwargs):
        self.clean()  # Ejecuta las validaciones
        super().save(*args, **kwargs)

    def __str__(self):
        if self.proposito:
            return f"Periodo Neonatal de {self.proposito}"
        elif self.pareja:
            return f"Periodo Neonatal de Pareja {self.pareja}"
        return f"Periodo Neonatal {self.neonatal_id}"

class Propositos(models.Model):
    proposito_id = models.AutoField(primary_key=True)
    historia = models.ForeignKey('HistoriasClinicas', on_delete=models.CASCADE, null=True, blank=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    lugar_nacimiento = models.CharField(max_length=100, null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    escolaridad = models.CharField(max_length=100, null=True, blank=True)
    ocupacion = models.CharField(max_length=100, null=True, blank=True)
    edad = models.IntegerField(null=True, blank=True)
    identificacion = models.CharField(max_length=20, unique=True)
    # documento_nacimiento = models.BinaryField(null=True, blank=True)
    direccion = models.CharField(max_length=200, null=True, blank=True)
    telefono = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    grupo_sanguineo = models.CharField(max_length=2, choices=[('A', 'A'), ('B', 'B'), ('AB', 'AB'), ('O', 'O')], null=True, blank=True)
    factor_rh = models.CharField(max_length=10, choices=[('Positivo', 'Positivo'), ('Negativo', 'Negativo')], null=True, blank=True)
    foto = models.ImageField(upload_to='propositos_fotos/', null=True, blank=True)

    def __str__(self):
        return f"Proposito {self.proposito_id}"