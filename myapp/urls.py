from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

# It's good practice to define an app_name if you plan to use namespaces
# app_name = 'nombre_de_tu_app' # Example: 'clinica'

urlpatterns = [
    # General/Tutorial paths (consider removing if not part of the clinical app)
    path('', views.index, name="index"), # Main landing page or dashboard
    path('about/', views.about, name="about"),
    path('hello/<str:username>/', views.hello, name="hello_user"), # Added trailing slash
    path('projects/', views.projects, name="project_list"),
    path('projects/create/', views.create_project, name="project_create"), # Changed from create_projecGDFDGt2
    path('projects/<int:id>/', views.project_detail, name="project_detail"), # Added trailing slash
    path('tasks/', views.tasks, name="task_list"),
    path('tasks/create/', views.create_task, name="task_create"),

    # Authentication
    path('signup/', views.signup, name="signup"),
    path('login/', views.login_medico, name="login"), # Consider renaming to just 'login' if it's the only login
    path('logout/', views.signout, name="logout"),

    # Clinical History Core Functionality
    path('historias/crear/', views.crear_historia, name="historia_crear"), # Changed from "historia_clinica"
    path('historias/<int:historia_id>/paciente/crear/', views.crear_paciente, name="paciente_crear"),
    path('historias/<int:historia_id>/pareja/crear/', views.crear_pareja, name="pareja_crear"),
    
    path('historias/<int:historia_id>/proposito/<int:proposito_id>/padres/', views.padres_proposito, name="padres_proposito_crear"),
    
    path('historias/<int:historia_id>/<str:tipo>/<int:objeto_id>/antecedentes-personales/', 
         views.crear_antecedentes_personales, name="antecedentes_personales_crear"),
    path('historias/<int:historia_id>/<str:tipo>/<int:objeto_id>/antecedentes-preconcepcionales/', 
         views.crear_antecedentes_preconcepcionales, name="antecedentes_preconcepcionales_crear"),
    
    path('propositos/<int:proposito_id>/examen-fisico/', views.crear_examen_fisico, name='examen_fisico_crear_editar'),
    path('propositos/<int:proposito_id>/', views.ver_proposito, name='proposito_detalle'), # Changed from 'ver_proposito'
    
    path('historias/<int:historia_id>/<str:tipo>/<int:objeto_id>/evaluacion-genetica/', 
         views.diagnosticos_plan_estudio, name='evaluacion_genetica_detalle'), # Changed from 'diagnosticos_plan'

    # AJAX / Search
    path('ajax/buscar-propositos/', views.buscar_propositos, name='ajax_buscar_propositos'), # Clarified AJAX path

    # Reports & Management
    path('reports/', views.reports_view, name="reports_dashboard"),
     path('reports/export/<str:export_format>/', views.export_report_data, name='export_report_data'),
    path('gestion-usuarios/', views.gestion_usuarios_view, name="gestion_usuarios_dashboard"), # Added trailing slash for consistency

]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)