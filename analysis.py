from output_schemas import RedeContingencialOutput, Step1Output, Step2Output, Step3Output
from typing import List, Optional, Union, Literal, Dict, Any, cast
from pydantic import BaseModel, Field, ValidationError
from google.genai import types
from dotenv import load_dotenv
from google import genai
import logging
import json
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Prompts ---
SYSTEM_PROMPT = """
Você é um assistente especializado em Análise do Comportamento. Sua tarefa é aplicar um procedimento metodológico para extrair e estruturar informações de um texto narrativo ou descritivo, transformando-o em uma representação de rede contingencial.

Esta rede é composta por Nós (objetos da análise: Sujeitos, Estímulos_Evento, Acoes_Comportamento, Condicoes_Estado, Hipoteses_Analiticas) e Arestas (relações funcionais e temporais entre os nós).

Você receberá instruções para focar em etapas específicas do procedimento e gerar apenas as partes do JSON correspondentes a essas etapas. Use os IDs dos nós e arestas de forma consistente e incremental (S1, S2, E1, E2, AC1, AR1, etc.). Gere `data_formulacao` para Hipoteses_Analiticas com a data e hora atuais no formato ISO (YYYY-MM-DDTHH:MM:SS.ffffff).

Se informações cruciais não estiverem explícitas no texto, você pode fazer inferências cautelosas, mas deve indicar o nível de inferência ou a fonte da informação nos atributos apropriados. Se uma informação for ambígua, registre a ambiguidade.
Certifique-se de que o JSON de saída para cada chamada seja um objeto único contendo APENAS as listas de nós e arestas relevantes para as etapas solicitadas nessa chamada. O JSON deve começar com '{' e terminar com '}'. Não adicione nenhum texto explicativo antes ou depois do JSON.
"""

# Conteúdo da AFC e do Procedimento Etapas 1-6
PROCEDIMENTO_COMPLETO_AFC = """
### Conceitos Fundamentais da Análise Funcional do Comportamento (AFC) 🧐

A **Análise Funcional do Comportamento (AFC)** é uma abordagem da psicologia comportamental que busca entender o comportamento identificando as relações funcionais entre ele e as variáveis ambientais. O foco está em como os eventos **antecedentes** (o que acontece antes do comportamento) e os eventos **consequentes** (o que acontece depois do comportamento) influenciam a probabilidade de um comportamento ocorrer novamente.

Componentes chave incluem:
* **Comportamento (Resposta):** A ação do organismo.
* **Antecedentes:** Estímulos ou contextos que estabelecem a ocasião para o comportamento. Podem ser:
    * **Estímulos Discriminativos ($S^D$):** Sinalizam que uma resposta específica provavelmente será reforçada.
    * **Estímulos Delta ($S^\\Delta$):** Sinalizam que uma resposta específica provavelmente não será reforçada.
    * **Operações Motivadoras (OMs):** Alteram temporariamente a eficácia de certas consequências como reforçadoras ou punitivas e a frequência de comportamentos relevantes para essas consequências. Podem ser **Estabelecedoras (OEs)**, que aumentam a eficácia e a frequência, ou **Abolidoras (OAs)**, que diminuem.
* **Consequências:** Eventos que seguem o comportamento e alteram sua probabilidade futura. Podem ser:
    * **Reforçamento (SR):** Aumenta a probabilidade do comportamento.
        * **Positivo ($S^{{R+}}$):** Adição de um estímulo agradável.
        * **Negativo ($S^{{R-}}$):** Remoção de um estímulo aversivo.
    * **Punição (SP):** Diminui a probabilidade do comportamento.
        * **Positiva ($S^{{P+}}$):** Adição de um estímulo aversivo.
        * **Negativa ($S^{{P-}}$):** Remoção de um estímulo agradável.
    * **Extinção (EXT):** Um comportamento previamente reforçado deixa de sê-lo, levando à diminuição gradual de sua frequência.
* **Função do Comportamento:** O propósito que o comportamento serve para o indivíduo, geralmente relacionado à obtenção de algo desejado (atenção, tangíveis, estimulação sensorial) ou à evitação/fuga de algo indesejado.

A **tríplice contingência** (Antecedente-Comportamento-Consequência, ou A-B-C) é a unidade básica de análise.

### Procedimento de Extração de Nós e Arestas (Até Etapa 6) 📝

Com base no texto narrativo fornecido, siga as etapas abaixo para construir a rede contingencial.

**Etapa 1: Leitura Inicial e Identificação de Entidades Centrais**
* **Objetivo:** Identificar os atores principais e suas ações mais evidentes.
* **1.1: Identificar `Sujeito(s)`:**
    * Localize os indivíduos centrais na narrativa.
    * Para cada um, crie um **Nó `Sujeito`** e preencha seus atributos (`id_sujeito`, `nome_descritivo`, `idade`, `historico_relevante`, `especie`, `observacoes_adicionais`).
* **1.2: Identificar `Acao_Comportamento(s)` Principais:**
    * Liste as ações ou comportamentos emitidos pelo(s) `Sujeito(s)`.
    * Para cada ação, crie um **Nó `Acao_Comportamento`** e preencha seus atributos (`id_acao`, `descricao_topografica`, `tipo_observabilidade`, `frequencia_base_periodo`, `duracao_media_seg`, `intensidade_media`, `latencia_tipica_resposta_seg`, `classe_funcional_hipotetica`, `observacoes_adicionais`).
    * Crie uma **Aresta `Emissao_Comportamental`** (com `id_aresta`, `id_origem_no` = ID do Sujeito, `id_destino_no` = ID da Acao_Comportamento, `data_hora_especifica_emissao`, `observacoes_adicionais`).

**Etapa 2: Mapeamento de `Estímulos_Evento` Imediatamente Associados às `Acoes_Comportamento`**
* **Objetivo:** Identificar eventos que ocorrem imediatamente antes e depois das ações.
* **2.1: Identificar Antecedentes Imediatos:**
    * Para cada `Acao_Comportamento`, identifique eventos/objetos/ações de outros que ocorreram logo antes.
    * Crie **Nós `Estímulo_Evento`** para esses antecedentes e preencha seus atributos (`id_estimulo_evento`, `descricao`, `tipo_fisico`, `modalidade_sensorial_primaria`, `intensidade_percebida_inicial`, `duracao_estimulo_evento_seg`, `localizacao`, `data_hora_ocorrencia`, `observacoes_adicionais`).
    * Crie uma **Aresta `Relacao_Temporal`** (com `id_aresta`, `id_origem_no` = ID do Estímulo_Evento antecedente, `id_destino_no` = ID da Acao_Comportamento, `tipo_temporalidade = "PRECEDE_IMEDIATAMENTE"`, `intervalo_atraso_seg`, `contiguidade_percebida`, `observacoes_adicionais`).
* **2.2: Identificar Consequências Imediatas:**
    * Para cada `Acao_Comportamento`, identifique eventos/objetos/ações de outros que ocorreram logo depois.
    * Crie **Nós `Estímulo_Evento`** para essas consequências e preencha seus atributos.
    * Crie uma **Aresta `Relacao_Temporal`** (com `id_aresta`, `id_origem_no` = ID da Acao_Comportamento, `id_destino_no` = ID do Estímulo_Evento consequente, `tipo_temporalidade = "SUCEDE_IMEDIATAMENTE"`, `intervalo_atraso_seg`, `contiguidade_percebida`, `observacoes_adicionais`).

**Etapa 3: Estabelecimento de Sequências Contingenciais Básicas (Cadeias A-B-C)**
* **Objetivo:** Formar as unidades básicas da análise (Antecedente-Comportamento-Consequência).
* **3.1: Formar Tríades A-B-C:**
    * Crie **Arestas `Relacao_Funcional_Antecedente`** (com `id_aresta`, `id_origem_no` = ID do Estímulo_Evento antecedente, `id_destino_no` = ID da Acao_Comportamento, `funcao_antecedente` - pode ser "A_DEFINIR" inicialmente, `prob_resposta_na_presenca`, `prob_resposta_na_ausencia`, `historico_pareamento`, `observacoes_adicionais`).
    * Crie **Arestas `Relacao_Funcional_Consequente`** (com `id_aresta`, `id_origem_no` = ID da Acao_Comportamento, `id_destino_no` = ID do Estímulo_Evento consequente, `funcao_consequente` - pode ser "A_DEFINIR" inicialmente, `imediatismo_consequencia`, `magnitude_consequencia`, `esquema_de_entrega`, `parametro_esquema`, `efeito_observado_na_frequencia_futura`, `observacoes_adicionais`).
* **3.2: Identificar Cadeias Comportamentais:**
    * Observe se a consequência de uma A-B-C serve como antecedente para a próxima.

**Etapa 4: Identificação de `Condicoes_Estado` (Moduladores)**
* **Objetivo:** Identificar contextos mais amplos, estados do sujeito ou OMs que influenciam as relações A-B-C.
* **4.1: Identificar Operações Motivadoras (OMs):**
    * Procure menções a privação, saciação, eventos aversivos antecedentes.
    * Crie **Nós `Condicao_Estado`** e preencha `id_condicao_estado`, `descricao`, `tipo_condicao = "Operação Motivadora"`, `duracao_condicao_desc`, `data_hora_inicio`, `observacoes_adicionais`.
* **4.2: Identificar Contextos Gerais:**
    * Procure descrições de ambientes, momentos do dia, presença de pessoas específicas.
    * Crie **Nós `Condicao_Estado`** e preencha `id_condicao_estado`, `descricao`, `tipo_condicao = "Contexto Ambiental Geral"`, etc.
* **4.3: Identificar Estados Fisiológicos/Emocionais Duradouros:**
    * Procure menções a doenças, dor, estados de humor persistentes.
    * Crie **Nós `Condicao_Estado`** e preencha `id_condicao_estado`, `descricao`, `tipo_condicao` apropriado, etc.

**Etapa 5: Atribuição de Funções e Detalhamento das Relações**
* **Objetivo:** Preencher os atributos funcionais das arestas criadas e conectar as Condicoes_Estado.
* **5.1: Detalhar Arestas `Relacao_Funcional_Antecedente`:**
    * Com base no texto, inferir e preencher `funcao_antecedente` e outros atributos relevantes.
* **5.2: Detalhar Arestas `Relacao_Funcional_Consequente`:**
    * Com base no texto, inferir e preencher `funcao_consequente` e outros atributos relevantes.
* **5.3: Conectar e Detalhar `Relacoes_Moduladoras_Estado`:**
    * Crie **Arestas `Relacao_Moduladora_Estado`** (com `id_aresta`, `id_origem_no` = ID da Condicao_Estado, `id_destino_no` = ID do Nó modulado) entre as `Condicoes_Estado` e os `Estímulos_Evento` ou `Acoes_Comportamento` que elas modulam.
    * Preencha os atributos da aresta (`tipo_modulacao_estado`, `alvo_da_modulacao_valor_ref_id_estimulo`, `descricao_efeito_modulatorio_valor`, `alvo_da_modulacao_frequencia_ref_id_acao`, `descricao_efeito_modulatorio_frequencia`, `observacoes_adicionais`).

**Etapa 6: Formulação e Adição de Nós `Hipotese_Analitica`**
* **Objetivo:** Formular hipóteses sobre as funções do comportamento com base na análise.
* **Como:** Para cada função comportamental principal inferida ou conjunto significativo de relações A-B-C-OM, formule uma declaração de hipótese.
* **Saída:**
    * Crie **Nós `Hipotese_Analitica`** e preencha seus atributos (`id_hipotese`, `descricao_hipotese`, `nivel_confianca`, `data_formulacao` - use a data e hora atuais no formato ISO, `status_hipotese`, `observacoes_adicionais`).
    * Crie **Arestas `Evidencia_Para_Hipotese`** (com `id_aresta`, `id_origem_no` - pode ser o ID da Acao_Comportamento central da hipótese, `id_destino_no` = ID da Hipotese_Analitica, `ids_elementos_contingencia_suporte` - lista de IDs de Nós e Arestas que suportam a hipótese, `tipo_evidencia`, `fonte_dados = "Narrativa Textual"`, `observacoes_adicionais`).
"""

def _make_api_call(
    client: genai.Client,
    model_name: str,
    prompt_content: str,
    schema: Optional[BaseModel] = None # Removido para evitar erro de schema complexo
) -> Optional[Dict[str, Any]]:
    """Função auxiliar para fazer uma chamada à API e processar a resposta."""
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt_content)],
        ),
    ]
    
    if schema:
        generate_content_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
            temperature=0.2
        )
    else:
        generate_content_config = types.GenerateContentConfig(
            temperature=0.2
        )

    logger.info(f"Enviando solicitação para o modelo Gemini ({model_name})...")
    
    full_response_text = ""
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=cast(List[types.Content], contents),
            config=generate_content_config,
        )
        full_response_text = response.text
    except Exception as e_gc:
        logger.warning(f"Falha ao usar client.models.generate_content: {e_gc}")

    logger.info("Resposta recebida do modelo.")
    
    if not full_response_text:
        logger.error("Resposta do modelo está vazia.")
        return None

    json_text = full_response_text.strip()
    if json_text.startswith("```json"):
        json_text = json_text.strip()[7:-3].strip()
    elif json_text.startswith("```"):
            json_text = json_text.strip()[3:-3].strip()

    logger.debug(f"Texto JSON bruto recebido: {json_text[:500]}...")

    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar JSON: {e}. Resposta: {full_response_text}")
        return None

def analisar_texto_para_rede_contingencial_client_api(
    texto_narrativo: str,
    model_name: str = "gemini-2.0-flash-exp", # Conforme solicitado pelo usuário
    debug: bool = False
):
    
    # loading Env
    load_dotenv()

    # setando o nível de log
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Verifica se a chave da API está configurada
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error(f"Variável de ambiente GEMINI_API_KEY não encontrada.")
        print(f"Erro: Chave da API Gemini não configurada na variável de ambiente GEMINI_API_KEY.")
        return None

    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        logger.error(f"Falha ao inicializar genai.Client: {e}", exc_info=True)
        print(f"Erro ao inicializar cliente Gemini: {e}")
        return None

    # Cria uma instância do modelo de saída
    rede_final = RedeContingencialOutput()
    
    # --- CHAMADA 1: Etapas 1 e 2 ---
    prompt_call_1 = (
        f"{SYSTEM_PROMPT}\n\n"
        f"{PROCEDIMENTO_COMPLETO_AFC}\n\n" 
        "FOCO DESTA CHAMADA: Execute APENAS as Etapas 1 e 2 do procedimento fornecido.\n"
        "No seu JSON de saída, inclua APENAS as seguintes chaves do modelo RedeContingencialOutput: "
        "`sujeitos`, `acoes_comportamentos`, `emissoes_comportamentais`, "
        "`estimulos_eventos` (apenas os identificados como antecedentes e consequências imediatas nessas etapas), "
        "e `relacoes_temporais`.\n\n"
        f"Texto narrativo para análise:\n```\n{texto_narrativo}\n```"
    )
    logger.info("Iniciando Chamada 1 da API (Etapas 1 e 2)...")
    json_data_1 = _make_api_call(client, model_name, prompt_call_1, Step1Output)

    if not json_data_1:
        logger.error("Chamada 1 da API falhou ou retornou dados inválidos.")
        return None
    
    try:
        for key in json_data_1:
            rede_final.__setattr__(key, rede_final.__getattribute__(key) + json_data_1[key])
        logger.info("Dados da Chamada 1 processados.")
    except ValidationError as e:
        logger.error(f"Erro de validação Pydantic na Chamada 1: {e}")
        logger.error(f"Dados JSON da Chamada 1 que falharam: {json.dumps(json_data_1, indent=2)}")
        return None
    except KeyError as e:
        logger.error(f"Chave ausente nos dados JSON da Chamada 1: {e}")
        logger.error(f"Dados JSON da Chamada 1: {json.dumps(json_data_1, indent=2)}")
        return None
    except TypeError as e: # Para capturar erros se uma lista esperada for None
        logger.error(f"Erro de tipo (provavelmente lista None) na Chamada 1: {e}")
        logger.error(f"Dados JSON da Chamada 1: {json.dumps(json_data_1, indent=2)}")
        return None


    # --- CHAMADA 2: Etapas 3 e 4 ---
    contexto_para_call_2 = {
        "sujeitos": rede_final.sujeitos,
        "acoes_comportamentos": rede_final.acoes_comportamentos,
        "estimulos_eventos_identificados_ate_agora": rede_final.estimulos_eventos
    }
    prompt_call_2 = (
        f"{SYSTEM_PROMPT}\n\n"
        f"{PROCEDIMENTO_COMPLETO_AFC}\n\n"
        "FOCO DESTA CHAMADA: Execute APENAS as Etapas 3 e 4 do procedimento fornecido.\n"
        "Utilize os IDs dos sujeitos, ações e estímulos_eventos fornecidos no contexto abaixo para criar as novas arestas. "
        "Se precisar criar novos `Estímulos_Evento` (que não foram identificados na chamada anterior) ou `Condicoes_Estado` durante estas etapas, adicione-os."
        "No seu JSON de saída, inclua APENAS as seguintes chaves do modelo RedeContingencialOutput: "
        "`estimulos_eventos` (apenas os novos ou atualizados), `condicoes_estados`, "
        "`relacoes_funcionais_antecedentes`, e `relacoes_funcionais_consequentes`.\n\n"
        f"Contexto da análise anterior (use estes IDs para criar relações):\n```json\n{json.dumps(contexto_para_call_2, indent=2, ensure_ascii=False)}\n```\n\n"
        f"Texto narrativo original para análise (relembre se necessário):\n```\n{texto_narrativo}\n```"
    )
    logger.info("Iniciando Chamada 2 da API (Etapas 3 e 4)...")
    json_data_2 = _make_api_call(client, model_name, prompt_call_2, Step2Output)

    if not json_data_2:
        logger.error("Chamada 2 da API falhou ou retornou dados inválidos.")
        return rede_final # Retorna o que foi construído até agora

    try:
        for key in json_data_2:
            rede_final.__setattr__(key, rede_final.__getattribute__(key) + json_data_2[key])
        logger.info("Dados da Chamada 2 processados.")
    except ValidationError as e:
        logger.error(f"Erro de validação Pydantic na Chamada 2: {e.to_json(indent=2)}")
        logger.error(f"Dados JSON da Chamada 2 que falharam: {json.dumps(json_data_2, indent=2)}")
        return rede_final 
    except KeyError as e:
        logger.error(f"Chave ausente nos dados JSON da Chamada 2: {e}")
        logger.error(f"Dados JSON da Chamada 2: {json.dumps(json_data_2, indent=2)}")
        return rede_final
    except TypeError as e:
        logger.error(f"Erro de tipo (provavelmente lista None) na Chamada 2: {e}")
        logger.error(f"Dados JSON da Chamada 2: {json.dumps(json_data_2, indent=2)}")
        return rede_final


    # --- CHAMADA 3: Etapas 5 e 6 ---
    contexto_para_call_3 = {
        "sujeitos": rede_final.sujeitos,
        "acoes_comportamentos": rede_final.acoes_comportamentos,
        "estimulos_eventos": rede_final.estimulos_eventos,
        "condicoes_estados": rede_final.condicoes_estados,
        "relacoes_funcionais_antecedentes": rede_final.relacoes_funcionais_antecedentes,
        "relacoes_funcionais_consequentes": rede_final.relacoes_funcionais_consequentes,
        "relacoes_temporais": rede_final.relacoes_temporais
    }
    prompt_call_3 = (
        f"{SYSTEM_PROMPT}\n\n"
        f"{PROCEDIMENTO_COMPLETO_AFC}\n\n"
        "FOCO DESTA CHAMADA: Execute APENAS as Etapas 5 e 6 do procedimento fornecido.\n"
        "Utilize os IDs dos nós e arestas existentes fornecidos no contexto abaixo. "
        "No seu JSON de saída, inclua APENAS as seguintes chaves do modelo RedeContingencialOutput: "
        "`relacoes_moduladoras_estado`, `hipoteses_analiticas`, e `evidencias_para_hipoteses`.\n\n"
        f"Contexto da análise anterior (use estes IDs para criar relações e hipóteses):\n```json\n{json.dumps(contexto_para_call_3, indent=2, ensure_ascii=False)}\n```\n\n"
        f"Texto narrativo original para análise (relembre se necessário):\n```\n{texto_narrativo}\n```"
    )
    logger.info("Iniciando Chamada 3 da API (Etapas 5 e 6)...")
    json_data_3 = _make_api_call(client, model_name, prompt_call_3, Step3Output)

    if not json_data_3:
        logger.error("Chamada 3 da API falhou ou retornou dados inválidos.")
        return rede_final # Retorna o que foi construído até agora

    try:
        for key in json_data_3:
            rede_final.__setattr__(key, rede_final.__getattribute__(key) + json_data_3[key])
        logger.info("Dados da Chamada 3 processados.")
    except ValidationError as e:
        logger.error(f"Erro de validação Pydantic na Chamada 3: {e.to_json(indent=2)}")
        logger.error(f"Dados JSON da Chamada 3 que falharam: {json.dumps(json_data_3, indent=2)}")
        return rede_final
    except KeyError as e:
        logger.error(f"Chave ausente nos dados JSON da Chamada 3: {e}")
        logger.error(f"Dados JSON da Chamada 3: {json.dumps(json_data_3, indent=2)}")
        return rede_final
    except TypeError as e:
        logger.error(f"Erro de tipo (provavelmente lista None) na Chamada 3: {e}")
        logger.error(f"Dados JSON da Chamada 3: {json.dumps(json_data_3, indent=2)}")
        return rede_final

    # Adiciona metadados simples ao final
    # rede_final.analise_metadados = {
    #     "modelo_utilizado": model_name,
    #     "data_analise_llm": datetime.datetime.now().isoformat(),
    #     "numero_chamadas_api": 3
    # }
    return json.loads(rede_final.model_dump_json())

def analisar(texto):
    return analisar_texto_para_rede_contingencial_client_api(texto)


# --- Exemplo de Uso (descomente para testar) ---
if __name__ == "__main__":
    # Certifique-se de ter sua GEMINI_API_KEY configurada no ambiente
    
    texto_exemplo = """
    João, um menino de 7 anos, estava na sala de aula. A professora pediu para todos fazerem a lição de matemática. 
    João olhou para a tarefa, que parecia difícil, e começou a choramingar. 
    A professora se aproximou e perguntou o que havia de errado. João disse que não conseguia fazer.
    A professora então sentou-se ao lado dele e explicou o primeiro exercício com calma. 
    Depois disso, João conseguiu fazer o resto da lição sozinho e sorriu quando terminou.
    Mais tarde, durante o recreio, João quis brincar com o carrinho que Pedro estava usando. 
    Pedro disse 'não'. João então empurrou Pedro, que largou o carrinho. João pegou o carrinho e começou a brincar.
    """
    
    print("Analisando o texto com a API genai.Client em múltiplas chamadas...")
    # Usando o modelo especificado pelo usuário no exemplo
    resultado_analise = analisar_texto_para_rede_contingencial_client_api(
        texto_narrativo=texto_exemplo,
        model_name="gemini-2.0-flash-exp" 
    )

    if resultado_analise:
        print("\n--- Análise da Rede Contingencial (JSON Final Agregado) ---")
        print(resultado_analise.model_dump_json(indent=2, exclude_none=True))
    else:
        print("\nA análise falhou ou não retornou dados válidos.")

