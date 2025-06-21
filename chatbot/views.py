# chatbot/views.py
import os
import re
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

import google.generativeai as genai
from dotenv import load_dotenv

# Importa los modelos de la otra app
from myapp.models import Propositos, DiagnosticoPresuntivo, PlanEstudio, ExamenFisico, Genetistas
from .models import ChatInteraction

load_dotenv()
print("CLAVE DE API CARGADA:", os.getenv("GOOGLE_API_KEY"))

try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
except Exception as e:
    print(f"Error crítico al configurar Gemini: {e}")

# --- Lógica del Chatbot Mejorada ---
def get_context_from_db(query: str, user) -> str:
    """Busca en la base de datos información relevante para la consulta del usuario logueado."""
    context_parts = []
    lower_query = query.lower()

    # Base queryset filtrado por rol
    base_paciente_qs = Propositos.objects.select_related('historia')
    try:
        user_profile = user.genetistas
        if user_profile.rol == 'GEN':
            base_paciente_qs = base_paciente_qs.filter(historia__genetista=user_profile)
        elif user_profile.rol == 'LEC' and user_profile.associated_genetista:
            base_paciente_qs = base_paciente_qs.filter(historia__genetista=user_profile.associated_genetista)
        elif user_profile.rol == 'LEC': # Lector no asociado
            return "No tiene pacientes asignados."
    except Genetistas.DoesNotExist:
        return "Su perfil de usuario no está configurado." # No debería pasar si hay decoradores

    # 1. Buscar paciente por ID/Cédula
    id_match = re.search(r'\d{5,}', query)
    if id_match:
        paciente = base_paciente_qs.filter(identificacion=id_match.group(0)).first()
        if paciente:
            context_parts.append(f"**Paciente:** {paciente.nombres} {paciente.apellidos} (ID: {paciente.identificacion})")
            if 'diagnóstico' in lower_query or 'diagnostico' in lower_query:
                diagnosticos = DiagnosticoPresuntivo.objects.filter(evaluacion__proposito=paciente).order_by('orden')
                if diagnosticos.exists():
                    context_parts.append(f"**Diagnósticos:** " + ", ".join([d.descripcion for d in diagnosticos]))
                else:
                    context_parts.append("**Diagnósticos:** No encontrados.")
            return "\n".join(context_parts)

    # 2. Buscar análisis pendientes para el médico
    if 'pendientes' in lower_query or 'mis tareas' in lower_query:
        planes_pendientes = PlanEstudio.objects.filter(completado=False, evaluacion__proposito__in=base_paciente_qs)[:5]
        if planes_pendientes.exists():
            plan_list = "\n".join([f"- {p.accion} (para {p.evaluacion.proposito.nombres})" for p in planes_pendientes])
            context_parts.append(f"**Tus Planes de Estudio Pendientes:**\n{plan_list}")

    return "\n\n".join(context_parts) if context_parts else "No se encontró información específica en la base de datos."

def get_bot_response(query: str, user) -> dict:
    """Obtiene la respuesta de Gemini y la formatea para el frontend."""
    system_prompt = """
    Eres 'GenAssist', un asistente experto integrado en un sistema de historias clínicas genéticas... (tu prompt completo va aquí)
    **Importante**: Tu respuesta debe ser concisa y formateada con Markdown para ser legible. Usa **negritas** para resaltar y listas con - o *.
    **Sugerencias**: Al final, si es apropiado, añade sugerencias con el formato: [SUGGESTIONS]: ["Pregunta 1", "Pregunta 2"]
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        db_context = get_context_from_db(query, user)
        full_prompt = f"{system_prompt}\n\n--- CONTEXTO DE LA BASE DE DATOS ---\n{db_context}\n--- FIN DEL CONTEXTO ---\n\n**Pregunta:** {query}"
        
        gemini_response = model.generate_content(full_prompt)
        response_text = gemini_response.text

        suggestions = []
        suggestion_match = re.search(r'\[SUGGESTIONS\]:\s*(\[.*?\])', response_text, re.DOTALL)
        if suggestion_match:
            try:
                suggestions = json.loads(suggestion_match.group(1))
                response_text = response_text[:suggestion_match.start()].strip()
            except json.JSONDecodeError: pass

        # Convertir Markdown a HTML básico para el frontend
        html_response = response_text.replace('**', '<strong>').replace('**', '</strong>')
        html_response = html_response.replace('* ', '<li>').replace('\n- ', '<li>')
        html_response = html_response.replace('\n', '<br>')
        
        return {'response': html_response, 'suggestions': suggestions}

    except Exception as e:
        print(f"Error procesando con Gemini: {e}")
        return {'response': "Lo siento, estoy experimentando dificultades técnicas.", 'suggestions': []}

# --- Vista de la API ---
@csrf_exempt
@require_http_methods(["POST"])
@login_required # ¡Importante! Asegura que solo usuarios logueados puedan usar el chat.
def chat_api(request):
    try:
        data = json.loads(request.body)
        query = data.get('query')

        if not query:
            return JsonResponse({'error': 'Falta la consulta (query).'}, status=400)
        
        bot_data = get_bot_response(query, request.user)

        ChatInteraction.objects.create(
            user=request.user,
            user_query=query,
            bot_response=bot_data.get('response', '').replace('<br>', '\n') # Guardar en DB con saltos de línea
        )
        
        return JsonResponse(bot_data)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON mal formado.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)