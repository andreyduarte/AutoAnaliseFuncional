# app.py
import os
import glob # For finding files
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response # Added Response
import io # For BytesIO
import json # Import json para serializar para o template
from analysis import analisar # Importa a função do arquivo analysis.py
from utils import transformar_para_vis # Importa a função do arquivo utils.py
import datetime # Added
from db import init_db, insert_analysis, get_analysis_by_uuid, get_all_analyses # New import for this route
import uuid
import threading # For potential future async, but also for thread-safe access to shared dict if needed
from functools import partial # To pass task_id to record_progress easily
import time # For timestamps

app = Flask(__name__)

ANALYSIS_PROGRESS_STORE = {}
# Using a lock for updating the shared dictionary, good practice even if Flask is single-threaded per request by default.
# For a multi-worker setup, a proper external store (Redis, DB) would be needed.
PROGRESS_STORE_LOCK = threading.Lock()

# Initialize the database
init_db()
# Confere estado do DB
all_analyses = get_all_analyses()
app.logger.info(f"Análises salvas no Banco de Dados: {len(all_analyses)}")

# Create static/json/examples directory if it doesn't exist
examples_dir = os.path.join('static', 'json', 'examples')
os.makedirs(examples_dir, exist_ok=True)

def record_progress(task_id, message_text, message_type='info', status_update=None, current_step_name=None):
    with PROGRESS_STORE_LOCK:
        if task_id not in ANALYSIS_PROGRESS_STORE:
            ANALYSIS_PROGRESS_STORE[task_id] = {
                'status': 'queued',
                'messages': [],
                'current_step_name': '',
                'start_time': time.time()
            }

        entry = ANALYSIS_PROGRESS_STORE[task_id]

        log_message = {
            'timestamp': datetime.datetime.now().isoformat(),
            'text': message_text,
            'type': message_type
        }
        entry['messages'].append(log_message)

        if status_update:
            entry['status'] = status_update
        if current_step_name:
            entry['current_step_name'] = current_step_name

        # Optional: log to console as well
        # app.logger.info(f"Progress for {task_id} [{message_type}]: {message_text}")

@app.route('/')
def index():
    json_data_main = get_analysis_by_uuid('0849e1cd-c9c6-4402-bb48-b388571fd091') # Usuário da Ferramenta
    try:
        nodes_main, edges_main = transformar_para_vis(json.loads(json_data_main['analysis_data']))
        nodes_data_main = json.dumps(nodes_main)
        edges_data_main = json.dumps(edges_main)
    except Exception as e:
        app.logger.error(f"Error loading main example for index page: {e}")
        # nodes_data_main and edges_data_main will remain empty

    examples = [{"name":"A Águia e a Raposa","uuid":'bb224eba-ec17-4e54-9b0c-29eda1d73eeb'}, 
                {"name":"A Gansa dos Ovos de Ouro","uuid":'745a94dd-c678-457e-b2f1-e1961bd7f213'}, 
                {"name":"O Ladrão e o Cão de Guarda","uuid":'10f36ec9-efa9-4ce6-af17-bec598d29292'}, 
                {"name":"Rato do Campo e Rato da Cidade","uuid":'39ea7ddb-fb2a-4b8a-8c23-a27bb4fbf4c4'}]

    return render_template('index.html',
                           nodes_data=nodes_data_main, # For the main visualization
                           edges_data=edges_data_main, # For the main visualization
                           examples=examples) # For the static examples dropdown

@app.route('/analise', methods=['POST'])
def analise_route():
    texto_entrada = request.form.get('texto_entrada', '')
    if not texto_entrada:
        # No task_id generated, just redirect or return error
        return redirect(url_for('index')) # Consider flashing an error

    task_id = uuid.uuid4().hex
    
    # Initialize progress for this task
    record_progress(task_id, "Análise solicitada.", message_type='info', status_update='queued', current_step_name="Iniciando")

    try:
        # Pass a recording function specific to this task_id to analisar
        # This uses functools.partial to pre-fill the task_id argument
        task_specific_recorder = partial(record_progress, task_id)

        record_progress(task_id, "Processamento da análise iniciado.", message_type='info', status_update='running', current_step_name="Processando")

        # Modify 'analisar' in analysis.py to accept 'progress_recorder' callable
        json_analisado_dict = analisar(texto_entrada, progress_recorder=task_specific_recorder)

        if not json_analisado_dict:
            record_progress(task_id, "Falha na análise: nenhum resultado retornado.", message_type='error', status_update='error')
            # Render index page with task_id so user can see the error log
            # Re-fetch default index data and examples for error page:
            json_data_main_error = get_analysis_by_uuid('0849e1cd-c9c6-4402-bb48-b388571fd091')
            nodes_main_error, edges_main_error = [], []
            if json_data_main_error:
                try:
                    nodes_main_error, edges_main_error = transformar_para_vis(json.loads(json_data_main_error['analysis_data']))
                except Exception as transform_e:
                    app.logger.error(f"Error transforming main example for error page: {transform_e}")
            examples_error = [{"name":"A Águia e a Raposa","uuid":'bb224eba-ec17-4e54-9b0c-29eda1d73eeb'},
                              {"name":"A Gansa dos Ovos de Ouro","uuid":'745a94dd-c678-457e-b2f1-e1961bd7f213'},
                              {"name":"O Ladrão e o Cão de Guarda","uuid":'10f36ec9-efa9-4ce6-af17-bec598d29292'},
                              {"name":"Rato do Campo e Rato da Cidade","uuid":'39ea7ddb-fb2a-4b8a-8c23-a27bb4fbf4c4'}]
            return render_template('index.html', task_id_from_server=task_id, error_message="Análise falhou.",
                                   nodes_data=json.dumps(nodes_main_error), edges_data=json.dumps(edges_main_error), examples=examples_error)

        json_analisado_dict['texto_original'] = texto_entrada
        analysis_data_json_string = json.dumps(json_analisado_dict)
        analysis_name = f"Análise de {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        record_progress(task_id, "Análise do texto concluída, salvando resultados...", message_type='info')

        analysis_uuid_db = insert_analysis(
            name=analysis_name,
            analysis_data=analysis_data_json_string
        )

        record_progress(task_id, f"Resultados salvos com ID: {analysis_uuid_db}.", message_type='success', status_update='complete', current_step_name="Concluído")

        return redirect(url_for('view_analysis_route', analysis_uuid=analysis_uuid_db))

    except Exception as e:
        app.logger.error(f"Erro durante a análise para task {task_id}: {e}", exc_info=True)
        record_progress(task_id, f"Erro crítico durante a análise: {str(e)}", message_type='error', status_update='error')

        json_data_main_error = get_analysis_by_uuid('0849e1cd-c9c6-4402-bb48-b388571fd091')
        nodes_main_error, edges_main_error = [], []
        if json_data_main_error:
            try:
                nodes_main_error, edges_main_error = transformar_para_vis(json.loads(json_data_main_error['analysis_data']))
            except Exception as transform_e:
                app.logger.error(f"Error transforming main example for error page: {transform_e}")

        examples_error = [{"name":"A Águia e a Raposa","uuid":'bb224eba-ec17-4e54-9b0c-29eda1d73eeb'},
                          {"name":"A Gansa dos Ovos de Ouro","uuid":'745a94dd-c678-457e-b2f1-e1961bd7f213'},
                          {"name":"O Ladrão e o Cão de Guarda","uuid":'10f36ec9-efa9-4ce6-af17-bec598d29292'},
                          {"name":"Rato do Campo e Rato da Cidade","uuid":'39ea7ddb-fb2a-4b8a-8c23-a27bb4fbf4c4'}]

        return render_template('index.html',
                               task_id_from_server=task_id,
                               error_message=f"Erro na análise: {str(e)}",
                               nodes_data=json.dumps(nodes_main_error),
                               edges_data=json.dumps(edges_main_error),
                               examples=examples_error)

@app.route('/explanation')
def explanation_page():
    """Renders the explanation page."""
    return render_template('explanation.html')

# @app.route('/download')
# def download():
#     # Faz o download do arquivo output.json
#     output_file = os.path.join('static', 'json', 'output.json')
#     return render_template('download.html', output_file=output_file)

@app.route('/analysis/download/<string:analysis_uuid>')
def download_analysis_route(analysis_uuid):
    analysis_record = get_analysis_by_uuid(analysis_uuid)

    if not analysis_record:
        app.logger.warn(f"Download request for non-existent analysis UUID {analysis_uuid}")
        # Or return a 404 error page
        return redirect(url_for('index'))

    analysis_data_json_string = analysis_record['analysis_data']
    analysis_name = analysis_record['name']

    # Sanitize the filename a bit (optional, but good practice)
    safe_filename = "".join(c if c.isalnum() or c in (' ', '.', '_') else '_' for c in analysis_name)
    if not safe_filename.lower().endswith(".json"):
        safe_filename += ".json"

    # Ensure it's not too long
    safe_filename = safe_filename[:100] if len(safe_filename) > 100 else safe_filename


    return Response(
        analysis_data_json_string,
        mimetype="application/json",
        headers={"Content-disposition": f"attachment; filename={safe_filename}"}
    )

@app.route('/examples')
def show_examples():
    """Lists available example JSON files."""
    current_examples_dir = os.path.join('static', 'json', 'examples') # Use the global or redefine for clarity
    if not os.path.exists(current_examples_dir):
        os.makedirs(current_examples_dir) # Ensure it exists if somehow deleted after app start
        
    example_file_paths = glob.glob(os.path.join(current_examples_dir, '*.json'))
    example_filenames = sorted([os.path.basename(p) for p in example_file_paths])
    return render_template('examples.html', example_files=example_filenames)

@app.route('/load_example/<path:example_filename>')
def load_example(example_filename):
    """Loads a selected example JSON into the main output.json and redirects to index."""
    example_file_path = os.path.join('static', 'json', 'examples', example_filename)

    if not os.path.exists(example_file_path):
        # TODO: Implement flash messaging for "Example not found"
        print(f"Error: Example file not found at {example_file_path}")
        return redirect(url_for('show_examples'))

    try:
        with open(example_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        nodes, edges = transformar_para_vis(json_data)
        return render_template('network.html',
                               nodes_data=json.dumps(nodes),
                               edges_data=json.dumps(edges),
                               texto_original=json_data['texto_original'],
                               timeline_data=json.dumps(json_data.get('timeline', [])))

    except Exception as e:
        # TODO: Implement flash messaging for "Error loading example"
        print(f"Error loading example {example_filename}: {e}")
        return redirect(url_for('show_examples'))

@app.route('/analysis/view/<string:analysis_uuid>')
def view_analysis_route(analysis_uuid):
    analysis_record = get_analysis_by_uuid(analysis_uuid)
    print(f"Viewing analysis with UUID: {analysis_uuid}")
    print(f"Analysis record: {analysis_record}")

    if not analysis_record:
        # Handle case where analysis_uuid is not found
        # Maybe redirect to an error page or the main list
        # For now, redirect to index and flash a message (if flash is set up)
        # flash("Análise não encontrada.", "error") # Example if using flash messages
        app.logger.warn(f"Analysis with UUID {analysis_uuid} not found.")
        return redirect(url_for('index'))

    try:
        # The 'analysis_data' is stored as a JSON string, so parse it
        analysis_data_dict = json.loads(analysis_record['analysis_data'])

        # The 'narrative_text' is stored directly
        narrative_text = analysis_data_dict.get('texto_original', '')

        # Ensure 'texto_original' is in analysis_data_dict for transformar_para_vis if it expects it
        # Based on previous logic, 'texto_original' is part of the JSON saved in 'analysis_data'
        # If transformar_para_vis expects it as a separate top-level key from the DB record, adjust accordingly
        # For now, assume 'texto_original' is within analysis_data_dict as 'texto_original'

        nodes, edges = transformar_para_vis(analysis_data_dict)

        timeline_data = analysis_data_dict.get('timeline', [])

        return render_template('network.html',
                               nodes_data=json.dumps(nodes),
                               edges_data=json.dumps(edges),
                               texto_original=narrative_text, # Use narrative_text from DB record
                               timeline_data=json.dumps(timeline_data),
                               analysis_name=analysis_record['name'], # Pass the name for display
                               analysis_uuid=analysis_uuid) # Pass UUID for potential use in template (e.g. download link)
    except Exception as e:
        app.logger.error(f"Error processing analysis {analysis_uuid} for viewing: {e}")
        # flash("Erro ao carregar a análise.", "error") # Example
        return redirect(url_for('index'))

@app.route('/analysis_progress/<string:task_id>', methods=['GET'])
def analysis_progress_route(task_id):
    with PROGRESS_STORE_LOCK: # Use lock for reading in case of complex data or future updates here
        task_info = ANALYSIS_PROGRESS_STORE.get(task_id)

    if not task_info:
        return jsonify({'status': 'error', 'messages': [{'text': 'Task ID not found.', 'type': 'error'}]}), 404

    # Determine if the task is "finished" (either complete or error) for the client
    # The client-side progress_logger.js expects 'complete' or 'error' to stop polling.
    # We can add a 'finished' status internally if needed, but for client, map to 'complete' or 'error'.
    client_status = task_info.get('status', 'unknown')

    # To ensure the client stops polling correctly, if our internal status is 'complete' or 'error',
    # we pass that through. If it's something else like 'queued' or 'running', it's still 'running' for the client.
    if client_status not in ['complete', 'error']:
        # If start_time exists and it's been too long (e.g. > 1 hour) without completion,
        # consider it timed out / error. (Optional timeout logic)
        # For now, any non-complete/error status is 'running' unless explicitly set otherwise.
        pass # status remains as is ('running', 'queued', etc.)


    return jsonify({
        'status': client_status,
        'messages': task_info.get('messages', []),
        'current_step_name': task_info.get('current_step_name', ''),
        # Add any other fields the client might need from task_info
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)