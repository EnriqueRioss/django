from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index, name ="index"),
    path('about/', views.about, name ="about"),
    path('hello/<str:username>', views.hello, name ="hello"),
    path('projects/', views.projects, name="projects"),
    path('projects/<int:id>', views.project_detail, name="project_detail"),
    path("tasks/", views.tasks, name="tasks"),
    path("create_task/", views.create_task, name="create_task"),
    path("create_projecGDFDGt2/", views.create_project,name="create_project"),




    path('signup/', views.signup, name ="signup"),
    path('login/', views.login_medico, name ="login"),
    path('logout/', views.signout, name ="logout"),
    path("historia_clinica/", views.crear_historia,name="historia_clinica"),
    path("crear_paciente/<int:historia_id>/", views.crear_paciente, name="crear_paciente"),
    path("crear_pareja/<int:historia_id>/", views.crear_pareja, name="crear_pareja"),
    path("padres_proposito/<int:historia_id>/<int:proposito_id>", views.padres_proposito, name="padres_proposito"),
    path("antecedentes_personales/<int:historia_id>/<str:tipo>/<int:objeto_id>", views.crear_antecedentes_personales, name="antecedentes_personales"),
     path("antecedentes_preconcepcionales/<int:historia_id>/<str:tipo>/<int:objeto_id>", views.crear_antecedentes_preconcepcionales, name="antecedentes_preconcepcionales"),
    path('propositos/<int:proposito_id>/examen-fisico/', views.crear_examen_fisico, name='examen_fisico'),
    path('buscar-propositos/', views.buscar_propositos, name='buscar_propositos'),
   path('propositos/<int:proposito_id>/', views.ver_proposito, name='ver_proposito')

    

    


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
