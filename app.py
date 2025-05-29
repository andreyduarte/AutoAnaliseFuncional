# app.py
import os
import glob # For finding files
from flask import Flask, render_template, request, jsonify, redirect, url_for # Added redirect, url_for
import json # Import json para serializar para o template
from analysis import analisar # Importa a função do arquivo analysis.py
from utils import transformar_para_vis # Importa a função do arquivo utils.py

app = Flask(__name__)

# Create static/json/examples directory if it doesn't exist
examples_dir = os.path.join('static', 'json', 'examples')
os.makedirs(examples_dir, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analise', methods=['POST'])
def analise():
    texto_entrada = request.form.get('texto_entrada', '')
    print(texto_entrada) # Para depuração, imprime o texto de entrada no console
    # Chama a função analisar para obter o JSON
    json_analisado = analisar(texto_entrada) # Esta função vem de analysis.py
    
    # Transforma o JSON para o formato do Vis.js
    nodes, edges = transformar_para_vis(json_analisado)
    
    # Salva outém o JSON em um arquivo
    output_file = os.path.join('static', 'json', 'output.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json_analisado['texto_original'] = texto_entrada
        json.dump(json_analisado, f, indent=4)

    # Renderiza a página da rede, passando os dados dos nós, arestas e timeline
    return render_template('network.html', 
                            nodes_data=json.dumps(nodes), 
                            edges_data=json.dumps(edges),
                            texto_original=texto_entrada,
                            timeline_data=json.dumps(json_analisado.get('timeline', [])))


@app.route('/explanation')
def explanation_page():
    """Renders the explanation page."""
    return render_template('explanation.html')

@app.route('/new', methods=['GET', 'POST'])
def new():
    # Limpa o arquivo output.json
    output_file = os.path.join('static', 'json', 'output.json')
    if os.path.exists(output_file):
        os.remove(output_file)
    
    # Renderiza a página inicial com o formulário
    return render_template('index.html')

@app.route('/download')
def download():
    # Faz o download do arquivo output.json
    output_file = os.path.join('static', 'json', 'output.json')
    return render_template('download.html', output_file=output_file)

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

if __name__ == '__main__':
    app.run(debug=True)
