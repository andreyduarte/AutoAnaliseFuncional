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

app = Flask(__name__)

# Initialize the database
init_db()
# Confere estado do DB
all_analyses = get_all_analyses()
app.logger.info(f"Análises salvas no Banco de Dados: {len(all_analyses)}")

# Create static/json/examples directory if it doesn't exist
examples_dir = os.path.join('static', 'json', 'examples')
os.makedirs(examples_dir, exist_ok=True)

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
def analise_route(): # Renamed to avoid conflict with imported 'analisar'
    texto_entrada = request.form.get('texto_entrada', '')
    if not texto_entrada:
        # Handle empty input, maybe return an error or redirect
        return redirect(url_for('index'))

    # Calls the analysis function from analysis.py
    json_analisado_dict = analisar(texto_entrada)

    if not json_analisado_dict:
        # Handle analysis failure
        # You might want to flash a message to the user here
        return redirect(url_for('index'))

    # Add original text to the analysis dictionary before saving
    json_analisado_dict['texto_original'] = texto_entrada
    
    # Convert the dict to a JSON string for storage
    analysis_data_json_string = json.dumps(json_analisado_dict)

    # Create a name for the analysis (e.g., based on timestamp or first few words)
    # For now, using a timestamp
    analysis_name = f"Análise de {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    try:
        # Save to database
        analysis_uuid = insert_analysis(
            name=analysis_name,
            analysis_data=analysis_data_json_string
        )
        # Redirect to the new view page for this analysis
        return redirect(url_for('view_analysis_route', analysis_uuid=analysis_uuid))
    except Exception as e:
        # Log the error
        app.logger.error(f"Error saving analysis to database: {e}")
        # Flash a message to the user
        # For now, redirect to index
        return redirect(url_for('index'))

@app.route('/explanation')
def explanation_page():
    """Renders the explanation page."""
    return render_template('explanation.html')

@app.route('/analysis/download/<string:analysis_uuid>')
def download_analysis_route(analysis_uuid):
    analysis_record = get_analysis_by_uuid(analysis_uuid)

    if not analysis_record:
        app.logger.warn(f"Download request for non-existent analysis UUID {analysis_uuid}")
        # Or return a 404 error page
        return '404 Not Found'

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)