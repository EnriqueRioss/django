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
    Parejas, AntecedentesPersonales, DesarrolloPsicomotor, PeriodoNeonatal, 
    AntecedentesFamiliaresPreconcepcionales, 
    EvaluacionGenetica, DiagnosticoPresuntivo, PlanEstudio
)
from .forms import (
    ExtendedUserCreationForm, HistoriasForm, PropositosForm, PadresPropositoForm,
    AntecedentesDesarrolloNeonatalForm, AntecedentesPreconcepcionalesForm,
    ExamenFisicoForm, ParejaPropositosForm, SignosClinicosForm,
    DiagnosticoPresuntivoFormSet, PlanEstudioFormSet, LoginForm
)
from .models import Project, Task
from .forms import CreateNewTask, CreateNewProject


# --- Main Clinical Views ---

@login_required
def crear_historia(request):
    if request.method == 'POST':
        form = HistoriasForm(request.POST)
        if form.is_valid():
            try:
                genetista = request.user.genetistas 
            except Genetistas.DoesNotExist: # Check correct related name or attribute
                # Fallback: Try to get Genetistas based on user directly if OneToOne is to User
                try:
                    genetista = Genetistas.objects.get(user=request.user)
                except Genetistas.DoesNotExist:
                    messages.error(request, 'El usuario actual no tiene un perfil de genetista asociado.')
                    return render(request, "historia_clinica.html", {'form1': form})

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
                return redirect('index') 
        else:
            messages.error(request, "Por favor, corrija los errores en el formulario.")
    else: 
        form = HistoriasForm()
    
    return render(request, "historia_clinica.html", {'form1': form})

@login_required
def crear_paciente(request, historia_id):
    historia = get_object_or_404(HistoriasClinicas, historia_id=historia_id)
    existing_proposito = None

    # Attempt to find an existing Proposito for this historia if it's singular for this context
    # This logic might need refinement based on how Propositos are uniquely tied to Historias in "Proposito-Diagnóstico"
    if historia.motivo_tipo_consulta == 'Proposito-Diagnóstico':
        potential_propositos = Propositos.objects.filter(historia=historia)
        if potential_propositos.count() == 1:
            existing_proposito = potential_propositos.first()
        elif potential_propositos.count() > 1 and request.method == 'GET': # Only message on GET
            messages.warning(request, "Múltiples propósitos existen para esta historia. La edición específica debe hacerse desde otro listado o interfaz.")


    if request.method == 'POST':
        form = PropositosForm(request.POST, request.FILES, instance=existing_proposito)
        if form.is_valid():
            try:
                proposito = form.save(historia=historia) # Form's save now handles update_or_create
                messages.success(request, f"Paciente {proposito.nombres} {proposito.apellidos} {'actualizado' if existing_proposito and existing_proposito.pk == proposito.pk else 'creado'} exitosamente.")
                return redirect('padres_proposito_crear', historia_id=historia.historia_id, proposito_id=proposito.proposito_id)
            except IntegrityError as e: 
                messages.error(request, f"Error de integridad al guardar el paciente: {e}. Verifique que la identificación no esté duplicada o contacte soporte.")
            except Exception as e:
                messages.error(request, f"Error inesperado al guardar el paciente: {e}")
        else:
            messages.error(request, "Por favor, corrija los errores en el formulario.")
    else: # GET
        form = PropositosForm(instance=existing_proposito)
        if existing_proposito:
            messages.info(request, f"Editando información para el propósito: {existing_proposito.nombres} {existing_proposito.apellidos}")
    
    return render(request, "Crear_paciente.html", {'form': form, 'historia': historia, 'editing': bool(existing_proposito)})

@login_required
def crear_pareja(request, historia_id):
    historia = get_object_or_404(HistoriasClinicas, historia_id=historia_id)

    if request.method == 'POST':
        form = ParejaPropositosForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    
                    def get_proposito_data_from_form(form_cleaned_data, prefix_num, historia_obj):
                        return {
                            'historia': historia_obj,
                            'nombres': form_cleaned_data[f'nombres_{prefix_num}'],
                            'apellidos': form_cleaned_data[f'apellidos_{prefix_num}'],
                            'lugar_nacimiento': form_cleaned_data.get(f'lugar_nacimiento_{prefix_num}'),
                            'fecha_nacimiento': form_cleaned_data.get(f'fecha_nacimiento_{prefix_num}'),
                            'escolaridad': form_cleaned_data.get(f'escolaridad_{prefix_num}'),
                            'ocupacion': form_cleaned_data.get(f'ocupacion_{prefix_num}'),
                            'edad': form_cleaned_data.get(f'edad_{prefix_num}'),
                            'direccion': form_cleaned_data.get(f'direccion_{prefix_num}'),
                            'telefono': form_cleaned_data.get(f'telefono_{prefix_num}'),
                            'email': form_cleaned_data.get(f'email_{prefix_num}'),
                            'grupo_sanguineo': form_cleaned_data.get(f'grupo_sanguineo_{prefix_num}'),
                            'factor_rh': form_cleaned_data.get(f'factor_rh_{prefix_num}'),
                        }

                    # Proposito 1
                    proposito1_all_data = get_proposito_data_from_form(form.cleaned_data, '1', historia)
                    identificacion1 = form.cleaned_data['identificacion_1']
                    photo1_val = form.cleaned_data.get('foto_1')
                    proposito1_defaults = {k: v for k, v in proposito1_all_data.items() if v is not None or k == 'historia'}
                    
                    proposito1, created1 = Propositos.objects.update_or_create(
                        identificacion=identificacion1,
                        defaults=proposito1_defaults
                    )
                    if photo1_val is not None: 
                        if photo1_val: proposito1.foto = photo1_val
                        else: proposito1.foto = None
                        proposito1.save(update_fields=['foto'])
                    elif created1 and photo1_val is None: # Ensure None if created and no photo
                        proposito1.foto = None
                        proposito1.save(update_fields=['foto'])

                    # Proposito 2
                    proposito2_all_data = get_proposito_data_from_form(form.cleaned_data, '2', historia)
                    identificacion2 = form.cleaned_data['identificacion_2']
                    photo2_val = form.cleaned_data.get('foto_2')
                    proposito2_defaults = {k: v for k, v in proposito2_all_data.items() if v is not None or k == 'historia'}

                    proposito2, created2 = Propositos.objects.update_or_create(
                        identificacion=identificacion2,
                        defaults=proposito2_defaults
                    )
                    if photo2_val is not None:
                        if photo2_val: proposito2.foto = photo2_val
                        else: proposito2.foto = None
                        proposito2.save(update_fields=['foto'])
                    elif created2 and photo2_val is None:
                        proposito2.foto = None
                        proposito2.save(update_fields=['foto'])
                    
                    if proposito1.pk == proposito2.pk:
                        raise IntegrityError("Los dos miembros de la pareja no pueden ser la misma persona (misma identificación).")

                    # Sort by PK for consistent Pareja lookup/creation
                    p_min, p_max = sorted([proposito1, proposito2], key=lambda p: p.pk)
                    
                    pareja, pareja_created = Parejas.objects.get_or_create(
                        proposito_id_1=p_min, 
                        proposito_id_2=p_max
                    )
                
                messages.success(request, f"Pareja ({proposito1.nombres} y {proposito2.nombres}) {'creada' if pareja_created else 'localizada/actualizada'} exitosamente.")
                return redirect('antecedentes_personales_crear', 
                                 historia_id=historia.historia_id,
                                 tipo="pareja",
                                 objeto_id=pareja.pareja_id)
            except IntegrityError as e:
                 messages.error(request, f"Error de integridad al guardar la pareja: {e}. Verifique las identificaciones y que no sean la misma persona.")
            except Exception as e:
                messages.error(request, f"Error inesperado al guardar la pareja: {e}")
        else:
            messages.error(request, "Por favor, corrija los errores en el formulario.")
    else: # GET
        form = ParejaPropositosForm()
        # Pre-filling ParejaPropositosForm on GET is complex as it involves two Propositos.
        # Usually, for "create" views, it's an empty form. If this view were also for "edit pareja",
        # then pre-filling logic would be needed, fetching the Pareja and its two Propositos.

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
                    padre_defaults = {
                        'nombres': form.cleaned_data['padre_nombres'],
                        'apellidos': form.cleaned_data['padre_apellidos'],
                        'escolaridad': form.cleaned_data.get('padre_escolaridad'),
                        'ocupacion': form.cleaned_data.get('padre_ocupacion'),
                        'lugar_nacimiento': form.cleaned_data.get('padre_lugar_nacimiento'),
                        'fecha_nacimiento': form.cleaned_data.get('padre_fecha_nacimiento'),
                        'edad': form.cleaned_data.get('padre_edad'),
                        'identificacion': form.cleaned_data.get('padre_identificacion'),
                        'grupo_sanguineo': form.cleaned_data.get('padre_grupo_sanguineo') or None,
                        'factor_rh': form.cleaned_data.get('padre_factor_rh') or None,
                        'telefono': form.cleaned_data.get('padre_telefono'),
                        'email': form.cleaned_data.get('padre_email'),
                        'direccion': form.cleaned_data.get('padre_direccion')
                    }
                    padre_defaults = {k:v for k,v in padre_defaults.items() if v is not None or k in ['nombres','apellidos']}


                    InformacionPadres.objects.update_or_create(
                        proposito=proposito, tipo='Padre',
                        defaults=padre_defaults
                    )

                    madre_defaults = {
                        'nombres': form.cleaned_data['madre_nombres'],
                        'apellidos': form.cleaned_data['madre_apellidos'],
                        'escolaridad': form.cleaned_data.get('madre_escolaridad'),
                        'ocupacion': form.cleaned_data.get('madre_ocupacion'),
                        'lugar_nacimiento': form.cleaned_data.get('madre_lugar_nacimiento'),
                        'fecha_nacimiento': form.cleaned_data.get('madre_fecha_nacimiento'),
                        'edad': form.cleaned_data.get('madre_edad'),
                        'identificacion': form.cleaned_data.get('madre_identificacion'),
                        'grupo_sanguineo': form.cleaned_data.get('madre_grupo_sanguineo') or None,
                        'factor_rh': form.cleaned_data.get('madre_factor_rh') or None,
                        'telefono': form.cleaned_data.get('madre_telefono'),
                        'email': form.cleaned_data.get('madre_email'),
                        'direccion': form.cleaned_data.get('madre_direccion')
                    }
                    madre_defaults = {k:v for k,v in madre_defaults.items() if v is not None or k in ['nombres','apellidos']}

                    InformacionPadres.objects.update_or_create(
                        proposito=proposito, tipo='Madre',
                        defaults=madre_defaults
                    )
                messages.success(request, "Información de los padres guardada/actualizada exitosamente.")
                return redirect('antecedentes_personales_crear', 
                                historia_id=historia_id,
                                tipo='proposito',
                                objeto_id=proposito_id)
            except Exception as e:
                messages.error(request, f"Error al guardar la información de los padres: {e}")
        else:
            messages.error(request, "Por favor, corrija los errores en el formulario.")
    else: # GET
        padre = InformacionPadres.objects.filter(proposito=proposito, tipo='Padre').first()
        madre = InformacionPadres.objects.filter(proposito=proposito, tipo='Madre').first()
        initial_data = {}
        if padre:
            for f in InformacionPadres._meta.fields:
                if f.name not in ['padre_id', 'proposito', 'tipo'] and hasattr(padre, f.name):
                    initial_data[f'padre_{f.name}'] = getattr(padre, f.name)
        if madre:
            for f in InformacionPadres._meta.fields:
                if f.name not in ['padre_id', 'proposito', 'tipo'] and hasattr(madre, f.name):
                    initial_data[f'madre_{f.name}'] = getattr(madre, f.name)
        form = PadresPropositoForm(initial=initial_data if initial_data else None)
        
    return render(request, "Padres_proposito.html", {'form': form, 'historia': historia, 'proposito': proposito})

@login_required
def crear_antecedentes_personales(request, historia_id, tipo, objeto_id):
    historia = get_object_or_404(HistoriasClinicas, historia_id=historia_id)
    proposito_obj, pareja_obj, context_object_name = None, None, ""
    editing = False

    if tipo == 'proposito':
        proposito_obj = get_object_or_404(Propositos, proposito_id=objeto_id, historia=historia)
        context_object_name = f"{proposito_obj.nombres} {proposito_obj.apellidos}"
        if AntecedentesPersonales.objects.filter(proposito=proposito_obj).exists():
            editing = True
    elif tipo == 'pareja':
        pareja_obj = get_object_or_404(Parejas, pareja_id=objeto_id, proposito_id_1__historia=historia) # Assuming proposito_id_1 is always part of this historia
        context_object_name = f"Pareja ID: {pareja_obj.pareja_id}"
        if AntecedentesPersonales.objects.filter(pareja=pareja_obj).exists():
            editing = True
    else:
        messages.error(request, 'Tipo de objeto no válido.')
        return redirect('index')

    if request.method == 'POST':
        form = AntecedentesDesarrolloNeonatalForm(request.POST)
        if form.is_valid():
            try:
                target_proposito = proposito_obj if tipo == 'proposito' else None
                target_pareja = pareja_obj if tipo == 'pareja' else None
                
                form.save(proposito=target_proposito, pareja=target_pareja) # Form's save now handles update_or_create
                
                messages.success(request, f"Antecedentes personales y desarrollo {'actualizados' if editing else 'guardados'} para {context_object_name}.")
                
                redirect_to = 'antecedentes_preconcepcionales_crear'
                redirect_kwargs = {'historia_id': historia.historia_id, 'tipo': tipo, 'objeto_id': objeto_id}
                return redirect(redirect_to, **redirect_kwargs)
            except Exception as e:
                messages.error(request, f'Error al guardar antecedentes: {str(e)}')
        else:
            messages.error(request, "Por favor, corrija los errores en el formulario.")
    else: # GET
        initial_data = {}
        if editing:
            ap_instance, dp_instance, pn_instance = None, None, None
            if tipo == 'proposito' and proposito_obj:
                ap_instance = AntecedentesPersonales.objects.filter(proposito=proposito_obj).first()
                dp_instance = DesarrolloPsicomotor.objects.filter(proposito=proposito_obj).first()
                pn_instance = PeriodoNeonatal.objects.filter(proposito=proposito_obj).first()
            elif tipo == 'pareja' and pareja_obj:
                ap_instance = AntecedentesPersonales.objects.filter(pareja=pareja_obj).first()
                dp_instance = DesarrolloPsicomotor.objects.filter(pareja=pareja_obj).first()
                pn_instance = PeriodoNeonatal.objects.filter(pareja=pareja_obj).first()

            if ap_instance:
                initial_data.update({f.name: getattr(ap_instance, f.name) for f in AntecedentesPersonales._meta.fields if hasattr(ap_instance, f.name) and f.name not in ['antecedente_id', 'proposito', 'pareja']})
            if dp_instance:
                initial_data.update({f.name: getattr(dp_instance, f.name) for f in DesarrolloPsicomotor._meta.fields if hasattr(dp_instance, f.name) and f.name not in ['desarrollo_id', 'proposito', 'pareja']})
            if pn_instance:
                initial_data.update({f.name: getattr(pn_instance, f.name) for f in PeriodoNeonatal._meta.fields if hasattr(pn_instance, f.name) and f.name not in ['neonatal_id', 'proposito', 'pareja']})
            
            if initial_data:
                 messages.info(request, f"Editando antecedentes personales para {context_object_name}.")

        form = AntecedentesDesarrolloNeonatalForm(initial=initial_data if initial_data else None)
        
    context = {
        'form': form, 'historia': historia, 'tipo': tipo, 
        'objeto': proposito_obj if tipo == 'proposito' else pareja_obj,
        'context_object_name': context_object_name,
        'editing': editing
    }
    return render(request, 'antecedentes_personales.html', context)

@login_required
def crear_antecedentes_preconcepcionales(request, historia_id, tipo, objeto_id):
    historia = get_object_or_404(HistoriasClinicas, historia_id=historia_id)
    proposito_obj, pareja_obj, context_object_name = None, None, ""
    instance_to_edit = None

    if tipo == 'proposito':
        proposito_obj = get_object_or_404(Propositos, proposito_id=objeto_id, historia=historia)
        context_object_name = f"{proposito_obj.nombres} {proposito_obj.apellidos}"
        instance_to_edit = AntecedentesFamiliaresPreconcepcionales.objects.filter(proposito=proposito_obj).first()
    elif tipo == 'pareja':
        pareja_obj = get_object_or_404(Parejas, pareja_id=objeto_id, proposito_id_1__historia=historia)
        context_object_name = f"Pareja ID: {pareja_obj.pareja_id}"
        instance_to_edit = AntecedentesFamiliaresPreconcepcionales.objects.filter(pareja=pareja_obj).first()
    else:
        messages.error(request, 'Tipo de objeto no válido.')
        return redirect('index')

    if request.method == 'POST':
        form = AntecedentesPreconcepcionalesForm(request.POST)
        if form.is_valid():
            try:
                target_proposito = proposito_obj if tipo == 'proposito' else None
                target_pareja = pareja_obj if tipo == 'pareja' else None

                form.save(proposito=target_proposito, pareja=target_pareja, tipo=tipo) # Form's save now handles update_or_create
                
                messages.success(request, f"Antecedentes preconcepcionales {'actualizados' if instance_to_edit else 'guardados'} para {context_object_name}.")
                
                redirect_to = 'evaluacion_genetica_detalle' 
                redirect_kwargs = {'historia_id': historia.historia_id, 'tipo': tipo, 'objeto_id': objeto_id}
                return redirect(redirect_to, **redirect_kwargs)
            except Exception as e:
                messages.error(request, f'Error al guardar antecedentes preconcepcionales: {str(e)}')
        else:
            messages.error(request, "Por favor, corrija los errores en el formulario.")
    else: # GET
        initial_data = {}
        if instance_to_edit:
            initial_data = {f.name: getattr(instance_to_edit, f.name) for f in AntecedentesFamiliaresPreconcepcionales._meta.fields if hasattr(instance_to_edit, f.name) and f.name not in ['antecedente_familiar_id', 'proposito', 'pareja']}
            if initial_data:
                 messages.info(request, f"Editando antecedentes preconcepcionales para {context_object_name}.")
        form = AntecedentesPreconcepcionalesForm(initial=initial_data if initial_data else None)

    context = {
        'form': form, 'historia': historia, 'tipo': tipo,
        'objeto': proposito_obj if tipo == 'proposito' else pareja_obj,
        'context_object_name': context_object_name,
        'editing': bool(instance_to_edit)
    }
    return render(request, 'antecedentes_preconcepcionales.html', context)

@login_required
def crear_examen_fisico(request, proposito_id):
    proposito = get_object_or_404(Propositos, pk=proposito_id)
    try:
        examen_existente = ExamenFisico.objects.get(proposito=proposito)
    except ExamenFisico.DoesNotExist:
        examen_existente = None

    if request.method == 'POST':
        form = ExamenFisicoForm(request.POST, instance=examen_existente)
        form.proposito_instance = proposito # Pass proposito to form's custom save logic
        
        if form.is_valid():
            form.save() 
            messages.success(request, f"Examen físico para {proposito.nombres} {'actualizado' if examen_existente else 'guardado'} exitosamente.")
            # Determine next step, e.g., back to proposito detail or to evaluation if that's the flow
            return redirect('evaluacion_genetica_detalle', historia_id=proposito.historia.historia_id, tipo="proposito", objeto_id=proposito.proposito_id)
            # return redirect('proposito_detalle', proposito_id=proposito.proposito_id) # Or previous redirect
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
    padres_info = InformacionPadres.objects.filter(proposito=proposito)
    antecedentes_personales = AntecedentesPersonales.objects.filter(proposito=proposito).first()
    desarrollo_psicomotor = DesarrolloPsicomotor.objects.filter(proposito=proposito).first()
    periodo_neonatal = PeriodoNeonatal.objects.filter(proposito=proposito).first()
    antecedentes_familiares = AntecedentesFamiliaresPreconcepcionales.objects.filter(proposito=proposito).first()
    evaluacion_genetica = EvaluacionGenetica.objects.filter(proposito=proposito).first()


    return render(request, "ver_proposito.html", {
        'proposito': proposito,
        'examen_fisico': examen_fisico,
        'padres_info': padres_info,
        'antecedentes_personales': antecedentes_personales,
        'desarrollo_psicomotor': desarrollo_psicomotor,
        'periodo_neonatal': periodo_neonatal,
        'antecedentes_familiares': antecedentes_familiares,
        'evaluacion_genetica': evaluacion_genetica,
        # Add other related data as needed
    })

@login_required
def diagnosticos_plan_estudio(request, historia_id, tipo, objeto_id): # Renamed from `evaluacion_genetica_detalle` for clarity if this is edit view
    historia = get_object_or_404(HistoriasClinicas, historia_id=historia_id)
    proposito_obj, pareja_obj, context_object_name = None, None, ""
    evaluacion_defaults = {} # Not strictly needed for get_or_create if defaults are simple

    if tipo == 'proposito':
        proposito_obj = get_object_or_404(Propositos, proposito_id=objeto_id, historia=historia)
        context_object_name = f"Propósito: {proposito_obj.nombres} {proposito_obj.apellidos}"
        evaluacion, created = EvaluacionGenetica.objects.get_or_create(
            proposito=proposito_obj, 
            defaults={'pareja': None} # Ensure pareja is None if creating for proposito
        )
        if not created and evaluacion.pareja is not None: 
            evaluacion.pareja = None
            evaluacion.proposito = proposito_obj 
            evaluacion.save()

    elif tipo == 'pareja':
        pareja_obj = get_object_or_404(Parejas, pareja_id=objeto_id, proposito_id_1__historia=historia)
        context_object_name = f"Pareja ID: {pareja_obj.pareja_id} ({pareja_obj.proposito_id_1.nombres} y {pareja_obj.proposito_id_2.nombres})"
        evaluacion, created = EvaluacionGenetica.objects.get_or_create(
            pareja=pareja_obj,
            defaults={'proposito': None} # Ensure proposito is None if creating for pareja
        )
        if not created and evaluacion.proposito is not None: 
            evaluacion.proposito = None
            evaluacion.pareja = pareja_obj 
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
                evaluacion_instance = signos_form.save() # EvaluacionGenetica instance

                DiagnosticoPresuntivo.objects.filter(evaluacion=evaluacion_instance).delete()
                for form_diag in diagnostico_formset:
                    if form_diag.is_valid() and form_diag.cleaned_data and not form_diag.cleaned_data.get('DELETE', False):
                        if form_diag.cleaned_data.get('descripcion'):
                            DiagnosticoPresuntivo.objects.create(
                                evaluacion=evaluacion_instance,
                                descripcion=form_diag.cleaned_data['descripcion'],
                                orden=form_diag.cleaned_data.get('orden', 0)
                            )
                
                PlanEstudio.objects.filter(evaluacion=evaluacion_instance).delete()
                for form_plan in plan_formset:
                    if form_plan.is_valid() and form_plan.cleaned_data and not form_plan.cleaned_data.get('DELETE', False):
                        if form_plan.cleaned_data.get('accion'):
                            PlanEstudio.objects.create(
                                evaluacion=evaluacion_instance,
                                accion=form_plan.cleaned_data['accion'],
                                fecha_limite=form_plan.cleaned_data.get('fecha_limite'),
                                completado=form_plan.cleaned_data.get('completado', False)
                            )
            
            messages.success(request, "Evaluación genética guardada exitosamente.")
            # Redirect to a summary or next step
            if tipo == 'proposito' and proposito_obj:
                 return redirect('index')
            # else if tipo == 'pareja', maybe a pareja detail view or back to historia
            return redirect('index') 
        else:
            error_messages = []
            if not signos_form.is_valid(): error_messages.append(f"Errores en Signos Clínicos: {signos_form.errors.as_ul()}")
            if not diagnostico_formset.is_valid(): error_messages.append(f"Errores en Diagnósticos: {diagnostico_formset.non_form_errors().as_ul()} {diagnostico_formset.errors}")
            if not plan_formset.is_valid(): error_messages.append(f"Errores en Plan de Estudio: {plan_formset.non_form_errors().as_ul()} {plan_formset.errors}")
            messages.error(request, "Por favor, corrija los errores en los formularios. " + " | ".join(error_messages))

    else: # GET
        signos_form = SignosClinicosForm(instance=evaluacion)
        
        diagnosticos_initial = [{'descripcion': d.descripcion, 'orden': d.orden} 
                                for d in DiagnosticoPresuntivo.objects.filter(evaluacion=evaluacion).order_by('orden')]
        diagnostico_formset = DiagnosticoPresuntivoFormSet(prefix='diagnosticos', initial=diagnosticos_initial or None) # Ensure at least one empty if none

        planes_initial = [{'accion': p.accion, 'fecha_limite': p.fecha_limite, 'completado': p.completado}
                          for p in PlanEstudio.objects.filter(evaluacion=evaluacion).order_by('pk')] 
        plan_formset = PlanEstudioFormSet(prefix='plans', initial=planes_initial or None)

    context = {
        'historia': historia,
        'tipo': tipo,
        'objeto': proposito_obj or pareja_obj,
        'context_object_name': context_object_name,
        'signos_form': signos_form,
        'diagnostico_formset': diagnostico_formset,
        'plan_formset': plan_formset,
        'evaluacion_instance': evaluacion 
    }
    return render(request, 'diagnosticos_plan.html', context)

# --- AJAX Views ---
@login_required 
def buscar_propositos(request):
    query = request.GET.get('q', '').strip()
    propositos_qs = Propositos.objects.none() 

    if request.user.is_authenticated:
        try:
            genetista = request.user.genetistas # Corrected from Genetistas.DoesNotExist
        except Genetistas.DoesNotExist:
             try:
                genetista = Genetistas.objects.get(user=request.user)
             except Genetistas.DoesNotExist:
                return JsonResponse({'propositos': [], 'error': 'Perfil de genetista no encontrado.'}, status=403)


        if query:
            propositos_qs = Propositos.objects.select_related('historia').filter(
                Q(nombres__icontains=query) | 
                Q(apellidos__icontains=query) |
                Q(identificacion__icontains=query),
                historia__genetista=genetista # Filter by the current genetista
            ).order_by('-historia__fecha_ingreso')[:10] 
        else:
            propositos_qs = Propositos.objects.select_related('historia').filter(
                historia__genetista=genetista
            ).order_by('-historia__fecha_ingreso')[:5]
    
    resultados = [{
        'proposito_id': p.proposito_id,
        'nombres': p.nombres,
        'apellidos': p.apellidos,
        'edad': p.edad,
        'direccion': p.direccion or "N/A",
        'identificacion': p.identificacion,
        'foto_url': p.foto.url if p.foto else None, 
        'fecha_ingreso': p.historia.fecha_ingreso.strftime("%d/%m/%Y %H:%M") if p.historia and p.historia.fecha_ingreso else "--",
        'historia_numero': p.historia.numero_historia if p.historia else "N/A"
    } for p in propositos_qs]
    
    return JsonResponse({'propositos': resultados})


# --- Authentication Views ---
def signup(request):
    if request.method == 'POST':
        form = ExtendedUserCreationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save() 
                    Genetistas.objects.create(user=user) 
                
                login(request, user)
                messages.success(request, "Registro exitoso. ¡Bienvenido!")
                return redirect('index') 
            except IntegrityError: 
                messages.error(request, "El nombre de usuario ya existe o ha ocurrido un error de base de datos.")
            except Exception as e:
                messages.error(request, f"Un error inesperado ocurrió: {e}")
        else:
            # Specific form errors will be displayed by the template
            messages.error(request, "Por favor, corrija los errores en el formulario de registro.")
    else: 
        form = ExtendedUserCreationForm()
    return render(request, "signup.html", {'form': form})
     
def login_medico(request):
    if request.user.is_authenticated:
        return redirect('index') 

    if request.method == 'POST':
        form = LoginForm(request.POST) 
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                try: # Ensure user has a genetista profile
                    _ = user.genetistas # Or Genetistas.objects.get(user=user)
                    login(request, user)
                    messages.info(request, f"Bienvenido de nuevo, {user.username}.")
                    next_url = request.GET.get('next')
                    return redirect(next_url or 'index')
                except Genetistas.DoesNotExist:
                    messages.error(request, "Este usuario no tiene un perfil de genetista asociado.")
            else:
                messages.error(request, "Nombre de usuario o contraseña incorrectos.")
        # No else needed for form invalid, template will show errors
    else: 
        form = LoginForm() 
    
    return render(request, "login.html", {'form': form})
   
def signout(request):
    logout(request)
    messages.success(request, "Has cerrado sesión exitosamente.")
    return redirect('login')


# --- Other/Management Views ---
@login_required
def reports_view(request):
    return render(request, 'reports.html')

@login_required
def gestion_usuarios_view(request):
    # if not request.user.is_superuser:
    #     messages.error(request, "Acceso denegado.")
    #     return redirect('index')
    # users = User.objects.all().select_related('genetistas') # Example
    # context = {'users': users}
    return render(request, 'gestion_usuarios.html') #, context)

# --- Example/Tutorial Views (Consider removing or separating) ---
def index(request): 
    if request.user.is_authenticated:
        try:
            genetista = request.user.genetistas # or Genetistas.objects.get(user=request.user)
            ultimos_propositos = Propositos.objects.filter(historia__genetista=genetista).order_by('-historia__fecha_ingreso')[:5]
            context = {'ultimos_propositos': ultimos_propositos}
            return render(request, "index.html", context)
        except Genetistas.DoesNotExist:
            # Handle case where authenticated user is not a genetista
            # This might happen if a superuser logs in without a Genetistas profile
            logout(request) # Log them out to avoid confusion
            messages.error(request, "Usuario autenticado pero sin perfil de genetista. Sesión cerrada.")
            return redirect('login')

    return render(request, "index.html", {'title': "Sistema de Gestión de Historias Clínicas Genéticas"})


def hello(request, username):
    return JsonResponse({"message": f"Hello {username}"}) 

def about(request):
    return render(request, "about.html", {'username': request.user.username if request.user.is_authenticated else "Invitado"})

@login_required 
def projects(request):
    projects_list = Project.objects.all() 
    return render(request, "projects.html", {'projects': projects_list})

@login_required
def tasks(request):
    tasks_list = Task.objects.all() 
    return render(request, "tasks.html", {'tasks': tasks_list})

@login_required
def create_task(request):
    if request.method == 'POST':
        form = CreateNewTask(request.POST)
        if form.is_valid():
            # Example: Task.objects.create(...)
            messages.success(request, "Tarea creada (ejemplo).")
            return redirect('tasks') # Use URL name
        # No else for form invalid, template shows errors
    else:
        form = CreateNewTask()
    return render(request, 'create_task.html', {'form': form})

@login_required
def create_project(request):
    if request.method == 'POST':
        form = CreateNewProject(request.POST)
        if form.is_valid():
            # Example: Project.objects.create(...)
            messages.success(request, "Proyecto creado (ejemplo).")
            return redirect('projects') # Use URL name
    else:
        form = CreateNewProject()
    return render(request, 'create_project.html', {'form': form})

@login_required
def project_detail(request, id):
    project_instance = get_object_or_404(Project, id=id) 
    project_tasks = Task.objects.filter(project=project_instance)
    return render(request, 'detail.html', {'project': project_instance, 'tasks': project_tasks})