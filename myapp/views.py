from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from .models import Project, Task, Project
from django.shortcuts import get_object_or_404, render, redirect, get_object_or_404
from .forms import CreateNewTask, CreateNewProject, LoginForm
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login,authenticate,logout
from django.db import IntegrityError
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.db import IntegrityError
from .forms import ExtendedUserCreationForm, HistoriasForm , PropositosForm, PadresPropositoForm, AntecedentesDesarrolloNeonatalForm ,AntecedentesPreconcepcionalesForm, ExamenFisicoForm, ParejaPropositosForm, DiagnosticosPlanEstudioForm, DiagnosticoPresuntivoFormSet
from .models import Genetistas, Propositos, HistoriasClinicas ,InformacionPadres, ExamenFisico,Parejas, AntecedentesPersonales, DiagnosticosPlanEstudio, DiagnosticoPresuntivo
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.core import serializers
import json
from django.utils import timezone
from django.db import transaction
# Create your views here.


def index(request):
    title = "Django hola q tal"
    return render(request, "index.html", {
        'title': title
    })

@login_required  
def crear_historia(request):
    if request.method == 'GET':
        return render(request, "historia_clinica.html", {'form1': HistoriasForm})
    elif request.method == 'POST':
        form = HistoriasForm(request.POST)
        if form.is_valid():
            # Obtener el usuario autenticado
            usuario = request.user

            # Obtener el genetista asociado al usuario
            try:
                genetista = Genetistas.objects.get(user=usuario)
            except Genetistas.DoesNotExist:
                # Manejar el caso en que el usuario no tenga un genetista asociado
                return render(request, 'error.html', {'mensaje': 'El usuario no tiene un genetista asociado.'})

            # Crear la historia clínica sin guardarla aún
            historia = form.save(commit=False)
           
            # Asignar el genetista a la historia clínica
            historia.genetista = genetista
    
            # Guardar la historia clínica en la base de datos
            historia.save()
            motivo_tipo_consulta = form.cleaned_data['motivo_tipo_consulta']
            
            if motivo_tipo_consulta == 'Proposito-Diagnóstico':
                return redirect('crear_paciente', historia_id=historia.historia_id)  # Redirige a la vista para diagnóstico
            elif motivo_tipo_consulta == 'Pareja-Asesoramiento Prenupcial':
                return redirect('crear_pareja', historia_id=historia.historia_id) # Redirige a la vista para asesoramiento prenupcial
            elif motivo_tipo_consulta == 'Pareja-Preconcepcional':
                return redirect('crear_pareja', historia_id=historia.historia_id) # Redirige a la vista para preconcepcional
            elif motivo_tipo_consulta == 'Pareja-Prenatal':
                return redirect('crear_pareja', historia_id=historia.historia_id)  # Redirige a la vista para prenatal
            else:
                # Redirigir a una vista por defecto si no coincide con ningún caso
                return redirect('historia_clinica')
        
        else:
            # Si el formulario no es válido, mostrar el formulario con errores
            return render(request, "historia_clinica.html", {'form1': form})
        
def get_ultimos_propositos(request):
    if request.user.is_authenticated:
        try:
            genetista = request.user.genetistas
            ultimos_propositos = Propositos.objects.select_related('historia').filter(
                historia__genetista=genetista
            ).order_by('-historia__fecha_ingreso')[:3]
            return ultimos_propositos
        except Genetistas.DoesNotExist:
            return Propositos.objects.none()
    return Propositos.objects.none()

@login_required
def crear_paciente(request, historia_id):
    # Obtener la historia clínica asociada
    try:
        historia = HistoriasClinicas.objects.get(historia_id=historia_id)
    except HistoriasClinicas.DoesNotExist:
        return render(request, 'error.html', {'mensaje': 'La historia clínica no existe.'})

    if request.method == 'GET':
        # Mostrar el formulario vacío
        return render(request, "Crear_paciente.html", {'form': PropositosForm()})
    
    elif request.method == 'POST':
        form = PropositosForm(request.POST, request.FILES)
        if form.is_valid():
            # Guardar el propósito en la base de datos
            proposito = form.save(historia)
            return redirect('padres_proposito', historia_id=historia.historia_id, proposito_id=proposito.proposito_id)
        else:
            # Si el formulario no es válido, mostrar el formulario con errores
            return render(request, "Crear_paciente.html", {'form': form})
    
    else:
        return render(request, 'error.html', {'mensaje': 'Método no permitido.'})
    


@login_required
def crear_pareja(request, historia_id):
    try:
        historia = HistoriasClinicas.objects.get(historia_id=historia_id)
    except HistoriasClinicas.DoesNotExist:
        return render(request, 'error.html', {'mensaje': 'La historia clínica no existe.'})

    if request.method == 'POST':
        form = ParejaPropositosForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Usamos transaction.atomic para asegurar que ambos propositos se creen o ninguno
                with transaction.atomic():
                    # Crear primer proposito (conyugue 1)
                    proposito1 = Propositos(
                        historia=historia,
                        nombres=form.cleaned_data['nombres_1'],
                        apellidos=form.cleaned_data['apellidos_1'],
                        lugar_nacimiento=form.cleaned_data['lugar_nacimiento_1'],
                        fecha_nacimiento=form.cleaned_data['fecha_nacimiento_1'],
                        escolaridad=form.cleaned_data['escolaridad_1'],
                        ocupacion=form.cleaned_data['ocupacion_1'],
                        edad=form.cleaned_data['edad_1'],
                        identificacion=form.cleaned_data['identificacion_1'],
                        direccion=form.cleaned_data['direccion_1'],
                        telefono=form.cleaned_data['telefono_1'],
                        email=form.cleaned_data['email_1'],
                        grupo_sanguineo=form.cleaned_data['grupo_sanguineo_1'],
                        factor_rh=form.cleaned_data['factor_rh_1'],
                        foto=form.cleaned_data['foto_1']
                    )
                    proposito1.save()

                    # Crear segundo proposito (conyugue 2)
                    proposito2 = Propositos(
                        historia=historia,
                        nombres=form.cleaned_data['nombres_2'],
                        apellidos=form.cleaned_data['apellidos_2'],
                        lugar_nacimiento=form.cleaned_data['lugar_nacimiento_2'],
                        fecha_nacimiento=form.cleaned_data['fecha_nacimiento_2'],
                        escolaridad=form.cleaned_data['escolaridad_2'],
                        ocupacion=form.cleaned_data['ocupacion_2'],
                        edad=form.cleaned_data['edad_2'],
                        identificacion=form.cleaned_data['identificacion_2'],
                        direccion=form.cleaned_data['direccion_2'],
                        telefono=form.cleaned_data['telefono_2'],
                        email=form.cleaned_data['email_2'],
                        grupo_sanguineo=form.cleaned_data['grupo_sanguineo_2'],
                        factor_rh=form.cleaned_data['factor_rh_2'],
                        foto=form.cleaned_data['foto_2']
                    )
                    proposito2.save()

                    # Crear la relación de pareja
                    pareja = Parejas(
                        proposito_id_1=proposito1,
                        proposito_id_2=proposito2
                    )
                    pareja.save()

                return redirect('antecedentes_personales', 
                                 historia_id=historia.historia_id,
                                 tipo = "pareja",
                                 objeto_id=pareja.pareja_id)
            
            except Exception as e:
                # Manejar cualquier error durante la creación
                return render(request, 'error.html', {'mensaje': f'Error al guardar la pareja: {str(e)}'})
    else:
        form = ParejaPropositosForm()

    return render(request, 'Crear_pareja.html', {
        'form': form,
        'historia': historia
    })




def buscar_propositos(request):
    query = request.GET.get('q', '')
    
    if request.user.is_authenticated:
        try:
            genetista = request.user.genetistas
            if query:
                propositos = Propositos.objects.select_related('historia').filter(
                    Q(nombres__icontains=query) | 
                    Q(apellidos__icontains=query) |
                    Q(identificacion__icontains=query),
                    historia__genetista=genetista
                ).order_by('-historia__fecha_ingreso')[:10]
            else:
                propositos = get_ultimos_propositos(request)
        except Genetistas.DoesNotExist:
            propositos = Propositos.objects.none()
    else:
        propositos = Propositos.objects.none()
    
    resultados = []
    for proposito in propositos:
        resultados.append({
            'proposito_id': proposito.proposito_id,
            'nombres': proposito.nombres,
            'apellidos': proposito.apellidos,
            'edad': proposito.edad,
            'direccion': proposito.direccion,
            'identificacion': proposito.identificacion,
            'foto': proposito.foto.url if proposito.foto else None,
            'fecha_ingreso': proposito.historia.fecha_ingreso.strftime("%d/%m/%Y %H:%M") if proposito.historia.fecha_ingreso else "--"
        })
    
    return JsonResponse({'propositos': resultados})


@login_required
def padres_proposito(request, historia_id, proposito_id):
    # Obtener el propósito asociado
    try:
        historia = HistoriasClinicas.objects.get(historia_id=historia_id)
        proposito = Propositos.objects.get(proposito_id=proposito_id)
    except Propositos.DoesNotExist:
        return render(request, 'error.html', {'mensaje': 'El propósito no existe.'})

    if request.method == 'GET':
        # Mostrar el formulario vacío
        return render(request, "Padres_proposito.html", {'form': PadresPropositoForm()})
    
    elif request.method == 'POST':
        form = PadresPropositoForm(request.POST)
        if form.is_valid():
            # Crear el registro del padre
            padre = InformacionPadres(
                proposito=proposito,
                tipo='Padre',
                nombres=form.cleaned_data['padre_nombres'],
                apellidos=form.cleaned_data['padre_apellidos'],
                escolaridad=form.cleaned_data['padre_escolaridad'],
                ocupacion=form.cleaned_data['padre_ocupacion'],
                lugar_nacimiento=form.cleaned_data['padre_lugar_nacimiento'],
                fecha_nacimiento=form.cleaned_data['padre_fecha_nacimiento'],
                edad=form.cleaned_data['padre_edad'],
                identificacion=form.cleaned_data['padre_identificacion'],
                grupo_sanguineo=form.cleaned_data['padre_grupo_sanguineo'],
                factor_rh=form.cleaned_data['padre_factor_rh'],
                telefono=form.cleaned_data['padre_telefono'],
                email=form.cleaned_data['padre_email'],
                direccion=form.cleaned_data['padre_direccion']
            )
            padre.save()

            # Crear el registro de la madre
            madre = InformacionPadres(
                proposito=proposito,
                tipo='Madre',
                nombres=form.cleaned_data['madre_nombres'],
                apellidos=form.cleaned_data['madre_apellidos'],
                escolaridad=form.cleaned_data['madre_escolaridad'],
                ocupacion=form.cleaned_data['madre_ocupacion'],
                lugar_nacimiento=form.cleaned_data['madre_lugar_nacimiento'],
                fecha_nacimiento=form.cleaned_data['madre_fecha_nacimiento'],
                edad=form.cleaned_data['madre_edad'],
                identificacion=form.cleaned_data['madre_identificacion'],
                grupo_sanguineo=form.cleaned_data['madre_grupo_sanguineo'],
                factor_rh=form.cleaned_data['madre_factor_rh'],
                telefono=form.cleaned_data['madre_telefono'],
                email=form.cleaned_data['madre_email'],
                direccion=form.cleaned_data['madre_direccion']
            )
            madre.save()

            return redirect('antecedentes_personales', 
                historia_id=historia_id,
                tipo='proposito',  # o el valor adecuado para tu caso
                objeto_id=proposito_id) # Redirigir a alguna vista después de guardar
        else:
            # Si el formulario no es válido, imprimir los errores en la consola
            print("Errores del formulario:", form.errors)
            
            # Mostrar el formulario con errores en la plantilla
            return render(request, "Padres_proposito.html", {'form': form, 'errors': form.errors})
    
    else:
        return render(request, 'error.html', {'mensaje': 'Método no permitido.'})




@login_required
def crear_antecedentes_personales(request, historia_id, tipo, objeto_id):
    try:
        # Primero verificar que la historia existe
        historia = HistoriasClinicas.objects.get(historia_id=historia_id)
        
        if tipo == 'proposito':
            try:
                proposito = Propositos.objects.get(proposito_id=objeto_id)
                pareja = None
            except Propositos.DoesNotExist:
                return render(request, 'error.html', {'mensaje': 'No se encontró el propósito.'})
        elif tipo == 'pareja':
            try:
                pareja = Parejas.objects.get(pareja_id=objeto_id)
                proposito = None
            except Parejas.DoesNotExist:
                return render(request, 'error.html', {'mensaje': 'No se encontró la pareja.'})
        else:
            return render(request, 'error.html', {'mensaje': 'Tipo no válido.'})
        
        # Verificar si ya existen antecedentes para evitar duplicados
        if tipo == 'proposito' and AntecedentesPersonales.objects.filter(proposito=proposito).exists():
            return redirect('antecedentes_preconcepcionales', 
                          historia_id=historia_id,
                          tipo = "proposito",
                          objeto_id=objeto_id)
        elif tipo == 'pareja' and AntecedentesPersonales.objects.filter(pareja=pareja).exists():
            return redirect('antecedentes_preconcepcionales', 
                          historia_id=historia_id,
                          tipo = "pareja",
                          objeto_id=objeto_id)

    except HistoriasClinicas.DoesNotExist:
        return render(request, 'error.html', {'mensaje': 'La historia clínica no existe.'})

    if request.method == 'POST':
        form = AntecedentesDesarrolloNeonatalForm(request.POST)
        if form.is_valid():
            try:
                # Guardar los antecedentes según el tipo
                if tipo == 'proposito':
                    antecedentes, desarrollo, neonatal = form.save(proposito=proposito)
                    return redirect('antecedentes_preconcepcionales',
                                  historia_id=historia.historia_id, 
                                  tipo = "proposito",
                                  objeto_id=proposito.proposito_id)
                else:  # tipo == 'pareja'
                    antecedentes, desarrollo, neonatal = form.save(pareja=pareja)
                    return redirect('antecedentes_preconcepcionales',
                                  historia_id=historia.historia_id,
                                  tipo = "pareja",
                                 objeto_id=pareja.pareja_id)
            
            except Exception as e:
                return render(request, 'error.html', {'mensaje': f'Error al guardar: {str(e)}'})
        else:
            return render(request, 'antecedentes_personales.html', {
                'form': form,
                'historia': historia,
                'tipo': tipo,
                'objeto': proposito if tipo == 'proposito' else pareja
            })
    
    else:  # GET request
        form = AntecedentesDesarrolloNeonatalForm()
        return render(request, 'antecedentes_personales.html', {
            'form': form,
            'historia': historia,
            'tipo': tipo,
            'objeto': proposito if tipo == 'proposito' else pareja
        })
    

@login_required
def crear_antecedentes_preconcepcionales(request, historia_id, tipo, objeto_id):
    try:
        # Primero verificar que la historia existe
        historia = HistoriasClinicas.objects.get(historia_id=historia_id)
        
        if tipo == 'proposito':
            try:
                proposito = Propositos.objects.get(proposito_id=objeto_id)
                pareja = None
            except Propositos.DoesNotExist:
                return render(request, 'error.html', {'mensaje': 'No se encontró el propósito.'})
        elif tipo == 'pareja':
            try:
                pareja = Parejas.objects.get(pareja_id=objeto_id)
                proposito = None
            except Parejas.DoesNotExist:
                return render(request, 'error.html', {'mensaje': 'No se encontró la pareja.'})
        else:
            return render(request, 'error.html', {'mensaje': 'Tipo no válido.'})
        
    except HistoriasClinicas.DoesNotExist:
        return render(request, 'error.html', {'mensaje': 'La historia clínica no existe.'})

    if request.method == 'POST':
        form = AntecedentesPreconcepcionalesForm(request.POST)
        if form.is_valid():
            try:
                antecedentespre = form.save(proposito=proposito, pareja=pareja, tipo=tipo)
                return redirect('diagnosticos_plan')
            except Exception as e:
                return render(request, 'error.html', {'mensaje': f'Error al guardar: {str(e)}'})
        else:
            return render(request, 'antecedentes_preconcepcionales.html', {
                'form': form,
                'errors': form.errors,
                'historia': historia,
                'tipo': tipo,
                'objeto': proposito if tipo == 'proposito' else pareja
            })
    else:
        form = AntecedentesPreconcepcionalesForm()
        return render(request, 'antecedentes_preconcepcionales.html', {
            'form': form,
            'historia': historia,
            'tipo': tipo,
            'objeto': proposito if tipo == 'proposito' else pareja
        })

def signup(request):
    if request.method == 'GET':
        return render(request, "signup.html", {
            'form': ExtendedUserCreationForm()  # Usar el formulario extendido
        })
    else:
        form = ExtendedUserCreationForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['password1'] == form.cleaned_data['password2']:
                try:
                    # Crear el usuario
                    user = User.objects.create_user(
                        username=form.cleaned_data['username'],
                        password=form.cleaned_data['password1'],
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        email=form.cleaned_data['email']
                    )
                    user.save()

                    # Crear el perfil de genetista
                    genetista = Genetistas(user=user)
                    genetista.save()

                    # Iniciar sesión y redirigir
                    login(request, user)
                    return redirect('tasks')
                except IntegrityError:
                    return render(request, "signup.html", {
                        'form': form,
                        "error": 'El nombre de usuario ya existe'
                    })
            else:
                return render(request, "signup.html", {
                    'form': form,
                    "error": 'Las contraseñas no coinciden'
                })
        else:
            return render(request, "signup.html", {
                'form': form,
                "error": 'Por favor, corrige los errores en el formulario'
            })

     
def login_medico(request):
    if request.method == 'GET':
        return render(request,"login.html",{
        'form' : AuthenticationForm
    })
    else:
      form = LoginForm(request.POST)
      if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is  None:
               return render (request, 'login.html', {
                   'form' : AuthenticationForm,
                   'error' : 'Username or password is incorrect'
               })
            else:
                login(request, user)
                return redirect ('index')
   
def signout(request):
    logout(request)
    return redirect('login')


@login_required 
def crear_examen_fisico(request, proposito_id):
    proposito = get_object_or_404(Propositos, pk=proposito_id)
    examen_existente = ExamenFisico.objects.filter(proposito=proposito).first()
    
    if request.method == 'POST':
        form = ExamenFisicoForm(request.POST, instance=examen_existente)
        form.proposito = proposito  # Asigna el propósito al formulario
        
        if form.is_valid():
            examen = form.save()  # Ahora funciona con commit=False o sin él
            return redirect('ver_proposito', proposito_id=proposito_id)
        else:
            return render(request, 'examen_fisico.html', {
                'form': form,
                'errors': form.errors,
                'proposito': proposito,
                'editing': bool(examen_existente)
            })
       
    else:
        if examen_existente:
            # Si existe, mostramos el formulario en modo edición
            form = ExamenFisicoForm(instance=examen_existente)
            return render(request, 'examen_fisico.html', {
                'form': form,
                'proposito': proposito,
                'editing': True
            })
        else:
            # Si no existe, mostramos formulario vacío
            form = ExamenFisicoForm()
            return render(request, 'examen_fisico.html', {
                'form': form,
                'proposito': proposito,
                'editing': False
            })

def ver_proposito(request, proposito_id):
    proposito = get_object_or_404(Propositos, pk=proposito_id)
    examen_fisico = ExamenFisico.objects.filter(proposito=proposito).first()
    if request.method == 'GET':
        return render(request, "ver_proposito.html",  {
        'proposito': proposito,
        'examen_fisico': examen_fisico,
        # ... otros contextos que ya tengas
    })


@login_required
def diagnosticos_plan_estudio(request, proposito_id):
    proposito = get_object_or_404(Propositos, pk=proposito_id)
    diagnostico_plan, created = DiagnosticosPlanEstudio.objects.get_or_create(
        proposito=proposito
    )
    
    if request.method == 'POST':
        form = DiagnosticosPlanEstudioForm(request.POST, instance=diagnostico_plan)
        formset = DiagnosticoPresuntivoFormSet(request.POST, instance=diagnostico_plan)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('ver_proposito', proposito_id=proposito_id)
    else:
        form = DiagnosticosPlanEstudioForm(instance=diagnostico_plan)
        formset = DiagnosticoPresuntivoFormSet(instance=diagnostico_plan)
    
    return render(request, 'diagnosticos_plan.html', {
        'form': form,
        'formset': formset,
        'proposito': proposito
    })
































































def hello(request, username):
    print(username)
    return HttpResponse("<h1>Hello %s</h1>" % username)


def about(request):
    username = 'Jose'
    return render(request, "about.html", {
        'username': username
    })


def projects(request):
   # projects = list(Project.objects.values())
    projects = Project.objects.all()
    return render(request, "projects.html", {
        'projects': projects

    })


def tasks(request):

    tasks = Task.objects.all()
    return render(request, "tasks.html", {
        'tasks': tasks
    })


def create_task(request):

    if request.method == 'GET':
        return render(request, 'create_task.html', {
            'form': CreateNewTask()
        })
    else:

        Task.objects.create(
            title=request.POST['title'], description=request.POST['description'], project_id=1)
        return redirect('tasks')


def create_project(request):

    if request.method == 'GET':
        return render(request, 'create_project.html', {
            'form': CreateNewProject()
        })
    else:

        Project.objects.create(name=request.POST['name'])
        return redirect('projects')


def project_detail(request, id):

    project = get_object_or_404(Project, id=id)
    tasks = Task.objects.filter(project_id=id)

    return render(request, 'detail.html', {
        'project': project,
        'tasks': tasks
    })
