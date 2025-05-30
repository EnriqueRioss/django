from django.contrib import admin
from .models import Project, Task, AntecedentesFamiliaresPreconcepcionales,Autorizaciones,AntecedentesPersonales,PeriodoNeonatal,Propositos,DesarrolloPsicomotor,InformacionPadres,EvolucionDesarrollo,Genealogia,Genetistas,HistorialCambios,HistoriasClinicas,Parejas,ExamenFisico,PlanEstudio,DiagnosticoPresuntivo,EvaluacionGenetica


# Readers
class Dateread(admin.ModelAdmin):
    readonly_fields =("fecha_ingreso", )
    
class Dateexamen(admin.ModelAdmin):
    readonly_fields =("fecha_examen" ,)
# Register your models here.
admin.site.register(AntecedentesFamiliaresPreconcepcionales)
admin.site.register(Autorizaciones)
admin.site.register(AntecedentesPersonales)
admin.site.register(PeriodoNeonatal)
admin.site.register(Propositos)
admin.site.register(DesarrolloPsicomotor)
admin.site.register(InformacionPadres)
admin.site.register(PlanEstudio)
admin.site.register(DiagnosticoPresuntivo)
admin.site.register(EvaluacionGenetica)
admin.site.register(ExamenFisico,Dateexamen)
admin.site.register(EvolucionDesarrollo)
admin.site.register(Genealogia)
admin.site.register(Genetistas)
admin.site.register(HistorialCambios)
admin.site.register(HistoriasClinicas,Dateread)
admin.site.register(Project)
admin.site.register(Parejas)
admin.site.register(Task)