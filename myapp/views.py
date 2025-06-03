# Django Core imports
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.forms import AuthenticationForm # Standard Django auth form

# App-specific imports
from .models import (
    Genetistas, Propositos, HistoriasClinicas, InformacionPadres, ExamenFisico,
    Parejas, AntecedentesPersonales, DesarrolloPsicomotor, PeriodoNeonatal, # For AntecedentesDesarrolloNeonatalForm save
    AntecedentesFamiliaresPreconcepcionales, # For AntecedentesPreconcepcionalesForm save
    EvaluacionGenetica, DiagnosticoPresuntivo, PlanEstudio
)
from .forms import (
    ExtendedUserCreationForm, HistoriasForm, PropositosForm, PadresPropositoForm,
    AntecedentesDesarrolloNeonatalForm, AntecedentesPreconcepcionalesForm,
    ExamenFisicoForm, ParejaPropositosForm, SignosClinicosForm,
    DiagnosticoPresuntivoFormSet, PlanEstudioFormSet, LoginForm # Your custom login form
)
# Imports for tutorial/example views (consider removing if not used by clinical app)
from .models import Project, Task
from .forms import CreateNewTask, CreateNewProject


# --- Main Clinical Views ---

@login_required
def crear_historia(request):
    if request.method == 'POST':
        form = HistoriasForm(request.POST)
        if form.is_valid():
            try:
                genetista = request.user.genetistas # Assumes related_name 'genetistas' or user is Genetistas model
            except Genetistas.DoesNotExist:
                messages.error(request, 'El usuario actual no tiene un perfil de genetista asociado.')
                return render(request, "historia_clinica.html", {'form1': form}) # Show form with error

            historia = form.save(commit=False)
            historia.genetista = genetista
            historia.save()
            messages.success(request, f"Historia Clínica N° {historia.numero_historia} creada exitosamente.")
            
            motivo = form.cleaned_data['motivo_tipo_consulta']
            redirect_map = {
                'Proposito-Diagnóstico': ('paciente_crear', {'historia_id': historia.historia_id}),
                'Pareja-Asesoramiento Prenupcial': ('pareja_crear', {'historia_id': historia.historia_id}),
                'Pareja-Preconcepcional': ('pareja_crear', {'historia_id': historia.historia_id}),
                'Pareja-Prenatal': ('pareja_crear', {'historia_id': historia.historia_id}),
            }
            if motivo in redirect_map:
                view_name, kwargs = redirect_map[motivo]
                return redirect(view_name, **kwargs)
            else:
                messages.warning(request, "Motivo de consulta no especificado para redirección, volviendo al inicio.")
                return redirect('index') # Fallback redirect
        else:
            messages.error(request, "Por favor, corrija los errores en el formulario.")
    else: # GET
        form = HistoriasForm()
    
    return render(request, "historia_clinica.html", {'form1': form})

@login_required
def crear_paciente(request, historia_id):
    historia = get_object_or_404(HistoriasClinicas, historia_id=historia_id)

    if request.method == 'POST':
        form = PropositosForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # The PropositosForm has a custom save method
                proposito = form.save(historia=historia)
                messages.success(request, f"Paciente {proposito.nombres} {proposito.apellidos} creado exitosamente.")
                return redirect('padres_proposito_crear', historia_id=historia.historia_id, proposito_id=proposito.proposito_id)
            except IntegrityError as e: # Catch potential unique constraint violations (e.g. 'identificacion')
                messages.error(request, f"Error al guardar el paciente: {e}. Verifique que la identificación no esté duplicada.")
            except Exception as e:
                messages.error(request, f"Error inesperado al guardar el paciente: {e}")
        else:
            messages.error(request, "Por favor, corrija los errores en el formulario.")
    else: # GET
        form = PropositosForm()
    
    return render(request, "Crear_paciente.html", {'form': form, 'historia': historia})

@login_required
def crear_pareja(request, historia_id):
    historia = get_object_or_404(HistoriasClinicas, historia_id=historia_id)

    if request.method == 'POST':
        form = ParejaPropositosForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create first proposito (conyugue 1)
                    proposito1 = Propositos.objects.create(
                        historia=historia,
                        nombres=form.cleaned_data['nombres_1'],
                        apellidos=form.cleaned_data['apellidos_1'],
                        lugar_nacimiento=form.cleaned_data.get('lugar_nacimiento_1'),
                        fecha_nacimiento=form.cleaned_data.get('fecha_nacimiento_1'),
                        escolaridad=form.cleaned_data.get('escolaridad_1'),
                        ocupacion=form.cleaned_data.get('ocupacion_1'),
                        edad=form.cleaned_data.get('edad_1'),
                        identificacion=form.cleaned_data['identificacion_1'],
                        direccion=form.cleaned_data.get('direccion_1'),
                        telefono=form.cleaned_data.get('telefono_1'),
                        email=form.cleaned_data.get('email_1'),
                        grupo_sanguineo=form.cleaned_data.get('grupo_sanguineo_1'),
                        factor_rh=form.cleaned_data.get('factor_rh_1'),
                        foto=form.cleaned_data.get('foto_1')
                    )

                    # Create second proposito (conyugue 2)
                    proposito2 = Propositos.objects.create(
                        historia=historia,
                        nombres=form.cleaned_data['nombres_2'],
                        apellidos=form.cleaned_data['apellidos_2'],
                        lugar_nacimiento=form.cleaned_data.get('lugar_nacimiento_2'),
                        fecha_nacimiento=form.cleaned_data.get('fecha_nacimiento_2'),
                        escolaridad=form.cleaned_data.get('escolaridad_2'),
                        ocupacion=form.cleaned_data.get('ocupacion_2'),
                        edad=form.cleaned_data.get('edad_2'),
                        identificacion=form.cleaned_data['identificacion_2'],
                        direccion=form.cleaned_data.get('direccion_2'),
                        telefono=form.cleaned_data.get('telefono_2'),
                        email=form.cleaned_data.get('email_2'),
                        grupo_sanguineo=form.cleaned_data.get('grupo_sanguineo_2'),
                        factor_rh=form.cleaned_data.get('factor_rh_2'),
                        foto=form.cleaned_data.get('foto_2')
                    )
                    
                    pareja = Parejas.objects.create(proposito_id_1=proposito1, proposito_id_2=proposito2)
                
                messages.success(request, f"Pareja ({proposito1.nombres} y {proposito2.nombres}) creada exitosamente.")
                return redirect('antecedentes_personales_crear', 
                                 historia_id=historia.historia_id,
                                 tipo="pareja",
                                 objeto_id=pareja.pareja_id)
            except IntegrityError as e:
                 messages.error(request, f"Error de integridad al guardar la pareja: {e}. Verifique las identificaciones.")
            except Exception as e:
                messages.error(request, f"Error inesperado al guardar la pareja: {e}")
        else:
            messages.error(request, "Por favor, corrija los errores en el formulario.")
    else: # GET
        form = ParejaPropositosForm()

    return render(request, 'Crear_pareja.html', {'form': form, 'historia': historia})

@login_required
def padres_proposito(request, historia_id, proposito_id):
    historia = get_object_or_404(HistoriasClinicas, historia_id=historia_id)
    proposito = get_object_or_404(Propositos, proposito_id=proposito_id, historia=historia)

    if request.method == 'POST':
        form = PadresPropositoForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Delete existing parents for this proposito to avoid duplicates if re-submitting
                    # InformacionPadres.objects.filter(proposito=proposito).delete() # Or handle update

                    InformacionPadres.objects.update_or_create(
                        proposito=proposito, tipo='Padre',
                        defaults={
                            'nombres': form.cleaned_data['padre_nombres'],
                            'apellidos': form.cleaned_data['padre_apellidos'],
                            'escolaridad': form.cleaned_data.get('padre_escolaridad'),
                            'ocupacion': form.cleaned_data.get('padre_ocupacion'),
                            'lugar_nacimiento': form.cleaned_data.get('padre_lugar_nacimiento'),
                            'fecha_nacimiento': form.cleaned_data.get('padre_fecha_nacimiento'),
                            'edad': form.cleaned_data.get('padre_edad'),
                            'identificacion': form.cleaned_data.get('padre_identificacion'),
                            'grupo_sanguineo': form.cleaned_data.get('padre_grupo_sanguineo'),
                            'factor_rh': form.cleaned_data.get('padre_factor_rh'),
                            'telefono': form.cleaned_data.get('padre_telefono'),
                            'email': form.cleaned_data.get('padre_email'),
                            'direccion': form.cleaned_data.get('padre_direccion')
                        }
                    )
                    InformacionPadres.objects.update_or_create(
                        proposito=proposito, tipo='Madre',
                        defaults={
                            'nombres': form.cleaned_data['madre_nombres'],
                            'apellidos': form.cleaned_data['madre_apellidos'],
                            'escolaridad': form.cleaned_data.get('madre_escolaridad'),
                            'ocupacion': form.cleaned_data.get('madre_ocupacion'),
                            'lugar_nacimiento': form.cleaned_data.get('madre_lugar_nacimiento'),
                            'fecha_nacimiento': form.cleaned_data.get('madre_fecha_nacimiento'),
                            'edad': form.cleaned_data.get('madre_edad'),
                            'identificacion': form.cleaned_data.get('madre_identificacion'),
                            'grupo_sanguineo': form.cleaned_data.get('madre_grupo_sanguineo'),
                            'factor_rh': form.cleaned_data.get('madre_factor_rh'),
                            'telefono': form.cleaned_data.get('madre_telefono'),
                            'email': form.cleaned_data.get('madre_email'),
                            'direccion': form.cleaned_data.get('madre_direccion')
                        }
                    )
                messages.success(request, "Información de los padres guardada exitosamente.")
                return redirect('antecedentes_personales_crear', 
                                historia_id=historia_id,
                                tipo='proposito',
                                objeto_id=proposito_id)
            except Exception as e:
                messages.error(request, f"Error al guardar la información de los padres: {e}")
        else:
            messages.error(request, "Por favor, corrija los errores en el formulario.")
    else: # GET
        # Pre-fill form if data exists
        padre = InformacionPadres.objects.filter(proposito=proposito, tipo='Padre').first()
        madre = InformacionPadres.objects.filter(proposito=proposito, tipo='Madre').first()
        initial_data = {}
        if padre:
            initial_data.update({f'padre_{f.name}': getattr(padre, f.name) for f in InformacionPadres._meta.fields if f.name not in ['padre_id', 'proposito', 'tipo']})
        if madre:
            initial_data.update({f'madre_{f.name}': getattr(madre, f.name) for f in InformacionPadres._meta.fields if f.name not in ['padre_id', 'proposito', 'tipo']})
        form = PadresPropositoForm(initial=initial_data if initial_data else None)
        
    return render(request, "Padres_proposito.html", {'form': form, 'historia': historia, 'proposito': proposito})

@login_required
def crear_antecedentes_personales(request, historia_id, tipo, objeto_id):
    historia = get_object_or_404(HistoriasClinicas, historia_id=historia_id)
    proposito_obj, pareja_obj, context_object_name = None, None, ""

    if tipo == 'proposito':
        proposito_obj = get_object_or_404(Propositos, proposito_id=objeto_id, historia=historia)
        context_object_name = f"{proposito_obj.nombres} {proposito_obj.apellidos}"
        # Check if antecedents already exist to prevent duplicates or allow update
        if AntecedentesPersonales.objects.filter(proposito=proposito_obj).exists() and request.method == 'GET':
             messages.info(request, f"Editando antecedentes personales para {context_object_name}.")
        # You might want to redirect if they exist and you don't want updates from this view:
        # if AntecedentesPersonales.objects.filter(proposito=proposito_obj).exists():
        #    return redirect('some_other_view_or_detail_page')
    elif tipo == 'pareja':
        pareja_obj = get_object_or_404(Parejas, pareja_id=objeto_id, proposito_id_1__historia=historia)
        context_object_name = f"Pareja ID: {pareja_obj.pareja_id}"
        if AntecedentesPersonales.objects.filter(pareja=pareja_obj).exists() and request.method == 'GET':
            messages.info(request, f"Editando antecedentes personales para {context_object_name}.")
    else:
        messages.error(request, 'Tipo de objeto no válido.')
        return redirect('index')

    if request.method == 'POST':
        form = AntecedentesDesarrolloNeonatalForm(request.POST)
        if form.is_valid():
            try:
                # The form's save method handles creating AntecedentesPersonales, DesarrolloPsicomotor, PeriodoNeonatal
                if tipo == 'proposito':
                    form.save(proposito=proposito_obj)
                    redirect_to = 'antecedentes_preconcepcionales_crear'
                    redirect_kwargs = {'historia_id': historia.historia_id, 'tipo': "proposito", 'objeto_id': proposito_obj.proposito_id}
                else: # tipo == 'pareja'
                    form.save(pareja=pareja_obj)
                    redirect_to = 'antecedentes_preconcepcionales_crear'
                    redirect_kwargs = {'historia_id': historia.historia_id, 'tipo': "pareja", 'objeto_id': pareja_obj.pareja_id}
                
                messages.success(request, f"Antecedentes personales y desarrollo guardados para {context_object_name}.")
                return redirect(redirect_to, **redirect_kwargs)
            except Exception as e:
                messages.error(request, f'Error al guardar antecedentes: {str(e)}')
        else:
            messages.error(request, "Por favor, corrija los errores en el formulario.")
    else: # GET
        # Pre-fill if editing (This part can be complex if form combines multiple models)
        # For simplicity, providing an empty form or a form partially filled if logic is added.
        # Example of pre-filling (simplified, would need more logic for combined form):
        # initial_data = {}
        # if tipo == 'proposito' and proposito_obj:
        #     ap = AntecedentesPersonales.objects.filter(proposito=proposito_obj).first()
        #     if ap: initial_data.update({f.name: getattr(ap, f.name) for f in AntecedentesPersonales._meta.fields})
        #     # ... do for DesarrolloPsicomotor and PeriodoNeonatal
        # form = AntecedentesDesarrolloNeonatalForm(initial=initial_data if initial_data else None)
        form = AntecedentesDesarrolloNeonatalForm() # Default to empty for now
        
    context = {
        'form': form, 'historia': historia, 'tipo': tipo, 
        'objeto': proposito_obj if tipo == 'proposito' else pareja_obj,
        'context_object_name': context_object_name
    }
    return render(request, 'antecedentes_personales.html', context)

@login_required
def crear_antecedentes_preconcepcionales(request, historia_id, tipo, objeto_id):
    historia = get_object_or_404(HistoriasClinicas, historia_id=historia_id)
    proposito_obj, pareja_obj, context_object_name = None, None, ""

    if tipo == 'proposito':
        proposito_obj = get_object_or_404(Propositos, proposito_id=objeto_id, historia=historia)
        context_object_name = f"{proposito_obj.nombres} {proposito_obj.apellidos}"
        if AntecedentesFamiliaresPreconcepcionales.objects.filter(proposito=proposito_obj).exists() and request.method == 'GET':
            messages.info(request, f"Editando antecedentes preconcepcionales para {context_object_name}.")
    elif tipo == 'pareja':
        pareja_obj = get_object_or_404(Parejas, pareja_id=objeto_id, proposito_id_1__historia=historia)
        context_object_name = f"Pareja ID: {pareja_obj.pareja_id}"
        if AntecedentesFamiliaresPreconcepcionales.objects.filter(pareja=pareja_obj).exists() and request.method == 'GET':
             messages.info(request, f"Editando antecedentes preconcepcionales para {context_object_name}.")
    else:
        messages.error(request, 'Tipo de objeto no válido.')
        return redirect('index')

    if request.method == 'POST':
        form = AntecedentesPreconcepcionalesForm(request.POST)
        if form.is_valid():
            try:
                # The form's save method handles creation
                if tipo == 'proposito':
                    form.save(proposito=proposito_obj, pareja=None, tipo='proposito')
                    redirect_to = 'evaluacion_genetica_detalle' # Or next step
                    redirect_kwargs = {'historia_id': historia.historia_id, 'tipo': "proposito", 'objeto_id': proposito_obj.proposito_id}
                else: # tipo == 'pareja'
                    form.save(proposito=None, pareja=pareja_obj, tipo='pareja')
                    redirect_to = 'evaluacion_genetica_detalle' # Or next step
                    redirect_kwargs = {'historia_id': historia.historia_id, 'tipo': "pareja", 'objeto_id': pareja_obj.pareja_id}
                
                messages.success(request, f"Antecedentes preconcepcionales guardados para {context_object_name}.")
                return redirect(redirect_to, **redirect_kwargs)
            except Exception as e:
                messages.error(request, f'Error al guardar antecedentes preconcepcionales: {str(e)}')
        else:
            messages.error(request, "Por favor, corrija los errores en el formulario.")
    else: # GET
        # Pre-fill if editing
        instance_to_edit = None
        if tipo == 'proposito' and proposito_obj:
            instance_to_edit = AntecedentesFamiliaresPreconcepcionales.objects.filter(proposito=proposito_obj).first()
        elif tipo == 'pareja' and pareja_obj:
            instance_to_edit = AntecedentesFamiliaresPreconcepcionales.objects.filter(pareja=pareja_obj).first()
        
        initial_data = {}
        if instance_to_edit:
            initial_data = {f.name: getattr(instance_to_edit, f.name) for f in AntecedentesFamiliaresPreconcepcionales._meta.fields if hasattr(instance_to_edit, f.name)}
        form = AntecedentesPreconcepcionalesForm(initial=initial_data if initial_data else None)

    context = {
        'form': form, 'historia': historia, 'tipo': tipo,
        'objeto': proposito_obj if tipo == 'proposito' else pareja_obj,
        'context_object_name': context_object_name
    }
    return render(request, 'antecedentes_preconcepcionales.html', context)

@login_required
def crear_examen_fisico(request, proposito_id):
    proposito = get_object_or_404(Propositos, pk=proposito_id)
    # ExamenFisico has a OneToOne or Unique ForeignKey with Proposito, so use .first() or try-except
    try:
        examen_existente = ExamenFisico.objects.get(proposito=proposito)
    except ExamenFisico.DoesNotExist:
        examen_existente = None

    if request.method == 'POST':
        form = ExamenFisicoForm(request.POST, instance=examen_existente)
        # Pass proposito to form if its save method needs it (as designed in your form)
        form.proposito_instance = proposito 
        
        if form.is_valid():
            form.save() # Form's save method handles setting proposito and fecha
            messages.success(request, f"Examen físico para {proposito.nombres} guardado exitosamente.")
            return redirect('proposito_detalle', proposito_id=proposito.proposito_id)
        else:
            messages.error(request, "Por favor, corrija los errores en el formulario.")
    else: # GET
        form = ExamenFisicoForm(instance=examen_existente)
        if examen_existente:
            messages.info(request, f"Editando examen físico para {proposito.nombres}.")

    return render(request, 'examen_fisico.html', {
        'form': form,
        'proposito': proposito,
        'editing': bool(examen_existente)
    })

@login_required
def ver_proposito(request, proposito_id):
    proposito = get_object_or_404(Propositos, pk=proposito_id)
    try:
        examen_fisico = ExamenFisico.objects.get(proposito=proposito)
    except ExamenFisico.DoesNotExist:
        examen_fisico = None
    # You might want to fetch other related data here as well
    # e.g., padres_info = InformacionPadres.objects.filter(proposito=proposito)
    return render(request, "ver_proposito.html", {
        'proposito': proposito,
        'examen_fisico': examen_fisico,
    })

@login_required
def diagnosticos_plan_estudio(request, historia_id, tipo, objeto_id):
    historia = get_object_or_404(HistoriasClinicas, historia_id=historia_id)
    proposito_obj, pareja_obj, context_object_name = None, None, ""
    evaluacion_defaults = {}

    if tipo == 'proposito':
        proposito_obj = get_object_or_404(Propositos, proposito_id=objeto_id, historia=historia)
        context_object_name = f"Propósito: {proposito_obj.nombres} {proposito_obj.apellidos}"
        evaluacion_defaults = {'proposito': proposito_obj, 'pareja': None}
        evaluacion, created = EvaluacionGenetica.objects.get_or_create(
            proposito=proposito_obj, defaults=evaluacion_defaults
        )
        if not created and evaluacion.pareja is not None: # Ensure consistency if somehow created wrongly
            evaluacion.pareja = None
            evaluacion.proposito = proposito_obj # Re-affirm
            evaluacion.save()

    elif tipo == 'pareja':
        pareja_obj = get_object_or_404(Parejas, pareja_id=objeto_id, proposito_id_1__historia=historia)
        context_object_name = f"Pareja ID: {pareja_obj.pareja_id} ({pareja_obj.proposito_id_1.nombres} y {pareja_obj.proposito_id_2.nombres})"
        evaluacion_defaults = {'pareja': pareja_obj, 'proposito': None}
        evaluacion, created = EvaluacionGenetica.objects.get_or_create(
            pareja=pareja_obj, defaults=evaluacion_defaults
        )
        if not created and evaluacion.proposito is not None: # Ensure consistency
            evaluacion.proposito = None
            evaluacion.pareja = pareja_obj # Re-affirm
            evaluacion.save()
    else:
        messages.error(request, "Tipo de objeto no válido para la evaluación genética.")
        return redirect('index')

    if request.method == 'POST':
        signos_form = SignosClinicosForm(request.POST, instance=evaluacion)
        diagnostico_formset = DiagnosticoPresuntivoFormSet(request.POST, prefix='diagnosticos')
        plan_formset = PlanEstudioFormSet(request.POST, prefix='plans')

        if signos_form.is_valid() and diagnostico_formset.is_valid() and plan_formset.is_valid():
            with transaction.atomic():
                signos_form.save() # Guarda/actualiza EvaluacionGenetica

                # Clear old and save new Diagnosticos Presuntivos
                DiagnosticoPresuntivo.objects.filter(evaluacion=evaluacion).delete()
                for form_diag in diagnostico_formset:
                    if form_diag.cleaned_data and not form_diag.cleaned_data.get('DELETE', False):
                        if form_diag.cleaned_data.get('descripcion'):
                            DiagnosticoPresuntivo.objects.create(
                                evaluacion=evaluacion,
                                descripcion=form_diag.cleaned_data['descripcion'],
                                orden=form_diag.cleaned_data.get('orden', 0)
                            )
                
                # Clear old and save new Planes de Estudio
                PlanEstudio.objects.filter(evaluacion=evaluacion).delete()
                for form_plan in plan_formset:
                    if form_plan.cleaned_data and not form_plan.cleaned_data.get('DELETE', False):
                        if form_plan.cleaned_data.get('accion'):
                            PlanEstudio.objects.create(
                                evaluacion=evaluacion,
                                accion=form_plan.cleaned_data['accion'],
                                fecha_limite=form_plan.cleaned_data.get('fecha_limite'),
                                completado=form_plan.cleaned_data.get('completado', False)
                            )
            
            messages.success(request, "Evaluación genética guardada exitosamente.")
            # Consider redirecting to a detail view or back to the main index/dashboard
            return redirect('index') 
        else:
            messages.error(request, "Por favor, corrija los errores en los formularios.")
    else: # GET
        signos_form = SignosClinicosForm(instance=evaluacion)
        
        diagnosticos_initial = [{'descripcion': d.descripcion, 'orden': d.orden} 
                                for d in DiagnosticoPresuntivo.objects.filter(evaluacion=evaluacion).order_by('orden')]
        diagnostico_formset = DiagnosticoPresuntivoFormSet(prefix='diagnosticos', initial=diagnosticos_initial or None)

        planes_initial = [{'accion': p.accion, 'fecha_limite': p.fecha_limite, 'completado': p.completado}
                          for p in PlanEstudio.objects.filter(evaluacion=evaluacion)] # .order_by if needed
        plan_formset = PlanEstudioFormSet(prefix='plans', initial=planes_initial or None)

    context = {
        'historia': historia,
        'tipo': tipo,
        'objeto': proposito_obj or pareja_obj,
        'context_object_name': context_object_name,
        'signos_form': signos_form,
        'diagnostico_formset': diagnostico_formset,
        'plan_formset': plan_formset,
        'evaluacion_instance': evaluacion # For template to know if it's create/edit context
    }
    return render(request, 'diagnosticos_plan.html', context)

# --- AJAX Views ---
@login_required # Or adjust based on whether anonymous users can search
def buscar_propositos(request):
    query = request.GET.get('q', '').strip()
    propositos_qs = Propositos.objects.none() # Default to empty

    if request.user.is_authenticated:
        try:
            # Assuming Genetistas has a OneToOneField to User named 'user'
            # and the related name from User to Genetistas is 'genetistas'
            genetista = request.user.genetistas
            if query:
                propositos_qs = Propositos.objects.select_related('historia').filter(
                    Q(nombres__icontains=query) | 
                    Q(apellidos__icontains=query) |
                    Q(identificacion__icontains=query),
                    historia__genetista=genetista
                ).order_by('-historia__fecha_ingreso')[:10] # Limit results
            else:
                # Optionally, return recent propositos if query is empty
                propositos_qs = Propositos.objects.select_related('historia').filter(
                    historia__genetista=genetista
                ).order_by('-historia__fecha_ingreso')[:5]
        except Genetistas.DoesNotExist:
            # Handle case where user is authenticated but not a genetista
            # Or if 'genetistas' related_name is different.
            pass # propositos_qs remains Propositos.objects.none()
    
    resultados = [{
        'proposito_id': p.proposito_id,
        'nombres': p.nombres,
        'apellidos': p.apellidos,
        'edad': p.edad,
        'direccion': p.direccion or "N/A",
        'identificacion': p.identificacion,
        'foto_url': p.foto.url if p.foto else None, # Ensure MEDIA_URL is set up
        'fecha_ingreso': p.historia.fecha_ingreso.strftime("%d/%m/%Y %H:%M") if p.historia and p.historia.fecha_ingreso else "--"
    } for p in propositos_qs]
    
    return JsonResponse({'propositos': resultados})


# --- Authentication Views ---
def signup(request):
    if request.method == 'POST':
        form = ExtendedUserCreationForm(request.POST)
        if form.is_valid():
            # Password validation is handled by UserCreationForm's clean method
            try:
                with transaction.atomic():
                    user = form.save() # This creates the User instance
                    # Create the Genetistas profile linked to the user
                    Genetistas.objects.create(user=user) 
                
                login(request, user)
                messages.success(request, "Registro exitoso. ¡Bienvenido!")
                return redirect('index') # Or 'task_list' / dashboard
            except IntegrityError: # Should be rare if username check is done by form
                messages.error(request, "El nombre de usuario ya existe o ha ocurrido un error de base de datos.")
            except Exception as e:
                messages.error(request, f"Un error inesperado ocurrió: {e}")
        else:
            messages.error(request, "Por favor, corrija los errores en el formulario de registro.")
    else: # GET
        form = ExtendedUserCreationForm()
    return render(request, "signup.html", {'form': form})
     
def login_medico(request):
    if request.user.is_authenticated:
        return redirect('index') # Or dashboard

    if request.method == 'POST':
        form = LoginForm(request.POST) # Using your custom LoginForm
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"Bienvenido de nuevo, {user.username}.")
                # Redirect to a specific page after login, e.g., a dashboard or 'next' URL
                next_url = request.GET.get('next')
                return redirect(next_url or 'index')
            else:
                messages.error(request, "Nombre de usuario o contraseña incorrectos.")
        else:
            messages.error(request, "Por favor, ingrese un nombre de usuario y contraseña válidos.")
    else: # GET
        form = LoginForm() # Or AuthenticationForm() if you prefer Django's default
    
    return render(request, "login.html", {'form': form})
   
def signout(request):
    logout(request)
    messages.success(request, "Has cerrado sesión exitosamente.")
    return redirect('login')


# --- Other/Management Views ---
@login_required
def reports_view(request):
    # Add logic here to gather data for reports
    return render(request, 'reports.html')

@login_required
def gestion_usuarios_view(request):
    # Add logic for user management if needed (e.g., listing users, roles)
    # Requires superuser or specific permissions typically
    # from django.contrib.auth.models import User
    # users = User.objects.all()
    # context = {'users': users}
    return render(request, 'gestion_usuarios.html') #, context)

# --- Example/Tutorial Views (Consider removing or separating) ---
def index(request): # This is the main index, not tutorial 'index'
    # You might want to display a dashboard here for logged-in users
    # e.g., recent patients, upcoming appointments, etc.
    # ultimos_propositos = get_ultimos_propositos(request) # If you define this helper
    # context = {'ultimos_propositos': ultimos_propositos}
    # return render(request, "dashboard.html", context)
    return render(request, "index.html", {'title': "Sistema de Gestión de Historias Clínicas Genéticas"})

def hello(request, username):
    return JsonResponse({"message": f"Hello {username}"}) # Example JSON response

def about(request):
    return render(request, "about.html", {'username': request.user.username if request.user.is_authenticated else "Invitado"})

@login_required # Assuming projects/tasks are for logged-in users
def projects(request):
    projects_list = Project.objects.all() # Ensure Project model is relevant
    return render(request, "projects.html", {'projects': projects_list})

@login_required
def tasks(request):
    tasks_list = Task.objects.all() # Ensure Task model is relevant
    return render(request, "tasks.html", {'tasks': tasks_list})

@login_required
def create_task(request):
    if request.method == 'POST':
        form = CreateNewTask(request.POST)
        if form.is_valid():
            # Assuming a default project_id=1 for simplicity, adjust as needed
            # project_instance = get_object_or_404(Project, id=1) 
            # Task.objects.create(
            #     title=form.cleaned_data['title'], 
            #     description=form.cleaned_data['description'], 
            #     project=project_instance 
            # )
            messages.success(request, "Tarea creada (ejemplo).")
            return redirect('task_list') # Use URL name
        else:
            messages.error(request, "Error en el formulario de tarea (ejemplo).")
    else:
        form = CreateNewTask()
    return render(request, 'create_task.html', {'form': form})

@login_required
def create_project(request):
    if request.method == 'POST':
        form = CreateNewProject(request.POST)
        if form.is_valid():
            # Project.objects.create(name=form.cleaned_data['name'])
            messages.success(request, "Proyecto creado (ejemplo).")
            return redirect('project_list') # Use URL name
        else:
            messages.error(request, "Error en el formulario de proyecto (ejemplo).")
    else:
        form = CreateNewProject()
    return render(request, 'create_project.html', {'form': form})

@login_required
def project_detail(request, id):
    project_instance = get_object_or_404(Project, id=id) # Ensure Project model is relevant
    project_tasks = Task.objects.filter(project=project_instance)
    return render(request, 'detail.html', {'project': project_instance, 'tasks': project_tasks})