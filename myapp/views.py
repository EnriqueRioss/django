
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.forms import AuthenticationForm # Standard Django auth form
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db.models import Q
from .forms import ReportSearchForm # Add this
from .models import HistoriasClinicas, Propositos, Genetistas, Parejas # Add Parejas
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
from .models import Project, Task # For example views
from .forms import CreateNewTask, CreateNewProject # For example views

# Conditional import for WeasyPrint
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    print("Warning: WeasyPrint is not installed. PDF export will not be available.")


# --- Helper for PDF Generation ---
def generate_report_pdf(filter_criteria, results, request):
    if not WEASYPRINT_AVAILABLE:
        return HttpResponse("PDF generation library (WeasyPrint) not installed.", status=501)

    context = {
        'filter_criteria': filter_criteria,
        'results': results,
        'site_url': request.build_absolute_uri('/')[:-1] # For static files in PDF if needed
    }
    html_string = render_to_string('reports/report_pdf_template.html', context)
    
    # Define base_url for WeasyPrint to find static files if your PDF template uses them
    # This assumes your static files are served from settings.STATIC_URL
    # and your CSS is appropriately linked in report_pdf_template.html
    # html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    
    # More robust way to handle static files for WeasyPrint if CSS is complex:
    # Collect static CSS content or link directly if WeasyPrint can access it.
    # For simplicity, we'll assume basic styling or inline styles in report_pdf_template.html for now.
    
    # Example of adding CSS (ensure the path is correct or CSS is inlined in template)
    # css_path = os.path.join(settings.STATIC_ROOT, 'styles/reports_pdf.css') # You'd create this CSS
    # main_css = CSS(filename=css_path) if os.path.exists(css_path) else None
    # pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(stylesheets=[main_css] if main_css else [])

    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_genetico.pdf"'
    return response

# --- Main Clinical Views ---

@login_required
def crear_historia(request):
    if request.method == 'POST':
        form = HistoriasForm(request.POST)
        if form.is_valid():
            try:
                genetista = request.user.genetistas # Assumes related_name 'genetistas' on User model
            except Genetistas.DoesNotExist: # Check correct related name or attribute
                try: # Fallback for user directly linked to Genetistas
                    genetista = Genetistas.objects.get(user=request.user)
                except Genetistas.DoesNotExist:
                    messages.error(request, 'El usuario actual no tiene un perfil de genetista asociado.')
                    return render(request, "historia_clinica.html", {'form1': form})

            historia = form.save(commit=False)
            historia.genetista = genetista
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
                    messages.warning(request, "Motivo de consulta no especificado para redirección, volviendo al inicio.")
                    return redirect('index')
            except IntegrityError: # Catch unique constraint violation for numero_historia
                 messages.error(request, f"Ya existe una historia clínica con el número '{historia.numero_historia}'. Por favor, use un número diferente.")
                 return render(request, "historia_clinica.html", {'form1': form}) # Return form with error
        else:
            messages.error(request, "No se pudo crear la historia. Por favor, corrija los errores indicados.")
    else: # GET
        form = HistoriasForm()

    return render(request, "historia_clinica.html", {'form1': form})

@login_required
def crear_paciente(request, historia_id):
    historia = get_object_or_404(HistoriasClinicas, historia_id=historia_id)
    existing_proposito = None

    # Attempt to find an existing Proposito if editing.
    # This is a simplified approach; for multiple Propositos per historia, a selection mechanism would be needed.
    if historia.motivo_tipo_consulta == 'Proposito-Diagnóstico':
        existing_proposito = Propositos.objects.filter(historia=historia).first()

    if request.method == 'POST':
        form = PropositosForm(request.POST, request.FILES, instance=existing_proposito)
        if form.is_valid():
            try:
                proposito = form.save(historia=historia) # Form's save handles update_or_create
                action_verb = 'actualizado' if existing_proposito and existing_proposito.pk == proposito.pk else 'creado'
                messages.success(request, f"Paciente {proposito.nombres} {proposito.apellidos} {action_verb} exitosamente.")
                return redirect('padres_proposito_crear', historia_id=historia.historia_id, proposito_id=proposito.proposito_id)
            except IntegrityError as e:
                messages.error(request, f"Error de integridad al guardar el paciente: {e}. Verifique que la identificación no esté duplicada.")
                # Form's clean_identificacion should ideally catch this.
            except Exception as e:
                messages.error(request, f"Error inesperado al guardar el paciente: {e}")
        else:
            messages.error(request, "No se pudo guardar el paciente. Por favor, corrija los errores indicados.")
    else: # GET
        form = PropositosForm(instance=existing_proposito) # Pass instance for pre-filling
        if existing_proposito:
            messages.info(request, f"Editando información para el propósito: {existing_proposito.nombres} {existing_proposito.apellidos}")

    return render(request, "Crear_paciente.html", {'form': form, 'historia': historia, 'editing': bool(existing_proposito)})

@login_required
def crear_pareja(request, historia_id):
    historia = get_object_or_404(HistoriasClinicas, historia_id=historia_id)
    # This view focuses on creating a new Pareja and its Propositos.
    # If Propositos with given IDs exist, they are updated.

    if request.method == 'POST':
        form = ParejaPropositosForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Helper to update or create a Proposito from form data
                    def get_or_create_proposito_from_form(form_cleaned_data, prefix_num, historia_obj):
                        identificacion = form_cleaned_data[f'identificacion_{prefix_num}']
                        proposito_data = {
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
                            'grupo_sanguineo': form_cleaned_data.get(f'grupo_sanguineo_{prefix_num}') or None,
                            'factor_rh': form_cleaned_data.get(f'factor_rh_{prefix_num}') or None,
                        }
                        proposito_defaults = {k: v for k, v in proposito_data.items() if v is not None or k == 'historia'}
                        proposito, created = Propositos.objects.update_or_create(
                            identificacion=identificacion,
                            defaults=proposito_defaults
                        )
                        foto_val = form_cleaned_data.get(f'foto_{prefix_num}')
                        if foto_val is not None:
                            if foto_val: proposito.foto = foto_val
                            elif foto_val is False: proposito.foto = None # Handle clear
                            proposito.save(update_fields=['foto'])
                        elif created and proposito.foto is not None:
                            proposito.foto = None
                            proposito.save(update_fields=['foto'])
                        return proposito

                    proposito1 = get_or_create_proposito_from_form(form.cleaned_data, '1', historia)
                    proposito2 = get_or_create_proposito_from_form(form.cleaned_data, '2', historia)

                    if proposito1.pk == proposito2.pk: # Should be caught by form clean
                        raise IntegrityError("Los dos miembros de la pareja no pueden ser la misma persona.")

                    # Ensure consistent order for unique_together constraint in Parejas model
                    p_min, p_max = sorted([proposito1, proposito2], key=lambda p: p.pk)
                    pareja, pareja_created = Parejas.objects.get_or_create(
                        proposito_id_1=p_min,
                        proposito_id_2=p_max
                        # Add any other defaults for Pareja if needed
                    )

                action_verb = 'creada' if pareja_created else 'localizada/actualizada'
                messages.success(request, f"Pareja ({proposito1.nombres} y {proposito2.nombres}) {action_verb} exitosamente.")
                return redirect('antecedentes_personales_crear',
                                 historia_id=historia.historia_id,
                                 tipo="pareja",
                                 objeto_id=pareja.pareja_id)
            except IntegrityError as e:
                 messages.error(request, f"Error de integridad al guardar la pareja: {e}. Verifique las identificaciones.")
            except Exception as e:
                messages.error(request, f"Error inesperado al guardar la pareja: {e}")
        else:
            messages.error(request, "No se pudo guardar la pareja. Por favor, corrija los errores indicados.")
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
                    padre_defaults = {k[len('padre_'):]: v for k, v in form.cleaned_data.items() if k.startswith('padre_')}
                    # Ensure required fields like nombres/apellidos are present even if None
                    padre_defaults_clean = {k:v for k,v in padre_defaults.items() if v is not None or k in ['nombres','apellidos']}
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
                messages.success(request, "Información de los padres guardada/actualizada exitosamente.")
                return redirect('antecedentes_personales_crear',
                                historia_id=historia_id,
                                tipo='proposito',
                                objeto_id=proposito_id)
            except Exception as e:
                messages.error(request, f"Error al guardar la información de los padres: {e}")
        else:
            messages.error(request, "No se pudo guardar la información de los padres. Por favor, corrija los errores indicados.")
    else: # GET
        padre = InformacionPadres.objects.filter(proposito=proposito, tipo='Padre').first()
        madre = InformacionPadres.objects.filter(proposito=proposito, tipo='Madre').first()
        initial_data = {}
        if padre:
            initial_data.update({f'padre_{f.name}': getattr(padre, f.name) for f in InformacionPadres._meta.fields if f.name not in ['padre_id', 'proposito', 'tipo'] and hasattr(padre, f.name)})
        if madre:
            initial_data.update({f'madre_{f.name}': getattr(madre, f.name) for f in InformacionPadres._meta.fields if f.name not in ['padre_id', 'proposito', 'tipo'] and hasattr(madre, f.name)})
        form = PadresPropositoForm(initial=initial_data if initial_data else None)
        if initial_data:
            messages.info(request, "Editando información de los padres.")

    return render(request, "Padres_proposito.html", {'form': form, 'historia': historia, 'proposito': proposito})

@login_required
def crear_antecedentes_personales(request, historia_id, tipo, objeto_id):
    historia = get_object_or_404(HistoriasClinicas, historia_id=historia_id)
    proposito_obj, pareja_obj, context_object_name = None, None, ""
    editing = False # To change messages like "guardados" vs "actualizados"

    if tipo == 'proposito':
        proposito_obj = get_object_or_404(Propositos, proposito_id=objeto_id, historia=historia)
        context_object_name = f"{proposito_obj.nombres} {proposito_obj.apellidos}"
        if AntecedentesPersonales.objects.filter(proposito=proposito_obj).exists() or \
           DesarrolloPsicomotor.objects.filter(proposito=proposito_obj).exists() or \
           PeriodoNeonatal.objects.filter(proposito=proposito_obj).exists():
            editing = True
    elif tipo == 'pareja':
        pareja_obj = get_object_or_404(Parejas, pareja_id=objeto_id, proposito_id_1__historia=historia)
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

                form.save(proposito=target_proposito, pareja=target_pareja) # Form's save handles update_or_create
                action_verb = "actualizados" if editing else "guardados"
                messages.success(request, f"Antecedentes personales y desarrollo {action_verb} para {context_object_name}.")

                redirect_to = 'antecedentes_preconcepcionales_crear'
                redirect_kwargs = {'historia_id': historia.historia_id, 'tipo': tipo, 'objeto_id': objeto_id}
                return redirect(redirect_to, **redirect_kwargs)
            except Exception as e:
                messages.error(request, f'Error al guardar antecedentes: {str(e)}')
        else:
            messages.error(request, "No se pudieron guardar los antecedentes. Por favor, corrija los errores indicados.")
    else: # GET
        initial_data = {}
        if editing: # Pre-fill form if editing
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

            if initial_data: messages.info(request, f"Editando antecedentes personales para {context_object_name}.")
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
        form = AntecedentesPreconcepcionalesForm(request.POST) # No instance passed directly, custom save handles it
        if form.is_valid():
            try:
                target_proposito = proposito_obj if tipo == 'proposito' else None
                target_pareja = pareja_obj if tipo == 'pareja' else None

                form.save(proposito=target_proposito, pareja=target_pareja, tipo=tipo) # Form save handles update_or_create
                action_verb = "actualizados" if instance_to_edit else "guardados"
                messages.success(request, f"Antecedentes preconcepcionales {action_verb} para {context_object_name}.")

                # Determine next step based on tipo
                if tipo == 'proposito' and proposito_obj:
                     # For Proposito, next step after preconcepcionales is usually ExamenFisico
                    return redirect('examen_fisico_crear_editar', proposito_id=proposito_obj.proposito_id)
                elif tipo == 'pareja' and pareja_obj:
                    # For Pareja, next step after preconcepcionales is EvaluacionGenetica
                    return redirect('evaluacion_genetica_detalle', historia_id=historia.historia_id, tipo="pareja", objeto_id=pareja_obj.pareja_id)
                else: # Fallback
                    return redirect('index')

            except Exception as e:
                messages.error(request, f'Error al guardar antecedentes preconcepcionales: {str(e)}')
        else:
            messages.error(request, "No se pudieron guardar los Antecedentes Preconcepcionales. Por favor, corrija los errores indicados.")
    else: # GET
        initial_data = {}
        if instance_to_edit:
            initial_data = {f.name: getattr(instance_to_edit, f.name) for f in AntecedentesFamiliaresPreconcepcionales._meta.fields if hasattr(instance_to_edit, f.name) and f.name not in ['antecedente_familiar_id', 'proposito', 'pareja']}
            if initial_data: messages.info(request, f"Editando antecedentes preconcepcionales para {context_object_name}.")
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
        form.proposito_instance = proposito # Pass proposito to form for its save method

        if form.is_valid():
            form.save()
            action_verb = "actualizado" if examen_existente else "guardado"
            messages.success(request, f"Examen físico para {proposito.nombres} {action_verb} exitosamente.")
            # Next step is Evaluacion Genetica for this proposito
            return redirect('evaluacion_genetica_detalle', historia_id=proposito.historia.historia_id, tipo="proposito", objeto_id=proposito.proposito_id)
        else:
            messages.error(request, "No se pudo guardar el Examen Físico. Por favor, corrija los errores indicados.")
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
    examen_fisico = ExamenFisico.objects.filter(proposito=proposito).first()
    padres_info = InformacionPadres.objects.filter(proposito=proposito)
    antecedentes_personales = AntecedentesPersonales.objects.filter(proposito=proposito).first()
    desarrollo_psicomotor = DesarrolloPsicomotor.objects.filter(proposito=proposito).first()
    periodo_neonatal = PeriodoNeonatal.objects.filter(proposito=proposito).first()
    antecedentes_familiares = AntecedentesFamiliaresPreconcepcionales.objects.filter(proposito=proposito).first()
    evaluacion_genetica = EvaluacionGenetica.objects.filter(proposito=proposito).first()
    diagnosticos = []
    planes_estudio = []
    if evaluacion_genetica:
        diagnosticos = DiagnosticoPresuntivo.objects.filter(evaluacion=evaluacion_genetica).order_by('orden')
        planes_estudio = PlanEstudio.objects.filter(evaluacion=evaluacion_genetica).order_by('pk')


    return render(request, "ver_proposito.html", {
        'proposito': proposito,
        'examen_fisico': examen_fisico,
        'padres_info': {p.tipo: p for p in padres_info},
        'antecedentes_personales': antecedentes_personales,
        'desarrollo_psicomotor': desarrollo_psicomotor,
        'periodo_neonatal': periodo_neonatal,
        'antecedentes_familiares': antecedentes_familiares,
        'evaluacion_genetica': evaluacion_genetica,
        'diagnosticos_presuntivos': diagnosticos,
        'planes_estudio': planes_estudio,
    })

@login_required
def diagnosticos_plan_estudio(request, historia_id, tipo, objeto_id):
    historia = get_object_or_404(HistoriasClinicas, historia_id=historia_id)
    proposito_obj, pareja_obj, context_object_name = None, None, ""

    if tipo == 'proposito':
        proposito_obj = get_object_or_404(Propositos, proposito_id=objeto_id, historia=historia)
        context_object_name = f"Propósito: {proposito_obj.nombres} {proposito_obj.apellidos}"
        evaluacion, created = EvaluacionGenetica.objects.get_or_create(
            proposito=proposito_obj, defaults={'pareja': None} # Ensure 'pareja' is None if linking to 'proposito'
        )
        if not created and evaluacion.pareja is not None: # Correct inconsistent data if found
            evaluacion.pareja = None; evaluacion.proposito = proposito_obj; evaluacion.save()
    elif tipo == 'pareja':
        pareja_obj = get_object_or_404(Parejas, pareja_id=objeto_id, proposito_id_1__historia=historia)
        context_object_name = f"Pareja ID: {pareja_obj.pareja_id} ({pareja_obj.proposito_id_1.nombres} y {pareja_obj.proposito_id_2.nombres})"
        evaluacion, created = EvaluacionGenetica.objects.get_or_create(
            pareja=pareja_obj, defaults={'proposito': None} # Ensure 'proposito' is None if linking to 'pareja'
        )
        if not created and evaluacion.proposito is not None: # Correct inconsistent data
            evaluacion.proposito = None; evaluacion.pareja = pareja_obj; evaluacion.save()
    else:
        messages.error(request, "Tipo de objeto no válido para la evaluación genética.")
        return redirect('index')

    if request.method == 'POST':
        signos_form = SignosClinicosForm(request.POST, instance=evaluacion)
        diagnostico_formset = DiagnosticoPresuntivoFormSet(request.POST, prefix='diagnosticos')
        plan_formset = PlanEstudioFormSet(request.POST, prefix='plans')

        if signos_form.is_valid() and diagnostico_formset.is_valid() and plan_formset.is_valid():
            with transaction.atomic():
                evaluacion_instance = signos_form.save() # This is the EvaluacionGenetica instance

                # Clear old and save new Diagnosticos Presuntivos
                DiagnosticoPresuntivo.objects.filter(evaluacion=evaluacion_instance).delete()
                for form_data_diag in diagnostico_formset.cleaned_data: # Iterate over cleaned_data list of dicts
                    if form_data_diag and not form_data_diag.get('DELETE', False): # Check if form has data and not marked for deletion
                        if form_data_diag.get('descripcion'): # Ensure description is present
                            DiagnosticoPresuntivo.objects.create(
                                evaluacion=evaluacion_instance,
                                descripcion=form_data_diag['descripcion'],
                                orden=form_data_diag.get('orden', 0) # Use .get with default
                            )

                # Clear old and save new Planes de Estudio
                PlanEstudio.objects.filter(evaluacion=evaluacion_instance).delete()
                for form_data_plan in plan_formset.cleaned_data: # Iterate over cleaned_data
                    if form_data_plan and not form_data_plan.get('DELETE', False):
                        if form_data_plan.get('accion'): # Ensure accion is present
                            PlanEstudio.objects.create(
                                evaluacion=evaluacion_instance,
                                accion=form_data_plan['accion'],
                                fecha_limite=form_data_plan.get('fecha_limite'), # .get is safer
                                completado=form_data_plan.get('completado', False)
                            )

            messages.success(request, "Evaluación genética guardada exitosamente.")
            messages.info(request, "POPUP:Historia Clínica Genética completada y guardada exitosamente.") # For the final pop-up

            if tipo == 'proposito' and proposito_obj:
                 return redirect('index')
            # else if tipo == 'pareja', maybe a pareja detail view or back to historia
            return redirect('index') # Fallback redirect
        else:
            error_msg_list = []
            if not signos_form.is_valid(): error_msg_list.append(f"Errores en Signos Clínicos: {signos_form.errors.as_ul()}")
            if not diagnostico_formset.is_valid(): error_msg_list.append(f"Errores en Diagnósticos Presuntivos: {diagnostico_formset.non_form_errors().as_ul()} {diagnostico_formset.errors}")
            if not plan_formset.is_valid(): error_msg_list.append(f"Errores en Plan de Estudio: {plan_formset.non_form_errors().as_ul()} {plan_formset.errors}")
            messages.error(request, "No se pudo guardar la Evaluación Genética. Por favor, corrija los errores indicados. " + " ".join(error_msg_list))
    else: # GET
        signos_form = SignosClinicosForm(instance=evaluacion)

        diagnosticos_initial = [{'descripcion': d.descripcion, 'orden': d.orden}
                                for d in DiagnosticoPresuntivo.objects.filter(evaluacion=evaluacion).order_by('orden')]
        # Ensure at least one empty form if no initial data for formsets with extra=1
        diagnostico_formset = DiagnosticoPresuntivoFormSet(prefix='diagnosticos', initial=diagnosticos_initial or [{'orden':0}])


        planes_initial = [{'accion': p.accion, 'fecha_limite': p.fecha_limite, 'completado': p.completado}
                          for p in PlanEstudio.objects.filter(evaluacion=evaluacion).order_by('pk')] # Use a consistent order
        plan_formset = PlanEstudioFormSet(prefix='plans', initial=planes_initial or [{}])

        if created:
            messages.info(request, "Iniciando nueva evaluación genética.")
        else:
            messages.info(request, f"Editando evaluación genética para {context_object_name}.")


    context = {
        'historia': historia, 'tipo': tipo, 'objeto': proposito_obj or pareja_obj,
        'context_object_name': context_object_name, 'signos_form': signos_form,
        'diagnostico_formset': diagnostico_formset, 'plan_formset': plan_formset,
        'evaluacion_instance': evaluacion # For template to know if it's create/edit context
    }
    return render(request, 'diagnosticos_plan.html', context)

# --- AJAX Views ---
@login_required
def buscar_propositos(request):
    query = request.GET.get('q', '').strip()
    propositos_qs = Propositos.objects.none()

    if request.user.is_authenticated:
        try:
            genetista = request.user.genetistas
        except Genetistas.DoesNotExist: # Fallback for direct link
             try:
                genetista = Genetistas.objects.get(user=request.user)
             except Genetistas.DoesNotExist:
                return JsonResponse({'propositos': [], 'error': 'Perfil de genetista no encontrado.'}, status=403) # Or handle differently

        if query:
            propositos_qs = Propositos.objects.select_related('historia').filter(
                Q(nombres__icontains=query) |
                Q(apellidos__icontains=query) |
                Q(identificacion__icontains=query),
                historia__genetista=genetista # Ensure propositos are linked to the genetista's historias
            ).order_by('-historia__fecha_ingreso')[:10]
        else: # Return recent if no query
            propositos_qs = Propositos.objects.select_related('historia').filter(
                historia__genetista=genetista
            ).order_by('-historia__fecha_ingreso')[:5]

    resultados = [{
        'proposito_id': p.proposito_id, 'nombres': p.nombres, 'apellidos': p.apellidos,
        'edad': p.edad, 'direccion': p.direccion or "N/A", 'identificacion': p.identificacion,
        'foto_url': p.foto.url if p.foto else None,
        'fecha_ingreso': p.historia.fecha_ingreso.strftime("%d/%m/%Y %H:%M") if p.historia and p.historia.fecha_ingreso else "--",
        'historia_numero': p.historia.numero_historia if p.historia else "N/A" # Add historia number
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
                    Genetistas.objects.create(user=user) # Create Genetistas profile
                login(request, user)
                messages.success(request, "Registro exitoso. ¡Bienvenido!")
                return redirect('index')
            except IntegrityError: # Should be rare if username check is done by form
                messages.error(request, "El nombre de usuario ya existe o ha ocurrido un error de base de datos.")
            except Exception as e:
                messages.error(request, f"Un error inesperado ocurrió: {e}")
        else:
            messages.error(request, "No se pudo completar el registro. Por favor, corrija los errores indicados.")
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
                try:
                    # Check if user has a Genetista profile
                    _ = user.genetistas # Assumes related_name='genetistas' from User to Genetista
                    login(request, user)
                    messages.info(request, f"Bienvenido de nuevo, {user.username}.")
                    next_url = request.GET.get('next')
                    return redirect(next_url or 'index')
                except Genetistas.DoesNotExist:
                     try: # Fallback for direct link
                         _ = Genetistas.objects.get(user=user)
                         login(request, user)
                         messages.info(request, f"Bienvenido de nuevo, {user.username}.")
                         next_url = request.GET.get('next')
                         return redirect(next_url or 'index')
                     except Genetistas.DoesNotExist:
                        messages.error(request, "Este usuario no tiene un perfil de genetista asociado.")
            else:
                messages.error(request, "Nombre de usuario o contraseña incorrectos.")
        else:
             messages.error(request, "Por favor, ingrese un nombre de usuario y contraseña válidos.")
    else: # GET
        form = LoginForm()

    return render(request, "login.html", {'form': form})

def signout(request):
    logout(request)
    messages.success(request, "Has cerrado sesión exitosamente.")
    return redirect('login')


# --- Other/Management Views ---
@login_required
def reports_view(request):
    form = ReportSearchForm(request.GET or None)
    results = []
    filter_criteria_for_pdf = {}

    if form.is_valid():
        buscar_paciente = form.cleaned_data.get('buscar_paciente')
        date_range_cleaned = form.cleaned_data.get('date_range') # This is (fecha_desde, fecha_hasta) or None
        tipo_registro = form.cleaned_data.get('tipo_registro')
        genetista_instance = form.cleaned_data.get('genetista')

        # Prepare filter criteria for PDF metadata
        filter_criteria_for_pdf['buscar_paciente'] = buscar_paciente or "Todos"
        if date_range_cleaned:
            filter_criteria_for_pdf['fecha_desde'] = date_range_cleaned[0].strftime('%d/%m/%Y')
            filter_criteria_for_pdf['fecha_hasta'] = date_range_cleaned[1].strftime('%d/%m/%Y')
        else:
            filter_criteria_for_pdf['rango_fechas'] = "Cualquiera"
        filter_criteria_for_pdf['tipo_registro'] = dict(form.fields['tipo_registro'].choices).get(tipo_registro, "Todos")
        filter_criteria_for_pdf['genetista'] = genetista_instance.user.get_full_name() if genetista_instance else "Todos"


        # Start with a base queryset
        historias_qs = HistoriasClinicas.objects.select_related('genetista__user').prefetch_related('propositos_set').distinct()

        query_filters = Q()

        if buscar_paciente:
            query_filters &= (
                Q(propositos__nombres__icontains=buscar_paciente) |
                Q(propositos__apellidos__icontains=buscar_paciente) |
                Q(propositos__identificacion__icontains=buscar_paciente)
            )

        if date_range_cleaned:
            fecha_desde, fecha_hasta = date_range_cleaned
            query_filters &= Q(fecha_ingreso__date__gte=fecha_desde)
            query_filters &= Q(fecha_ingreso__date__lte=fecha_hasta)

        if genetista_instance:
            query_filters &= Q(genetista=genetista_instance)

        if tipo_registro == 'proposito':
            # Assuming 'Proposito-Diagnóstico' is the key for single proposito histories
            query_filters &= Q(motivo_tipo_consulta='Proposito-Diagnóstico')
        elif tipo_registro == 'pareja':
            # Assuming 'Pareja-' prefix for couple related histories
            query_filters &= Q(motivo_tipo_consulta__startswith='Pareja-')
        
        historias_qs = historias_qs.filter(query_filters).order_by('-fecha_ingreso', 'numero_historia')

        # Process queryset for template
        processed_results = []
        for historia in historias_qs:
            propositos_en_historia = list(historia.propositos_set.all())
            genetista_nombre = historia.genetista.user.get_full_name() if historia.genetista and historia.genetista.user else 'N/A'

            # Check if the current historia matches the 'tipo_registro' filter if one was applied.
            # If no tipo_registro filter, display based on historia's nature.
            display_as_pareja = historia.motivo_tipo_consulta.startswith('Pareja-')
            display_as_proposito = historia.motivo_tipo_consulta == 'Proposito-Diagnóstico'

            if tipo_registro == 'pareja' and not display_as_pareja:
                continue # Skip if filtering for parejas but this isn't one
            if tipo_registro == 'proposito' and not display_as_proposito:
                continue # Skip if filtering for propositos but this isn't one

            if display_as_pareja and len(propositos_en_historia) >= 1: # Need at least one to show, ideally 2
                # For a "Pareja" type historia, its propositos are the members
                miembro1 = propositos_en_historia[0]
                miembro2 = propositos_en_historia[1] if len(propositos_en_historia) > 1 else None

                processed_results.append({
                    'id_historia': historia.numero_historia,
                    'nombre_completo': f"{miembro1.nombres} {miembro1.apellidos}",
                    'edad': miembro1.edad,
                    'tipo_display': 'Pareja',
                    'genetista': genetista_nombre,
                    'fecha_ingreso': historia.fecha_ingreso,
                    'is_pareja_member': True,
                    'is_first_member': True,
                    'pareja_historia_id': historia.pk 
                })
                if miembro2:
                    processed_results.append({
                        'id_historia': historia.numero_historia,
                        'nombre_completo': f"{miembro2.nombres} {miembro2.apellidos}",
                        'edad': miembro2.edad,
                        'tipo_display': 'Pareja',
                        'genetista': genetista_nombre,
                        'fecha_ingreso': historia.fecha_ingreso,
                        'is_pareja_member': True,
                        'is_first_member': False,
                        'pareja_historia_id': historia.pk
                    })
                elif len(propositos_en_historia) == 1 and display_as_pareja: # Pareja history but only one proposito listed
                     # Optionally log or handle this case of incomplete pareja data
                    pass

            elif display_as_proposito and len(propositos_en_historia) >= 1:
                proposito_individual = propositos_en_historia[0]
                processed_results.append({
                    'id_historia': historia.numero_historia,
                    'nombre_completo': f"{proposito_individual.nombres} {proposito_individual.apellidos}",
                    'edad': proposito_individual.edad,
                    'tipo_display': 'Propósito',
                    'genetista': genetista_nombre,
                    'fecha_ingreso': historia.fecha_ingreso,
                    'is_pareja_member': False,
                    'pareja_historia_id': None # Not part of a grouped pareja display
                })
        
        results = processed_results

        if 'export_pdf' in request.GET:
            return generate_report_pdf(filter_criteria_for_pdf, results, request)

    # Pass genetistas to the form for dropdown population even if form is not submitted yet
    # The ModelChoiceField in ReportSearchForm handles this automatically via its queryset.

    context = {
        'form': form,
        'results': results,
        'has_searched': bool(request.GET), # True if any GET parameters exist (form submitted)
    }
    return render(request, 'reports/reports.html', context) # Adjusted template path


@login_required
def gestion_usuarios_view(request):
    # if not request.user.is_superuser:
    #     messages.error(request, "Acceso denegado.")
    #     return redirect('index')
    # users = User.objects.all().select_related('genetistas') # Example query
    # context = {'users': users}
    return render(request, 'gestion_usuarios.html') #, context)

# --- Example/Tutorial Views (Consider removing or separating) ---
def index(request): # This is the main index/dashboard
    if request.user.is_authenticated:
        try:
            genetista = request.user.genetistas
            ultimos_propositos = Propositos.objects.filter(historia__genetista=genetista).order_by('-historia__fecha_ingreso')[:5]
            context = {'ultimos_propositos': ultimos_propositos}
            return render(request, "index.html", context)
        except Genetistas.DoesNotExist: # Fallback for direct access or if related_name is different
            try:
                genetista = Genetistas.objects.get(user=request.user)
                ultimos_propositos = Propositos.objects.filter(historia__genetista=genetista).order_by('-historia__fecha_ingreso')[:5]
                context = {'ultimos_propositos': ultimos_propositos}
                return render(request, "index.html", context)
            except Genetistas.DoesNotExist:
                # Handle users authenticated but without a Genetista profile
                if request.user.is_superuser:
                     # Superusers might not have a genetista profile but can access admin
                     messages.info(request, "Sesión de Superusuario iniciada. No hay datos de genetista para mostrar en el dashboard.")
                     return render(request, "index.html", {'title': "Panel de Administración"})

                # For other authenticated users without a genetista profile, log them out or show error
                logout(request) # Force logout
                messages.error(request, "Usuario autenticado pero sin perfil de genetista. Sesión cerrada.")
                return redirect('login')


    # For unauthenticated users, show a generic landing page
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