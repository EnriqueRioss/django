from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.exceptions import PermissionDenied
from functools import wraps
import csv
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from .models import (
    Genetistas, Propositos, HistoriasClinicas, InformacionPadres, ExamenFisico,
    Parejas, AntecedentesPersonales, DesarrolloPsicomotor, PeriodoNeonatal,
    AntecedentesFamiliaresPreconcepcionales,
    EvaluacionGenetica, DiagnosticoPresuntivo, PlanEstudio, Project, Task
)
from .forms import (
    ExtendedUserCreationForm, HistoriasForm, PropositosForm, PadresPropositoForm,
    AntecedentesDesarrolloNeonatalForm, AntecedentesPreconcepcionalesForm,
    ExamenFisicoForm, ParejaPropositosForm, SignosClinicosForm,
    DiagnosticoPresuntivoFormSet, PlanEstudioFormSet, LoginForm,
    CreateNewTask, CreateNewProject, ReportSearchForm
)


# --- Role-Based Access Decorators ---
def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            try:
                # Ensure Genetistas profile exists, especially for superusers
                if not hasattr(request.user, 'genetistas'):
                    if request.user.is_superuser:
                        Genetistas.objects.get_or_create(user=request.user) # Create with default role
                        messages.info(request, "Perfil de Genetista creado para superusuario. Por favor, revise y ajuste el rol si es necesario en el panel de administración.")
                    else: # Non-superuser missing profile is an error
                        messages.error(request, "No tiene un perfil de aplicación configurado. Contacte al administrador.")
                        logout(request) # Log out user as they can't proceed
                        return redirect('login')
                
                user_gen_profile = request.user.genetistas
                user_role = user_gen_profile.rol
                
                if not user_role: # Role must be set
                    messages.error(request, "Su perfil de usuario no tiene un rol asignado. Contacte al administrador.")
                    if not request.user.is_superuser: logout(request)
                    return redirect('login')


            except Genetistas.DoesNotExist: # Should be caught by the creation logic above
                messages.error(request, "Error crítico: Perfil de Genetista no encontrado y no se pudo crear.")
                if not request.user.is_superuser: logout(request)
                return redirect('login')

            if user_role not in allowed_roles:
                # Allow superuser to override if they also have an ADM role
                if request.user.is_superuser and user_role == 'ADM' and 'ADM' in allowed_roles:
                    pass # Superuser with ADM role can proceed if ADM is allowed
                elif request.user.is_superuser and user_role == 'ADM' and 'ADM' not in allowed_roles and 'GEN' in allowed_roles and 'LEC' in allowed_roles:
                     # Superuser as ADM trying to access GEN/LEC specific, let them proceed for testing
                    pass
                else:
                    role_names = [dict(Genetistas.ROL_CHOICES).get(r, r) for r in allowed_roles]
                    messages.error(request, f"Acceso denegado. Se requiere rol: {', '.join(role_names)}.")
                    # raise PermissionDenied(f"No tiene permisos suficientes. Su rol: {user_gen_profile.get_rol_display()}. Roles requeridos: {', '.join(role_names)}")
                    return redirect('index') # Redirect to a safe page

            # Specific check for Lector needing an associated genetista for certain views
            if user_role == 'LEC' and not user_gen_profile.associated_genetista:
                # Some views might be accessible to unassociated Lectors, others not.
                # This check can be more granular within views or a separate decorator.
                # For now, allow if 'LEC' is in allowed_roles, view itself should handle data.
                pass
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

admin_required = role_required(['ADM'])
genetista_required = role_required(['GEN', 'ADM']) # Admin can do what Genetista can
lector_required = role_required(['LEC', 'ADM']) # Admin can do what Lector can
genetista_or_admin_required = role_required(['GEN', 'ADM'])
all_roles_required = role_required(['GEN', 'ADM', 'LEC'])


# --- Main Clinical Views ---
@login_required
@genetista_or_admin_required
def crear_historia(request):
    if request.method == 'POST':
        form = HistoriasForm(request.POST)
        if form.is_valid():
            try:
                genetista_profile = request.user.genetistas
                # If admin is creating, historia.genetista can be their own profile or remain None/be selected via form (not current form)
                # If GEN is creating, it's their profile.
            except Genetistas.DoesNotExist: # Should be handled by decorator
                messages.error(request, 'Perfil de genetista no encontrado.')
                return render(request, "historia_clinica.html", {'form1': form})

            historia = form.save(commit=False)
            # Only assign if the current user is a GEN. If ADM, it might be for general record or another GEN.
            # For now, if ADM creates, it's assigned to them. Modify if ADM should select a GEN.
            if genetista_profile.rol == 'GEN' or genetista_profile.rol == 'ADM':
                 historia.genetista = genetista_profile
            
            try:
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
                    messages.warning(request, "Motivo de consulta no mapeado para redirección.")
                    return redirect('index')
            except IntegrityError: 
                 messages.error(request, f"Ya existe una historia clínica con el número '{historia.numero_historia}'.")
                 return render(request, "historia_clinica.html", {'form1': form}) 
        else:
            messages.error(request, "No se pudo crear la historia. Corrija los errores.")
    else: 
        form = HistoriasForm()
    return render(request, "historia_clinica.html", {'form1': form})

@login_required
@genetista_or_admin_required
def crear_paciente(request, historia_id):
    historia = get_object_or_404(HistoriasClinicas, historia_id=historia_id)
    user_profile = request.user.genetistas
    if user_profile.rol == 'GEN' and historia.genetista != user_profile:
        raise PermissionDenied("No tiene permiso para modificar pacientes de esta historia clínica.")
    
    existing_proposito = Propositos.objects.filter(historia=historia).first() # Assumes one proposito per 'Proposito-Diagnóstico' historia

    if request.method == 'POST':
        form = PropositosForm(request.POST, request.FILES, instance=existing_proposito)
        if form.is_valid():
            try:
                proposito = form.save(historia=historia) 
                action_verb = 'actualizado' if existing_proposito else 'creado'
                messages.success(request, f"Paciente {proposito.nombres} {proposito.apellidos} {action_verb} exitosamente.")
                return redirect('padres_proposito_crear', historia_id=historia.historia_id, proposito_id=proposito.proposito_id)
            except IntegrityError as e:
                messages.error(request, f"Error de integridad al guardar el paciente: {e}.")
            except Exception as e:
                messages.error(request, f"Error inesperado al guardar el paciente: {e}")
        else:
            messages.error(request, "No se pudo guardar el paciente. Corrija los errores.")
    else: 
        form = PropositosForm(instance=existing_proposito) 
        if existing_proposito:
            messages.info(request, f"Editando información para: {existing_proposito.nombres} {existing_proposito.apellidos}")
    return render(request, "Crear_paciente.html", {'form': form, 'historia': historia, 'editing': bool(existing_proposito)})

@login_required
@genetista_or_admin_required
def crear_pareja(request, historia_id):
    historia = get_object_or_404(HistoriasClinicas, historia_id=historia_id)
    user_profile = request.user.genetistas
    if user_profile.rol == 'GEN' and historia.genetista != user_profile:
        # This check might need refinement if a Pareja's Propositos can belong to different Genetistas.
        # For now, assume the Historia's Genetista is the primary owner.
        raise PermissionDenied("No tiene permiso para modificar parejas de esta historia clínica.")

    if request.method == 'POST':
        form = ParejaPropositosForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    def get_or_create_proposito_from_form(form_cleaned_data, prefix_num, historia_obj):
                        identificacion = form_cleaned_data[f'identificacion_{prefix_num}']
                        proposito_data = {
                            'historia': historia_obj, # Associate with this specific historia
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
                            'grupo_sanguineo': form_cleaned_data.get(f'grupo_sanguineo_{prefix_num}') or None,
                            'factor_rh': form_cleaned_data.get(f'factor_rh_{prefix_num}') or None,
                        }
                        proposito_defaults = {k: v for k, v in proposito_data.items() if v is not None or k == 'historia'}
                        
                        # Ensure this Proposito is linked to the correct historia, especially if updating an existing one
                        # that might have been (incorrectly) linked to another historia.
                        proposito_defaults['historia'] = historia_obj 

                        proposito, created = Propositos.objects.update_or_create(
                            identificacion=identificacion,
                            defaults=proposito_defaults
                        )
                        # If it was an update and the historia was different, ensure it's now correct.
                        if not created and proposito.historia != historia_obj:
                            proposito.historia = historia_obj
                            # proposito.save(update_fields=['historia']) # Done by update_or_create if 'historia' in defaults

                        foto_val = form_cleaned_data.get(f'foto_{prefix_num}')
                        if foto_val is not None:
                            if foto_val: proposito.foto = foto_val
                            elif foto_val is False: proposito.foto = None 
                            proposito.save(update_fields=['foto'])
                        elif created and proposito.foto is not None: # New proposito, no photo submitted, but somehow instance had one
                            proposito.foto = None
                            proposito.save(update_fields=['foto'])
                        return proposito

                    proposito1 = get_or_create_proposito_from_form(form.cleaned_data, '1', historia)
                    proposito2 = get_or_create_proposito_from_form(form.cleaned_data, '2', historia)

                    if proposito1.pk == proposito2.pk: 
                        raise IntegrityError("Los dos miembros de la pareja no pueden ser la misma persona.")

                    # Ensure consistent ordering for Parejas model's unique_together
                    p_min, p_max = sorted([proposito1, proposito2], key=lambda p: p.pk)
                    pareja, pareja_created = Parejas.objects.get_or_create(
                        proposito_id_1=p_min,
                        proposito_id_2=p_max
                        # No defaults needed here, as the key is the pair of propositos
                    )
                action_verb = 'creada' if pareja_created else 'localizada/actualizada'
                messages.success(request, f"Pareja ({proposito1.nombres} y {proposito2.nombres}) {action_verb} exitosamente.")
                return redirect('antecedentes_personales_crear',
                                 historia_id=historia.historia_id,
                                 tipo="pareja",
                                 objeto_id=pareja.pareja_id)
            except IntegrityError as e:
                 messages.error(request, f"Error de integridad al guardar la pareja: {e}. Verifique identificaciones.")
            except Exception as e:
                messages.error(request, f"Error inesperado al guardar la pareja: {e}")
        else:
            messages.error(request, "No se pudo guardar la pareja. Corrija los errores.")
    else: 
        form = ParejaPropositosForm()
    return render(request, 'Crear_pareja.html', {'form': form, 'historia': historia})

@login_required
@genetista_or_admin_required
def padres_proposito(request, historia_id, proposito_id):
    historia = get_object_or_404(HistoriasClinicas, historia_id=historia_id)
    proposito = get_object_or_404(Propositos, proposito_id=proposito_id, historia=historia)
    user_profile = request.user.genetistas
    if user_profile.rol == 'GEN' and proposito.historia.genetista != user_profile:
        raise PermissionDenied("No tiene permiso para modificar esta información.")

    if request.method == 'POST':
        form = PadresPropositoForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    padre_defaults = {k[len('padre_'):]: v for k, v in form.cleaned_data.items() if k.startswith('padre_')}
                    padre_defaults_clean = {k:v for k,v in padre_defaults.items() if v is not None or k in ['nombres','apellidos']} # Ensure required fields are kept even if None temporarily
                    padre_defaults_clean['grupo_sanguineo'] = padre_defaults_clean.get('grupo_sanguineo') or None
                    padre_defaults_clean['factor_rh'] = padre_defaults_clean.get('factor_rh') or None

                    InformacionPadres.objects.update_or_create(
                        proposito=proposito, tipo='Padre',
                        defaults=padre_defaults_clean
                    )

                    madre_defaults = {k[len('madre_'):]: v for k, v in form.cleaned_data.items() if k.startswith('madre_')}
                    madre_defaults_clean = {k:v for k,v in madre_defaults.items() if v is not None or k in ['nombres','apellidos']}
                    madre_defaults_clean['grupo_sanguineo'] = madre_defaults_clean.get('grupo_sanguineo') or None
                    madre_defaults_clean['factor_rh'] = madre_defaults_clean.get('factor_rh') or None

                    InformacionPadres.objects.update_or_create(
                        proposito=proposito, tipo='Madre',
                        defaults=madre_defaults_clean
                    )
                messages.success(request, "Información de los padres guardada/actualizada.")
                return redirect('antecedentes_personales_crear',
                                historia_id=historia_id,
                                tipo='proposito',
                                objeto_id=proposito_id)
            except Exception as e:
                messages.error(request, f"Error al guardar información de padres: {e}")
        else:
            messages.error(request, "No se pudo guardar información de padres. Corrija errores.")
    else: 
        padre = InformacionPadres.objects.filter(proposito=proposito, tipo='Padre').first()
        madre = InformacionPadres.objects.filter(proposito=proposito, tipo='Madre').first()
        initial_data = {}
        if padre: initial_data.update({f'padre_{f.name}': getattr(padre, f.name) for f in InformacionPadres._meta.fields if f.name not in ['padre_id', 'proposito', 'tipo'] and hasattr(padre, f.name)})
        if madre: initial_data.update({f'madre_{f.name}': getattr(madre, f.name) for f in InformacionPadres._meta.fields if f.name not in ['padre_id', 'proposito', 'tipo'] and hasattr(madre, f.name)})
        form = PadresPropositoForm(initial=initial_data if initial_data else None)
        if initial_data: messages.info(request, "Editando información de padres.")
    return render(request, "Padres_proposito.html", {'form': form, 'historia': historia, 'proposito': proposito})


@login_required
@genetista_or_admin_required
def crear_antecedentes_personales(request, historia_id, tipo, objeto_id):
    historia = get_object_or_404(HistoriasClinicas, historia_id=historia_id)
    proposito_obj, pareja_obj, context_object_name = None, None, ""
    editing = False 
    user_gen_profile = request.user.genetistas

    if tipo == 'proposito':
        proposito_obj = get_object_or_404(Propositos, proposito_id=objeto_id, historia=historia)
        if user_gen_profile.rol == 'GEN' and proposito_obj.historia.genetista != user_gen_profile:
            raise PermissionDenied("No tiene permiso para esta acción.")
        context_object_name = f"{proposito_obj.nombres} {proposito_obj.apellidos}"
        if AntecedentesPersonales.objects.filter(proposito=proposito_obj).exists() or \
           DesarrolloPsicomotor.objects.filter(proposito=proposito_obj).exists() or \
           PeriodoNeonatal.objects.filter(proposito=proposito_obj).exists():
            editing = True
    elif tipo == 'pareja':
        pareja_obj = get_object_or_404(Parejas, pareja_id=objeto_id)
        # Ensure pareja is linked to the current historia's genetista if user is GEN
        if user_gen_profile.rol == 'GEN':
            p1_hist_gen = pareja_obj.proposito_id_1.historia.genetista if pareja_obj.proposito_id_1.historia else None
            p2_hist_gen = pareja_obj.proposito_id_2.historia.genetista if pareja_obj.proposito_id_2 and pareja_obj.proposito_id_2.historia else None
            if not (p1_hist_gen == user_gen_profile or p2_hist_gen == user_gen_profile):
                 raise PermissionDenied("No tiene permiso para esta acción sobre la pareja.")
        context_object_name = f"Pareja ID: {pareja_obj.pareja_id}"
        if AntecedentesPersonales.objects.filter(pareja=pareja_obj).exists() or \
           DesarrolloPsicomotor.objects.filter(pareja=pareja_obj).exists() or \
           PeriodoNeonatal.objects.filter(pareja=pareja_obj).exists():
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
                form.save(proposito=target_proposito, pareja=target_pareja) 
                action_verb = "actualizados" if editing else "guardados"
                messages.success(request, f"Antecedentes personales y desarrollo {action_verb} para {context_object_name}.")
                return redirect('antecedentes_preconcepcionales_crear', historia_id=historia.historia_id, tipo=tipo, objeto_id=objeto_id)
            except Exception as e:
                messages.error(request, f'Error al guardar antecedentes: {str(e)}')
        else:
            messages.error(request, "No se pudieron guardar los antecedentes. Corrija errores.")
    else: 
        initial_data = {}
        if editing: 
            # Code to populate initial_data from existing instances... (as before)
            ap_instance, dp_instance, pn_instance = None, None, None
            if tipo == 'proposito' and proposito_obj:
                ap_instance = AntecedentesPersonales.objects.filter(proposito=proposito_obj).first()
                dp_instance = DesarrolloPsicomotor.objects.filter(proposito=proposito_obj).first()
                pn_instance = PeriodoNeonatal.objects.filter(proposito=proposito_obj).first()
            elif tipo == 'pareja' and pareja_obj:
                ap_instance = AntecedentesPersonales.objects.filter(pareja=pareja_obj).first()
                dp_instance = DesarrolloPsicomotor.objects.filter(pareja=pareja_obj).first()
                pn_instance = PeriodoNeonatal.objects.filter(pareja=pareja_obj).first()

            if ap_instance: initial_data.update({f.name: getattr(ap_instance, f.name) for f in AntecedentesPersonales._meta.fields if hasattr(ap_instance, f.name) and f.name not in ['antecedente_id', 'proposito', 'pareja']})
            if dp_instance: initial_data.update({f.name: getattr(dp_instance, f.name) for f in DesarrolloPsicomotor._meta.fields if hasattr(dp_instance, f.name) and f.name not in ['desarrollo_id', 'proposito', 'pareja']})
            if pn_instance: initial_data.update({f.name: getattr(pn_instance, f.name) for f in PeriodoNeonatal._meta.fields if hasattr(pn_instance, f.name) and f.name not in ['neonatal_id', 'proposito', 'pareja']})
            if initial_data: messages.info(request, f"Editando antecedentes para {context_object_name}.")
        form = AntecedentesDesarrolloNeonatalForm(initial=initial_data if initial_data else None)

    context = {'form': form, 'historia': historia, 'tipo': tipo, 'objeto': proposito_obj or pareja_obj, 'context_object_name': context_object_name, 'editing': editing}
    return render(request, 'antecedentes_personales.html', context)

@login_required
@genetista_or_admin_required
def crear_antecedentes_preconcepcionales(request, historia_id, tipo, objeto_id):
    historia = get_object_or_404(HistoriasClinicas, historia_id=historia_id)
    proposito_obj, pareja_obj, context_object_name = None, None, ""
    instance_to_edit = None
    user_gen_profile = request.user.genetistas

    if tipo == 'proposito':
        proposito_obj = get_object_or_404(Propositos, proposito_id=objeto_id, historia=historia)
        if user_gen_profile.rol == 'GEN' and proposito_obj.historia.genetista != user_gen_profile:
            raise PermissionDenied("No tiene permiso para esta acción.")
        context_object_name = f"{proposito_obj.nombres} {proposito_obj.apellidos}"
        instance_to_edit = AntecedentesFamiliaresPreconcepcionales.objects.filter(proposito=proposito_obj).first()
    elif tipo == 'pareja':
        pareja_obj = get_object_or_404(Parejas, pareja_id=objeto_id)
        if user_gen_profile.rol == 'GEN':
            p1_hist_gen = pareja_obj.proposito_id_1.historia.genetista if pareja_obj.proposito_id_1.historia else None
            p2_hist_gen = pareja_obj.proposito_id_2.historia.genetista if pareja_obj.proposito_id_2 and pareja_obj.proposito_id_2.historia else None
            if not (p1_hist_gen == user_gen_profile or p2_hist_gen == user_gen_profile) :
                 raise PermissionDenied("No tiene permiso para esta acción sobre la pareja.")
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
                form.save(proposito=target_proposito, pareja=target_pareja, tipo=tipo) 
                action_verb = "actualizados" if instance_to_edit else "guardados"
                messages.success(request, f"Antecedentes preconcepcionales {action_verb} para {context_object_name}.")
                if tipo == 'proposito' and proposito_obj:
                    return redirect('examen_fisico_crear_editar', proposito_id=proposito_obj.proposito_id)
                elif tipo == 'pareja' and pareja_obj:
                    return redirect('evaluacion_genetica_detalle', historia_id=historia.historia_id, tipo="pareja", objeto_id=pareja_obj.pareja_id)
                else: return redirect('index')
            except Exception as e:
                messages.error(request, f'Error al guardar antec. preconcepcionales: {str(e)}')
        else:
            messages.error(request, "No se pudieron guardar antec. preconcepcionales. Corrija errores.")
    else: 
        initial_data = {}
        if instance_to_edit:
            initial_data = {f.name: getattr(instance_to_edit, f.name) for f in AntecedentesFamiliaresPreconcepcionales._meta.fields if hasattr(instance_to_edit, f.name) and f.name not in ['antecedente_familiar_id', 'proposito', 'pareja']}
            if initial_data: messages.info(request, f"Editando antec. preconcepcionales para {context_object_name}.")
        form = AntecedentesPreconcepcionalesForm(initial=initial_data if initial_data else None)

    context = {'form': form, 'historia': historia, 'tipo': tipo, 'objeto': proposito_obj or pareja_obj, 'context_object_name': context_object_name, 'editing': bool(instance_to_edit)}
    return render(request, 'antecedentes_preconcepcionales.html', context)

@login_required
@genetista_or_admin_required
def crear_examen_fisico(request, proposito_id):
    proposito = get_object_or_404(Propositos, pk=proposito_id)
    user_profile = request.user.genetistas
    if user_profile.rol == 'GEN' and proposito.historia.genetista != user_profile:
        raise PermissionDenied("No tiene permiso para modificar el examen físico de este propósito.")

    examen_existente = ExamenFisico.objects.filter(proposito=proposito).first()

    if request.method == 'POST':
        form = ExamenFisicoForm(request.POST, instance=examen_existente)
        form.proposito_instance = proposito 
        if form.is_valid():
            form.save()
            action_verb = "actualizado" if examen_existente else "guardado"
            messages.success(request, f"Examen físico para {proposito.nombres} {action_verb}.")
            return redirect('evaluacion_genetica_detalle', historia_id=proposito.historia.historia_id, tipo="proposito", objeto_id=proposito.proposito_id)
        else:
            messages.error(request, "No se pudo guardar Examen Físico. Corrija errores.")
    else: 
        form = ExamenFisicoForm(instance=examen_existente)
        if examen_existente: messages.info(request, f"Editando examen físico para {proposito.nombres}.")
    return render(request, 'examen_fisico.html', {'form': form, 'proposito': proposito, 'editing': bool(examen_existente)})

@login_required
@all_roles_required # All roles can view, but data scoped inside
def ver_proposito(request, proposito_id):
    proposito = get_object_or_404(Propositos, pk=proposito_id)
    user_gen_profile = request.user.genetistas

    if user_gen_profile.rol == 'GEN' and proposito.historia.genetista != user_gen_profile:
        raise PermissionDenied("No tiene permiso para ver este propósito.")
    elif user_gen_profile.rol == 'LEC':
        if not user_gen_profile.associated_genetista or \
           proposito.historia.genetista != user_gen_profile.associated_genetista:
            raise PermissionDenied("No tiene permiso para ver este propósito.")
    # ADM can see all

    # Fetch related data (as before)
    examen_fisico = ExamenFisico.objects.filter(proposito=proposito).first()
    padres_info = InformacionPadres.objects.filter(proposito=proposito)
    antecedentes_personales = AntecedentesPersonales.objects.filter(proposito=proposito).first()
    desarrollo_psicomotor = DesarrolloPsicomotor.objects.filter(proposito=proposito).first()
    periodo_neonatal = PeriodoNeonatal.objects.filter(proposito=proposito).first()
    antecedentes_familiares = AntecedentesFamiliaresPreconcepcionales.objects.filter(proposito=proposito).first()
    evaluacion_genetica = EvaluacionGenetica.objects.filter(proposito=proposito).first()
    diagnosticos, planes_estudio = [], []
    if evaluacion_genetica:
        diagnosticos = DiagnosticoPresuntivo.objects.filter(evaluacion=evaluacion_genetica).order_by('orden')
        planes_estudio = PlanEstudio.objects.filter(evaluacion=evaluacion_genetica).order_by('pk')

    return render(request, "ver_proposito.html", {
        'proposito': proposito, 'examen_fisico': examen_fisico,
        'padres_info': {p.tipo: p for p in padres_info},
        'antecedentes_personales': antecedentes_personales,
        'desarrollo_psicomotor': desarrollo_psicomotor, 'periodo_neonatal': periodo_neonatal,
        'antecedentes_familiares': antecedentes_familiares, 'evaluacion_genetica': evaluacion_genetica,
        'diagnosticos_presuntivos': diagnosticos, 'planes_estudio': planes_estudio,
    })

@login_required
@genetista_or_admin_required
def diagnosticos_plan_estudio(request, historia_id, tipo, objeto_id):
    historia = get_object_or_404(HistoriasClinicas, historia_id=historia_id)
    proposito_obj, pareja_obj, context_object_name = None, None, ""
    user_gen_profile = request.user.genetistas

    if user_gen_profile.rol == 'GEN' and historia.genetista != user_gen_profile:
        raise PermissionDenied("No tiene permiso para acceder a la evaluación de esta historia.")

    if tipo == 'proposito':
        proposito_obj = get_object_or_404(Propositos, proposito_id=objeto_id, historia=historia)
        context_object_name = f"Propósito: {proposito_obj.nombres} {proposito_obj.apellidos}"
        evaluacion, created = EvaluacionGenetica.objects.get_or_create(proposito=proposito_obj, defaults={'pareja': None})
        if not created and evaluacion.pareja is not None: evaluacion.pareja = None; evaluacion.proposito = proposito_obj; evaluacion.save()
    elif tipo == 'pareja':
        pareja_obj = get_object_or_404(Parejas, pareja_id=objeto_id)
        # Add security check for pareja related to historia for GEN role
        if user_gen_profile.rol == 'GEN':
             p1_hist_gen = pareja_obj.proposito_id_1.historia.genetista if pareja_obj.proposito_id_1.historia else None
             p2_hist_gen = pareja_obj.proposito_id_2.historia.genetista if pareja_obj.proposito_id_2 and pareja_obj.proposito_id_2.historia else None
             if not (p1_hist_gen == user_gen_profile or p2_hist_gen == user_gen_profile):
                  raise PermissionDenied("La pareja no está asociada con su perfil de genetista.")
        context_object_name = f"Pareja ID: {pareja_obj.pareja_id} ({pareja_obj.proposito_id_1.nombres} y {pareja_obj.proposito_id_2.nombres})"
        evaluacion, created = EvaluacionGenetica.objects.get_or_create(pareja=pareja_obj, defaults={'proposito': None})
        if not created and evaluacion.proposito is not None: evaluacion.proposito = None; evaluacion.pareja = pareja_obj; evaluacion.save()
    else:
        messages.error(request, "Tipo de objeto no válido para evaluación genética.")
        return redirect('index')

    if request.method == 'POST':
        signos_form = SignosClinicosForm(request.POST, instance=evaluacion)
        diagnostico_formset = DiagnosticoPresuntivoFormSet(request.POST, prefix='diagnosticos')
        plan_formset = PlanEstudioFormSet(request.POST, prefix='plans')

        if signos_form.is_valid() and diagnostico_formset.is_valid() and plan_formset.is_valid():
            with transaction.atomic():
                evaluacion_instance = signos_form.save()
                DiagnosticoPresuntivo.objects.filter(evaluacion=evaluacion_instance).delete()
                for form_data_diag in diagnostico_formset.cleaned_data: 
                    if form_data_diag and not form_data_diag.get('DELETE', False) and form_data_diag.get('descripcion'): 
                        DiagnosticoPresuntivo.objects.create(evaluacion=evaluacion_instance, descripcion=form_data_diag['descripcion'], orden=form_data_diag.get('orden', 0))
                PlanEstudio.objects.filter(evaluacion=evaluacion_instance).delete()
                for form_data_plan in plan_formset.cleaned_data: 
                    if form_data_plan and not form_data_plan.get('DELETE', False) and form_data_plan.get('accion'): 
                        PlanEstudio.objects.create(evaluacion=evaluacion_instance, accion=form_data_plan['accion'], fecha_limite=form_data_plan.get('fecha_limite'), completado=form_data_plan.get('completado', False))
            messages.success(request, "Evaluación genética guardada.")
            messages.info(request, "POPUP:Historia Clínica Genética completada y guardada.") 
            return redirect('index')
        else:
            # Error reporting logic (as before)
            error_msg_list = []
            if not signos_form.is_valid(): error_msg_list.append(f"Errores en Signos Clínicos: {signos_form.errors.as_ul()}")
            if not diagnostico_formset.is_valid(): error_msg_list.append(f"Errores en Diagnósticos: {diagnostico_formset.non_form_errors().as_ul()} {diagnostico_formset.errors}")
            if not plan_formset.is_valid(): error_msg_list.append(f"Errores en Plan: {plan_formset.non_form_errors().as_ul()} {plan_formset.errors}")
            messages.error(request, "No se pudo guardar Evaluación. Corrija errores. " + " ".join(error_msg_list))
    else: 
        signos_form = SignosClinicosForm(instance=evaluacion)
        diagnosticos_initial = [{'descripcion': d.descripcion, 'orden': d.orden} for d in DiagnosticoPresuntivo.objects.filter(evaluacion=evaluacion).order_by('orden')]
        diagnostico_formset = DiagnosticoPresuntivoFormSet(prefix='diagnosticos', initial=diagnosticos_initial or [{'orden':0}])
        planes_initial = [{'accion': p.accion, 'fecha_limite': p.fecha_limite, 'completado': p.completado} for p in PlanEstudio.objects.filter(evaluacion=evaluacion).order_by('pk')] 
        plan_formset = PlanEstudioFormSet(prefix='plans', initial=planes_initial or [{}])
        if created: messages.info(request, "Iniciando nueva evaluación genética.")
        else: messages.info(request, f"Editando evaluación para {context_object_name}.")

    context = {'historia': historia, 'tipo': tipo, 'objeto': proposito_obj or pareja_obj, 'context_object_name': context_object_name, 'signos_form': signos_form, 'diagnostico_formset': diagnostico_formset, 'plan_formset': plan_formset, 'evaluacion_instance': evaluacion}
    return render(request, 'diagnosticos_plan.html', context)

# --- AJAX Views ---
@login_required
@all_roles_required # Search is available to all, results are scoped
def buscar_propositos(request):
    query = request.GET.get('q', '').strip()
    propositos_qs = Propositos.objects.none()
    
    try:
        user_gen_profile = request.user.genetistas
    except Genetistas.DoesNotExist: # Should be handled by decorator
        return JsonResponse({'propositos': [], 'error': 'Perfil de genetista no encontrado.'}, status=403)

    base_query = Propositos.objects.select_related('historia', 'historia__genetista__user')

    if user_gen_profile.rol == 'ADM' or request.user.is_superuser:
        propositos_qs = base_query.filter(historia__isnull=False)
    elif user_gen_profile.rol == 'GEN':
        propositos_qs = base_query.filter(historia__genetista=user_gen_profile)
    elif user_gen_profile.rol == 'LEC':
        if user_gen_profile.associated_genetista:
            propositos_qs = base_query.filter(historia__genetista=user_gen_profile.associated_genetista)
        else: propositos_qs = Propositos.objects.none()
    else: propositos_qs = Propositos.objects.none()

    if query:
        propositos_qs = propositos_qs.filter(
            Q(nombres__icontains=query) | Q(apellidos__icontains=query) | Q(identificacion__icontains=query)
        )
    
    propositos_qs = propositos_qs.order_by('-historia__fecha_ingreso')[:10 if query else 5]
    resultados = [{
        'proposito_id': p.proposito_id, 'nombres': p.nombres, 'apellidos': p.apellidos,
        'edad': p.edad, 'direccion': p.direccion or "N/A", 'identificacion': p.identificacion,
        'foto_url': p.foto.url if p.foto else None,
        'fecha_ingreso': p.historia.fecha_ingreso.strftime("%d/%m/%Y %H:%M") if p.historia and p.historia.fecha_ingreso else "--",
        'historia_numero': p.historia.numero_historia if p.historia else "N/A",
        'genetista_nombre': p.historia.genetista.user.get_full_name() or p.historia.genetista.user.username if p.historia and p.historia.genetista else "N/A"
    } for p in propositos_qs]
    return JsonResponse({'propositos': resultados})


# --- Authentication Views ---
def signup(request):
    if request.user.is_authenticated: return redirect('index')
    if request.method == 'POST':
        form = ExtendedUserCreationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    # Genetistas profile created by post_save signal (default role 'GEN')
                login(request, user)
                messages.success(request, "Registro exitoso. ¡Bienvenido!")
                return redirect('index')
            except IntegrityError: messages.error(request, "Nombre de usuario ya existe o error de BD.")
            except Exception as e: messages.error(request, f"Error inesperado: {e}")
        else: messages.error(request, "No se pudo completar registro. Corrija errores.")
    else: form = ExtendedUserCreationForm()
    return render(request, "signup.html", {'form': form})

def login_medico(request):
    if request.user.is_authenticated: return redirect('index')
    if request.method == 'POST':
        form = LoginForm(request.POST) 
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                try:
                    gen_profile = getattr(user, 'genetistas', None)
                    if not gen_profile: # Attempt to create if missing, e.g. for superuser
                        if user.is_superuser:
                           gen_profile, _ = Genetistas.objects.get_or_create(user=user)
                        else: # Non-superuser must have one
                           messages.error(request, "Perfil de aplicación no encontrado. Contacte al admin.")
                           return render(request, "login.html", {'form': form})
                    
                    if not gen_profile.rol:
                        messages.error(request, "El perfil no tiene un rol asignado. Contacte al admin.")
                        return render(request, "login.html", {'form': form})

                    login(request, user)
                    messages.info(request, f"Bienvenido, {user.get_full_name() or user.username} ({gen_profile.get_rol_display()}).")
                    return redirect(request.GET.get('next') or 'index')
                except Genetistas.DoesNotExist: # Should be caught by getattr
                     messages.error(request, "Este usuario no tiene un perfil de genetista. Contacte al admin.")
            else: messages.error(request, "Usuario o contraseña incorrectos.")
        else: messages.error(request, "Ingrese usuario y contraseña válidos.")
    else: form = LoginForm()
    return render(request, "login.html", {'form': form})

def signout(request):
    logout(request)
    messages.success(request, "Sesión cerrada exitosamente.")
    return redirect('login')


# --- Other/Management Views ---
@login_required
@all_roles_required # View itself is accessible, data/actions within are permissioned by form/export logic
def reports_view(request):
    form = ReportSearchForm(request.GET or None, user=request.user)
    results = []
    applied_filters_display = {}
    search_attempted = bool(request.GET) # Search is attempted if there are GET params
    
    if form.is_valid():
        # Logic for fetching and filtering propositos_qs as before...
        query_paciente = form.cleaned_data.get('buscar_paciente')
        date_range_val = form.cleaned_data.get('date_range')
        tipo_registro = form.cleaned_data.get('tipo_registro')
        genetista_obj_from_form = form.cleaned_data.get('genetista') # Form handles scoping

        propositos_qs = Propositos.objects.filter(historia__isnull=False) \
                                          .select_related('historia', 'historia__genetista', 'historia__genetista__user') \
                                          .order_by('historia__numero_historia', 'apellidos', 'nombres')
        
        user_gen_profile = request.user.genetistas # Assumed to exist by decorator

        # Filter by genetista based on form's selection (which is already role-scoped)
        if genetista_obj_from_form:
            propositos_qs = propositos_qs.filter(historia__genetista=genetista_obj_from_form)
            applied_filters_display['Genetista'] = genetista_obj_from_form.user.get_full_name() or genetista_obj_from_form.user.username
        elif user_gen_profile.rol == 'GEN': # If GEN and form didn't force one (should not happen if form is correct)
            propositos_qs = propositos_qs.filter(historia__genetista=user_gen_profile)
            applied_filters_display['Genetista'] = user_gen_profile.user.get_full_name() or user_gen_profile.user.username
        elif user_gen_profile.rol == 'LEC':
            if user_gen_profile.associated_genetista:
                propositos_qs = propositos_qs.filter(historia__genetista=user_gen_profile.associated_genetista)
                applied_filters_display['Genetista'] = user_gen_profile.associated_genetista.user.get_full_name() or user_gen_profile.associated_genetista.user.username
            else:
                propositos_qs = Propositos.objects.none()
        # ADM without a specific genetista selected sees all (or form forces selection)

        if query_paciente:
            propositos_qs = propositos_qs.filter(
                Q(nombres__icontains=query_paciente) | Q(apellidos__icontains=query_paciente) | Q(identificacion__icontains=query_paciente)
            )
            applied_filters_display['Paciente'] = query_paciente
        
        if date_range_val:
            fecha_desde, fecha_hasta = date_range_val.get('desde'), date_range_val.get('hasta')
            if fecha_desde: propositos_qs = propositos_qs.filter(historia__fecha_ingreso__date__gte=fecha_desde); applied_filters_display['Fecha Desde'] = fecha_desde.strftime('%d/%m/%Y')
            if fecha_hasta: propositos_qs = propositos_qs.filter(historia__fecha_ingreso__date__lte=fecha_hasta); applied_filters_display['Fecha Hasta'] = fecha_hasta.strftime('%d/%m/%Y')
        
        temp_results = []
        for p in propositos_qs:
            historia = p.historia
            is_pareja_member = Parejas.objects.filter(Q(proposito_id_1=p) | Q(proposito_id_2=p)).exists()
            item_tipo = 'Pareja' if is_pareja_member else 'Propósito'
            if (tipo_registro == 'proposito' and is_pareja_member) or \
               (tipo_registro == 'pareja' and not is_pareja_member):
                continue
            genetista_user = historia.genetista.user if historia.genetista else None
            genetista_name = genetista_user.get_full_name() or genetista_user.username if genetista_user else "N/A"
            temp_results.append({
                'id_historia': historia.numero_historia, 'paciente_nombre': f"{p.nombres} {p.apellidos}",
                'paciente_id': p.proposito_id, 'edad': p.edad if p.edad is not None else 'N/A', 'tipo': item_tipo,
                'genetista_nombre': genetista_name,
                'fecha_ingreso': historia.fecha_ingreso.strftime('%d-%m-%Y') if historia.fecha_ingreso else 'N/A',
                'is_pareja_member_css_class': 'pareja-row' if is_pareja_member else ''
            })
        results = temp_results
        if tipo_registro: applied_filters_display['Tipo de Registro'] = dict(form.fields['tipo_registro'].choices).get(tipo_registro)
    else: # Form is not valid or not submitted with GET params for search
        if request.GET: # If there were GET params but form invalid
            messages.error(request, "Filtros inválidos. Mostrando todos los resultados permitidos.")
        # Show some default data or empty based on role if no search is made
        # This part is covered by how 'ultimos_propositos' is handled in index_view
        pass


    context = {'form': form, 'results': results, 'search_attempted': search_attempted, 'applied_filters_display': applied_filters_display}
    return render(request, 'reports.html', context)


@login_required
@all_roles_required # Export is available to all, data is scoped
def export_report_data(request, export_format):
    # ... (Logic for fetching and filtering propositos_qs, identical to reports_view)
    form = ReportSearchForm(request.GET or None, user=request.user)
    if not form.is_valid():
        return HttpResponse("Filtros inválidos para exportación.", status=400)

    query_paciente = form.cleaned_data.get('buscar_paciente')
    date_range_val = form.cleaned_data.get('date_range')
    tipo_registro = form.cleaned_data.get('tipo_registro')
    genetista_obj_from_form = form.cleaned_data.get('genetista')
    
    applied_filters_display = {}
    propositos_qs = Propositos.objects.filter(historia__isnull=False) \
                                      .select_related('historia', 'historia__genetista', 'historia__genetista__user') \
                                      .order_by('historia__numero_historia', 'apellidos', 'nombres')
    user_gen_profile = request.user.genetistas

    if genetista_obj_from_form:
        propositos_qs = propositos_qs.filter(historia__genetista=genetista_obj_from_form)
        applied_filters_display['Genetista'] = genetista_obj_from_form.user.get_full_name() or genetista_obj_from_form.user.username
    # ... (rest of the filtering logic from reports_view) ...
    elif user_gen_profile.rol == 'GEN':
        propositos_qs = propositos_qs.filter(historia__genetista=user_gen_profile)
        applied_filters_display['Genetista'] = user_gen_profile.user.get_full_name() or user_gen_profile.user.username
    elif user_gen_profile.rol == 'LEC':
        if user_gen_profile.associated_genetista:
            propositos_qs = propositos_qs.filter(historia__genetista=user_gen_profile.associated_genetista)
            applied_filters_display['Genetista'] = user_gen_profile.associated_genetista.user.get_full_name() or user_gen_profile.associated_genetista.user.username
        else:
            propositos_qs = Propositos.objects.none()
    
    if query_paciente:
        propositos_qs = propositos_qs.filter(
            Q(nombres__icontains=query_paciente) | Q(apellidos__icontains=query_paciente) | Q(identificacion__icontains=query_paciente)
        )
        applied_filters_display['Paciente'] = query_paciente
    
    if date_range_val:
        fecha_desde, fecha_hasta = date_range_val.get('desde'), date_range_val.get('hasta')
        if fecha_desde: 
            propositos_qs = propositos_qs.filter(historia__fecha_ingreso__date__gte=fecha_desde)
            applied_filters_display['Fecha Desde'] = fecha_desde.strftime('%d/%m/%Y')
        if fecha_hasta: 
            propositos_qs = propositos_qs.filter(historia__fecha_ingreso__date__lte=fecha_hasta)
            applied_filters_display['Fecha Hasta'] = fecha_hasta.strftime('%d/%m/%Y')

    if tipo_registro:
        applied_filters_display['Tipo de Registro'] = dict(form.fields['tipo_registro'].choices).get(tipo_registro)

    report_data = []
    for p in propositos_qs:
        # ... (data assembly logic from reports_view)
        historia = p.historia
        is_pareja_member = Parejas.objects.filter(Q(proposito_id_1=p) | Q(proposito_id_2=p)).exists()
        item_tipo = 'Pareja' if is_pareja_member else 'Propósito'
        if (tipo_registro == 'proposito' and is_pareja_member) or \
           (tipo_registro == 'pareja' and not is_pareja_member):
            continue
        genetista_user = historia.genetista.user if historia.genetista else None
        genetista_name = genetista_user.get_full_name() or genetista_user.username if genetista_user else "N/A"
        report_data.append({
            'ID Historia': historia.numero_historia, 'Paciente': f"{p.nombres} {p.apellidos}",
            'Edad': p.edad if p.edad is not None else 'N/A', 'Tipo': item_tipo, 'Genetista': genetista_name,
            'Fecha Ingreso': historia.fecha_ingreso.strftime('%d-%m-%Y') if historia.fecha_ingreso else 'N/A',
        })

    if export_format == 'csv':
        # ... (CSV export logic from original code, including applied_filters_display)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="reporte_genetico_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        writer = csv.writer(response)
        if applied_filters_display:
            writer.writerow(['Filtros Aplicados:'])
            for key, value in applied_filters_display.items():
                 writer.writerow([f"{key}:", value])
            writer.writerow([]) 
        header = ['ID Historia', 'Paciente', 'Edad', 'Tipo', 'Genetista', 'Fecha Ingreso']
        writer.writerow(header)
        for item in report_data: writer.writerow([item[col] for col in header])
        return response

    elif export_format == 'pdf':
        # ... (PDF export logic from original code, including applied_filters_display)
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
        elements, styles = [], getSampleStyleSheet()
        elements.append(Paragraph("Reporte de Historias Clínicas Genéticas", styles['h1']))
        elements.append(Spacer(1, 0.2*72)) 
        if applied_filters_display:
            elements.append(Paragraph("Filtros Aplicados:", styles['h3']))
            for key, value in applied_filters_display.items(): elements.append(Paragraph(f"<b>{key}:</b> {value}", styles['Normal']))
            elements.append(Spacer(1, 0.2*72))
        header = ['ID Historia', 'Paciente', 'Edad', 'Tipo', 'Genetista', 'Fecha Ingreso']
        table_data = [header]
        for item in report_data: table_data.append([str(item['ID Historia']), item['Paciente'], str(item['Edad']), item['Tipo'], item['Genetista'], item['Fecha Ingreso']])
        if not report_data: table_data.append(["No se encontraron registros.", "", "", "", "", ""])
        table = Table(table_data, colWidths=[0.8*72, 2.5*72, 0.5*72, 1.0*72, 1.5*72, 1.0*72])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige), ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0,0), (-1,-1), 8), 
        ]))
        elements.append(table)
        doc.build(elements)
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="reporte_genetico_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
        return response

    return HttpResponse("Formato de exportación no soportado.", status=400)


@login_required
@admin_required
def gestion_usuarios_view(request):
    # This view would typically list users and provide forms to change their roles
    # and associate Lectors with Genetistas. For now, it's a placeholder.
    # users = User.objects.all().select_related('genetistas').prefetch_related('genetistas__lectores_asociados')
    # context = {'users': users}
    # return render(request, 'gestion_usuarios.html', context)
    messages.info(request, "La gestión detallada de usuarios (roles, asociaciones) se realiza a través del panel de Administración de Django por ahora.")
    return render(request, 'gestion_usuarios.html') 


# --- Index view and role-specific "Pacientes" list views ---
def _get_pacientes_queryset_for_role(user):
    try:
        user_gen_profile = user.genetistas
    except Genetistas.DoesNotExist:
        # If superuser and no profile, create one. Handled by decorator mostly.
        if user.is_superuser:
            user_gen_profile, _ = Genetistas.objects.get_or_create(user=user)
        else:
            return Propositos.objects.none()

    role = user_gen_profile.rol
    base_qs = Propositos.objects.filter(historia__isnull=False).select_related('historia', 'historia__genetista__user').order_by('-historia__fecha_ingreso')

    if role == 'ADM' or user.is_superuser: # Superuser sees all, ADM sees all
        return base_qs
    elif role == 'GEN':
        return base_qs.filter(historia__genetista=user_gen_profile)
    elif role == 'LEC':
        if user_gen_profile.associated_genetista:
            return base_qs.filter(historia__genetista=user_gen_profile.associated_genetista)
        else:
            return Propositos.objects.none()
    return Propositos.objects.none()


@login_required
@all_roles_required # The view itself is accessible, content is role-dependent
def index_view(request):
    ultimos_propositos_qs = _get_pacientes_queryset_for_role(request.user)
    user_gen_profile = request.user.genetistas # Assumed to exist by decorator
    
    page_title = "Inicio"
    if user_gen_profile:
        page_title = f"Inicio ({user_gen_profile.get_rol_display()})"
        if user_gen_profile.rol == 'LEC' and not user_gen_profile.associated_genetista:
            messages.warning(request, "Usted es un Lector no asociado a ningún Genetista. Su vista de datos estará limitada.")

    context = {
        'ultimos_propositos': ultimos_propositos_qs[:5],
        'page_title': page_title,
        'can_create_historia': user_gen_profile.rol in ['GEN', 'ADM'] if user_gen_profile else False
    }
    return render(request, "index.html", context)


@login_required
@admin_required
def pacientes_admin_view(request):
    ultimos_propositos_qs = _get_pacientes_queryset_for_role(request.user)
    context = {
        'ultimos_propositos': ultimos_propositos_qs[:10],
        'page_title': "Lista de Pacientes (Administrador)",
        'can_create_historia': True
    }
    return render(request, "index.html", context)

@login_required
@genetista_required # GEN or ADM
def pacientes_genetista_view(request):
    ultimos_propositos_qs = _get_pacientes_queryset_for_role(request.user)
    context = {
        'ultimos_propositos': ultimos_propositos_qs[:5],
        'page_title': "Mis Pacientes", # Title can be generic if role is clear from sidebar
        'can_create_historia': True
    }
    return render(request, "index.html", context)

@login_required
@lector_required # LEC or ADM
def pacientes_lector_view(request, genetista_id):
    user_profile = request.user.genetistas
    target_genetista = get_object_or_404(Genetistas, pk=genetista_id, rol='GEN')

    if user_profile.rol == 'LEC' and (not user_profile.associated_genetista or user_profile.associated_genetista.pk != genetista_id):
        raise PermissionDenied("No tiene permiso para ver pacientes de este genetista.")
    # ADM can view any genetista's patients via this URL if they want

    # Fetch patients specifically for the target_genetista
    ultimos_propositos_qs = Propositos.objects.filter(historia__genetista=target_genetista)\
                                           .select_related('historia').order_by('-historia__fecha_ingreso')
    context = {
        'ultimos_propositos': ultimos_propositos_qs[:5],
        'page_title': f"Pacientes de {target_genetista.user.get_full_name()}",
        'can_create_historia': False # Lectors cannot create
    }
    return render(request, "index.html", context)

@login_required
@all_roles_required
def pacientes_redirect_view(request):
    user_profile = request.user.genetistas # Assumed by decorator
    role = user_profile.rol

    if role == 'ADM':
        return redirect('pacientes_admin_list')
    elif role == 'GEN':
        return redirect('pacientes_genetista_list')
    elif role == 'LEC':
        if user_profile.associated_genetista_id:
            return redirect('pacientes_lector_list', genetista_id=user_profile.associated_genetista_id)
        else:
            messages.warning(request, "Como Lector, no está asociado a ningún Genetista.")
            return redirect('index')
    else:
        return redirect('index')


# --- Example/Tutorial Views ---
# These are mostly unchanged, ensure @login_required if they deal with sensitive example data.
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
        if form.is_valid(): messages.success(request, "Tarea creada (ejemplo)."); return redirect('task_list') 
        else: messages.error(request, "Error en formulario de tarea (ejemplo).")
    else: form = CreateNewTask()
    return render(request, 'create_task.html', {'form': form})

@login_required
def create_project(request):
    if request.method == 'POST':
        form = CreateNewProject(request.POST)
        if form.is_valid(): messages.success(request, "Proyecto creado (ejemplo)."); return redirect('project_list') 
        else: messages.error(request, "Error en formulario de proyecto (ejemplo).")
    else: form = CreateNewProject()
    return render(request, 'create_project.html', {'form': form})

@login_required
def project_detail(request, id):
    project_instance = get_object_or_404(Project, id=id) 
    return render(request, 'detail.html', {'project': project_instance, 'tasks': Task.objects.filter(project=project_instance)})
