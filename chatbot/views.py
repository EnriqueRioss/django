# chatbot/views.py

import os
import re
import json
import traceback
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.cache import cache
from django.conf import settings

import google.generativeai as genai
from google.generativeai.types import content_types
from dotenv import load_dotenv
from duckduckgo_search import DDGS

# Importaciones de LangChain para la funcionalidad RAG
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

# Importaciones de los modelos de la app principal
from myapp.models import Propositos, HistoriasClinicas, Genetistas
from .models import ChatInteraction

# --- Función de Utilidad para Debugging ---
def debug_print(message):
    """Imprime mensajes de debug de forma destacada en la consola."""
    print(f"\n===== CHATBOT DEBUG =====\n{message}\n=======================\n")

load_dotenv()

# --- Configuración de la API de Google Gemini ---
api_key_check = os.getenv("GOOGLE_API_KEY")
if api_key_check:
    debug_print(f"API Key Loaded: {api_key_check[:5]}...")
else:
    debug_print("API Key NOT FOUND. Please check your .env file.")

try:
    genai.configure(api_key=api_key_check)
except Exception as e:
    debug_print(f"Error crítico al configurar Gemini: {e}")

# ==============================================================================
# === DECLARACIÓN DE HERRAMIENTAS PARA EL MODELO DE IA =========================
# ==============================================================================

def buscar_paciente(nombre_o_id: str) -> str:
    """Busca UN paciente por nombre, apellido o ID. Úsalo para resúmenes o detalles de un individuo."""
    pass

def listar_entidades(tipo_entidad: str) -> str:
    """Lista entidades generales como 'doctores' o 'pacientes recientes'."""
    pass

def buscar_pacientes_por_estado(estado: str) -> str:
    """Busca y lista TODOS los pacientes que coinciden con un estado como 'pendientes' o 'completados'."""
    pass

def generar_enlace_pdf_paciente(nombre_o_id_paciente: str) -> str:
    """Genera un enlace PDF para UN paciente específico. Preferiblemente usar el ID."""
    pass

def buscar_en_la_web(query: str) -> str:
    """Busca en la web información no relacionada con los pacientes de la clínica ni con el uso de la aplicación."""
    pass

def consultar_documentacion_app(pregunta_del_usuario: str) -> str:
    """Busca en la documentación interna para responder preguntas sobre CÓMO USAR la aplicación, qué significan los roles, cuál es el flujo de trabajo, etc. Es la herramienta principal para preguntas de 'cómo', 'dónde', 'qué es' o 'cuál es el proceso'."""
    pass

# ==============================================================================
# === LÓGICA INTERNA DE LAS HERRAMIENTAS (IMPLEMENTACIÓN) =====================
# ==============================================================================

def _get_pacientes_permitidos_for_user(user):
    """Obtiene el QuerySet de pacientes a los que el usuario tiene acceso."""
    try:
        user_profile = user.genetistas
    except Genetistas.DoesNotExist:
        return Propositos.objects.none()
    base_qs = Propositos.objects.select_related('historia__genetista__user').filter(historia__isnull=False)
    if user_profile.rol == 'ADM': return base_qs
    if user_profile.rol == 'GEN': return base_qs.filter(historia__genetista=user_profile)
    if user_profile.rol == 'LEC' and user_profile.associated_genetista:
        return base_qs.filter(historia__genetista=user_profile.associated_genetista)
    return Propositos.objects.none()

def _internal_buscar_paciente(consulta_especifica: str, user) -> dict:
    """Busca un paciente de forma inteligente y con control de permisos."""
    try:
        pacientes_permitidos_qs = _get_pacientes_permitidos_for_user(user)
        todos_los_pacientes_qs = Propositos.objects.all()
        paciente = None
        id_match = re.search(r'\b(\d+)\b', consulta_especifica)
        if id_match:
            paciente_id = id_match.group(1)
            paciente_encontrado = todos_los_pacientes_qs.filter(identificacion=paciente_id).first()
            if paciente_encontrado:
                if pacientes_permitidos_qs.filter(pk=paciente_encontrado.pk).exists():
                    paciente = paciente_encontrado
                else:
                    return {"error": f"El paciente con ID {paciente_id} existe, pero no tienes permisos para acceder a su información."}
        if not paciente:
            terms = [t for t in consulta_especifica.lower().split() if t not in {'de', 'el', 'la', 'un', 'resumen', 'info'}]
            if not terms:
                return {"error": "Por favor, proporciona un nombre, apellido o ID para la búsqueda."}
            q_obj = Q()
            for term in terms: q_obj &= (Q(nombres__icontains=term) | Q(apellidos__icontains=term))
            resultados = pacientes_permitidos_qs.filter(q_obj)
            if resultados.count() == 1: paciente = resultados.first()
            elif resultados.count() > 1:
                return {"error": f"Búsqueda ambigua. Múltiples pacientes encontrados: {', '.join([p.nombres for p in resultados])}."}
        if paciente:
            historia = hasattr(paciente, 'historia') and paciente.historia
            return {
                "resumen_paciente": f"Paciente: {paciente.nombres} {paciente.apellidos}",
                "id": paciente.identificacion, "sexo": paciente.get_sexo_display(),
                "edad": f"{paciente.edad} años", "genetista": historia.genetista.user.get_full_name() if historia and historia.genetista else "N/A"
            }
        return {"error": f"No se encontró ningún paciente que coincida con '{consulta_especifica}'."}
    except Exception as e:
        debug_print(f"EXCEPCIÓN en _internal_buscar_paciente: {e}"); return {"error": "Error crítico al buscar paciente."}

def _internal_listar_entidades(tipo_entidad: str, pacientes_permitidos_qs) -> dict:
    try:
        tipo_entidad = tipo_entidad.lower()
        if tipo_entidad in ['doctores', 'genetistas']:
            doctores = Genetistas.objects.filter(rol='GEN').select_related('user').order_by('user__last_name')
            return {"listado_doctores": [doc.user.get_full_name() or doc.user.username for doc in doctores]}
        if tipo_entidad in ['pacientes', 'pacientes_recientes', 'mis pacientes']:
            pacientes = pacientes_permitidos_qs.order_by('-historia__fecha_ingreso')[:10]
            if not pacientes.exists(): return {"error": "No se encontraron pacientes para tu perfil."}
            return {"listado_pacientes": [f"{p.nombres} {p.apellidos} (ID: {p.identificacion})" for p in pacientes]}
        return {"error": f"Tipo de entidad '{tipo_entidad}' no válido. Opciones: 'doctores', 'pacientes'."}
    except Exception as e:
        debug_print(f"EXCEPCIÓN en _internal_listar_entidades: {e}"); return {"error": "Error crítico al listar."}

def _internal_buscar_pacientes_por_estado(estado: str, pacientes_permitidos_qs) -> dict:
    # Esta función asume que tienes un campo 'estado_analisis' en tu modelo HistoriasClinicas
    # Debes adaptar 'historia__estado_analisis' y los valores ('PENDIENTE', etc.) a tu modelo real.
    try:
        estado_mapping = { 'pendiente': 'PENDIENTE', 'completado': 'COMPLETADO', 'en progreso': 'EN_PROGRESO' }
        db_valor = estado_mapping.get(estado.lower().strip())
        if not db_valor: return {"error": "Estado no reconocido. Prueba con 'pendientes', 'completados' o 'en progreso'."}
        
        # CAMBIA 'historia__estado_analisis' POR TU CAMPO REAL
        pacientes = pacientes_permitidos_qs.filter(historia__estado_analisis=db_valor) 
        if not pacientes.exists(): return {"mensaje": f"No se encontraron pacientes con estado '{estado}'."}
        return {f"pacientes_{estado.replace(' ','_')}": [f"{p.nombres} {p.apellidos}" for p in pacientes]}
    except Exception as e:
        debug_print(f"EXCEPCIÓN en _internal_buscar_pacientes_por_estado: {e}"); return {"error": "Error crítico buscando por estado."}

def _internal_generar_enlace_pdf(nombre_o_id: str, pacientes_permitidos_qs) -> dict:
    try:
        id_match = re.search(r'\b(\d+)\b', nombre_o_id)
        if not id_match: return {"error": "Por favor, proporciona el ID numérico del paciente para generar el PDF."}
        paciente = pacientes_permitidos_qs.filter(identificacion=id_match.group(1)).first()
        if not paciente: return {"error": f"No se encontró un paciente con ID '{id_match.group(1)}' en tus registros."}
        # CAMBIA 'export_paciente_pdf' por el nombre real de tu URL para exportar PDF
        url = reverse('myapp:export_paciente_pdf', kwargs={'proposito_id': paciente.pk})
        return {"nombre_paciente": f"{paciente.nombres} {paciente.apellidos}", "url_descarga": url}
    except Exception as e:
        debug_print(f"EXCEPCIÓN en _internal_generar_enlace_pdf: {e}"); return {"error": "Error crítico al generar enlace PDF."}

def _internal_buscar_web(query: str) -> dict:
    try:
        with DDGS() as ddgs: results = [r['body'] for r in ddgs.text(query, max_results=3)]
        return {"web_search_summary": "\n".join(results) if results else "No se encontraron resultados."}
    except Exception as e: return {"error": f"Error en búsqueda web: {e}"}

def _internal_consultar_documentacion_app(query: str) -> dict:
    """Realiza una búsqueda de similitud en la base de datos vectorial de ChromaDB."""
    try:
        chroma_db_dir = os.path.join(settings.BASE_DIR, 'chroma_db')
        if not os.path.exists(chroma_db_dir):
            return {"error": "La base de conocimiento de la aplicación no ha sido creada. Un administrador debe ejecutar 'build_vector_db'."}
        embeddings_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        vector_store = Chroma(persist_directory=chroma_db_dir, embedding_function=embeddings_model)
        retriever = vector_store.as_retriever(search_kwargs={'k': 4})
        relevant_docs = retriever.invoke(query)
        if not relevant_docs:
            return {"contexto": "No se encontró información relevante en la documentación para responder a esta pregunta."}
        context = "\n\n---\n\n".join([doc.page_content for doc in relevant_docs])
        return {"contexto_encontrado": context}
    except Exception as e:
        debug_print(f"EXCEPCIÓN en _internal_consultar_documentacion_app: {e}\n{traceback.format_exc()}"); 
        return {"error": "Error crítico al buscar en la base de conocimiento."}

# ==============================================================================
# === VISTA PRINCIPAL DEL CHATBOT ==============================================
# ==============================================================================
def get_bot_response(query: str, user) -> dict:
    session_key = f"chat_history_{user.id}"
    chat_history = cache.get(session_key, [])

    system_prompt = f"""
    Eres GenAssist, un asistente experto de la aplicación GenClinic para el usuario '{user.username}'. Tu objetivo es ser útil y preciso. Prioriza las herramientas en este orden:

    1.  **AYUDA DE LA APLICACIÓN (`consultar_documentacion_app`)**: Si la pregunta es sobre CÓMO usar el software, QUÉ significa algo, CUÁL es un proceso o DÓNDE encontrar una opción, usa esta herramienta. Ejemplos: "¿Cómo exporto un reporte?", "¿Qué puede hacer un usuario Lector?", "¿Cuál es el proceso para crear un paciente?".

    2.  **DATOS DE LA CLÍNICA (`buscar_paciente`, etc.)**: Si la pregunta es sobre datos de pacientes, doctores, o estados de análisis, usa las herramientas de datos correspondientes.

    3.  **CONOCIMIENTO GENERAL (`buscar_en_la_web`)**: Si la pregunta no se puede responder con las herramientas anteriores (ej. "¿Qué es el síndrome de Marfan?"), usa la búsqueda web.

    Siempre invoca una herramienta. No intentes responder desde tu conocimiento general si una herramienta parece apropiada.
    """

    try:
        tools_for_model = [
            buscar_paciente, listar_entidades, buscar_pacientes_por_estado, 
            generar_enlace_pdf_paciente, buscar_en_la_web, consultar_documentacion_app
        ]
        model = genai.GenerativeModel('gemini-1.5-flash-latest', system_instruction=system_prompt, tools=tools_for_model)
        chat_session = model.start_chat(history=chat_history)
        response = chat_session.send_message(query)

        while response.candidates and response.candidates[0].content.parts and response.candidates[0].content.parts[0].function_call:
            function_call = response.candidates[0].content.parts[0].function_call
            function_name = function_call.name
            function_args = {key: value for key, value in function_call.args.items()}
            debug_print(f"Modelo quiere llamar a: {function_name} con argumentos: {function_args}")
            
            tool_result_obj = {}
            pacientes_permitidos = _get_pacientes_permitidos_for_user(user)

            if function_name == "consultar_documentacion_app":
                tool_result_obj = _internal_consultar_documentacion_app(function_args.get('pregunta_del_usuario', query))
            elif function_name == "buscar_paciente":
                tool_result_obj = _internal_buscar_paciente(function_args.get('nombre_o_id', ''), user)
            elif function_name == "listar_entidades":
                tool_result_obj = _internal_listar_entidades(function_args.get('tipo_entidad', ''), pacientes_permitidos)
            elif function_name == "buscar_pacientes_por_estado":
                tool_result_obj = _internal_buscar_pacientes_por_estado(function_args.get('estado', ''), pacientes_permitidos)
            elif function_name == "generar_enlace_pdf_paciente":
                 tool_result_obj = _internal_generar_enlace_pdf(function_args.get('nombre_o_id_paciente', ''), pacientes_permitidos)
            elif function_name == "buscar_en_la_web":
                tool_result_obj = _internal_buscar_web(function_args.get('query', ''))
            else:
                tool_result_obj = {"error": f"Herramienta desconocida: {function_name}"}

            debug_print(f"Resultado de la herramienta ({function_name}): {tool_result_obj}")
            
            response = chat_session.send_message(
                content_types.to_content(genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(name=function_name, response={"result": tool_result_obj})
                ))
            )
        
        response_text = "".join(part.text for part in response.candidates[0].content.parts) if response.candidates and response.candidates[0].content.parts else ""
        if not response_text.strip():
            debug_print(f"El modelo no devolvió una respuesta de texto. Respuesta completa: {response}")
            response_text = "No pude procesar la solicitud para generar una respuesta de texto. Por favor, intenta reformular tu pregunta."
        
        chat_history.append({'role': 'user', 'parts': [{'text': query}]})
        chat_history.append({'role': 'model', 'parts': [{'text': response_text}]})
        cache.set(session_key, chat_history, timeout=600)
        
        html_response = response_text.replace('\n', '<br>')
        html_response = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_response)
        html_response = re.sub(r'\* (.*?)(<br>|$)', r'<li>\1</li>', html_response)
        if '<li>' in html_response: html_response = f"<ul>{html_response.replace('<br>', '')}</ul>"

        return {'response': html_response, 'suggestions': []}

    except Exception as e:
        error_details = traceback.format_exc()
        debug_print(f"Error CRÍTICO en get_bot_response: {e}\n{error_details}")
        return {'response': "Lo siento, ha ocurrido un error inesperado en el asistente. El equipo técnico ha sido notificado.", 'suggestions': []}

# ==============================================================================
# === VISTA DE API (ENDPOINT DE DJANGO) ========================================
# ==============================================================================
@csrf_exempt
@require_http_methods(["POST"])
@login_required
def chat_api(request):
    try:
        data = json.loads(request.body)
        query = data.get('query')
        if not query: return JsonResponse({'error': 'Falta la consulta (query).'}, status=400)
        bot_data = get_bot_response(query, request.user)
        ChatInteraction.objects.create(user=request.user, user_query=query, bot_response=bot_data.get('response', ''))
        return JsonResponse(bot_data)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Cuerpo de la petición inválido (no es JSON).'}, status=400)
    except Exception as e:
        debug_print(f"Error en la vista chat_api: {e}")
        return JsonResponse({'error': f'Error en el servidor: {e}'}, status=500)