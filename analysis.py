# analysis_modular.py
from output_schemas import (
    RedeContingencialOutput,
    NoSujeito,
    NoAcaoComportamento,
    ArestaEmissaoComportamental,
    NoEstimuloEvento,
    ArestaRelacaoTemporal,
    ArestaRelacaoFuncionalAntecedente,
    ArestaRelacaoFuncionalConsequente,
    NoCondicaoEstado,
    ArestaRelacaoModuladoraEstado,
    NoHipoteseAnalitica,
    ArestaEvidenciaParaHipotese
)
from typing import List, Optional, Dict, Any, Type, Union, cast
from pydantic import BaseModel, Field, ValidationError
from google.genai import types as genai_types # Renomeado para evitar conflito
from dotenv import load_dotenv
from google import genai
import logging
import json
import os
import datetime
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Prompts (Mantidos do original, podem ser encurtados/seccionados para cada etapa no futuro) ---
SYSTEM_PROMPT = """
Você é um assistente especializado em Análise do Comportamento. Sua tarefa é aplicar um procedimento metodológico para extrair e estruturar informações de um texto narrativo ou descritivo, transformando-o em uma representação de rede contingencial.

Esta rede é composta por Nós (objetos da análise: Sujeitos, Estímulos_Evento, Acoes_Comportamento, Condicoes_Estado, Hipoteses_Analiticas) e Arestas (relações funcionais e temporais entre os nós).

Você receberá instruções para focar em etapas específicas do procedimento e gerar apenas as partes do JSON correspondentes a essas etapas. Use os IDs dos nós e arestas de forma consistente e incremental (S1, S2, E1, E2, AC1, AR1, etc.). Gere `data_formulacao` para Hipoteses_Analiticas com a data e hora atuais no formato ISO (YYYY-MM-DDTHH:MM:SS.ffffff).

Se um ID fornecido no contexto já existir e você estiver descrevendo o mesmo elemento, reutilize esse ID para indicar uma atualização. Se for um novo elemento, crie um novo ID.

Se informações cruciais não estiverem explícitas no texto, você pode fazer inferências cautelosas, mas deve indicar o nível de inferência ou a fonte da informação nos atributos apropriados. Se uma informação for ambígua, registre a ambiguidade.
Certifique-se de que o JSON de saída para cada chamada seja um objeto único contendo APENAS as listas de nós e arestas relevantes para as etapas solicitadas nessa chamada. O JSON deve começar com '{' e terminar com '}'. Não adicione nenhum texto explicativo antes ou depois do JSON.
"""

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

# --- Pydantic Schemas para Saídas de Etapas Específicas ---
# Estes modelos definem o que esperamos que a API retorne para cada etapa modular.

class BaseEtapa(BaseModel):
    raciocinio: str = Field(..., description='Reflita sobre o que precisará fazer para completar essa etapa, frente ao contexto atual. Então descreva passo a passo seu raciocínio para executar a etapa da forma mais completa.')

class OutputEtapaSujeitos(BaseEtapa):
    sujeitos: List[NoSujeito] = Field(default_factory=list)

class OutputEtapaAcoes(BaseEtapa):
    acoes_comportamentos: List[NoAcaoComportamento] = Field(default_factory=list)
    emissoes_comportamentais: List[ArestaEmissaoComportamental] = Field(default_factory=list)

class OutputEtapaEventosTemporais(BaseEtapa):
    estimulos_eventos: List[NoEstimuloEvento] = Field(default_factory=list)
    relacoes_temporais: List[ArestaRelacaoTemporal] = Field(default_factory=list)

class OutputEtapaFuncionaisAntecedentes(BaseEtapa):
    relacoes_funcionais_antecedentes: List[ArestaRelacaoFuncionalAntecedente] = Field(default_factory=list)
    # A API pode sugerir atualizações em nós existentes, mas a fusão é feita no Python
    estimulos_eventos_atualizados: Optional[List[NoEstimuloEvento]] = Field(default_factory=list)
    acoes_comportamentos_atualizados: Optional[List[NoAcaoComportamento]] = Field(default_factory=list)

class OutputEtapaFuncionaisConsequentes(BaseEtapa):
    relacoes_funcionais_consequentes: List[ArestaRelacaoFuncionalConsequente] = Field(default_factory=list)
    estimulos_eventos_atualizados: Optional[List[NoEstimuloEvento]] = Field(default_factory=list)
    acoes_comportamentos_atualizados: Optional[List[NoAcaoComportamento]] = Field(default_factory=list)

class OutputEtapaCondicoesEstado(BaseEtapa):
    condicoes_estados: List[NoCondicaoEstado] = Field(default_factory=list)

class OutputEtapaRelacoesModuladoras(BaseEtapa):
    relacoes_moduladoras_estado: List[ArestaRelacaoModuladoraEstado] = Field(default_factory=list)
    # A API pode sugerir atualizações em nós existentes
    condicoes_estados_atualizadas: Optional[List[NoCondicaoEstado]] = Field(default_factory=list)
    estimulos_eventos_atualizados: Optional[List[NoEstimuloEvento]] = Field(default_factory=list)
    acoes_comportamentos_atualizados: Optional[List[NoAcaoComportamento]] = Field(default_factory=list)

class OutputEtapaHipoteses(BaseEtapa):
    hipoteses_analiticas: List[NoHipoteseAnalitica] = Field(default_factory=list)
    evidencias_para_hipoteses: List[ArestaEvidenciaParaHipotese] = Field(default_factory=list)
    
class OutputEtapaTimeline(BaseEtapa):
    timeline: List[str] = Field(description='Lista das IDs de todos os Nós por ordem de aparição no texto narrativo.' ,default_factory=list)

# --- Funções Auxiliares ---

def _get_id(element: BaseModel) -> Optional[str]:
    """Retorna o valor do campo ID do elemento Pydantic, se existir."""
    for field_name in ["id_sujeito", "id_acao", "id_estimulo_evento", "id_condicao_estado", "id_hipotese", "id_aresta"]:
        if hasattr(element, field_name):
            return getattr(element, field_name)
    return None

def _merge_element_list(
    existing_elements: List[BaseModel],
    new_elements_data: Optional[List[Dict[str, Any]]],
    element_model: Type[BaseModel]
) -> List[BaseModel]:
    """
    Mescla uma lista de novos elementos (como dicts da API) em uma lista existente de elementos Pydantic.
    Atualiza elementos existentes pelo ID ou adiciona novos.
    """
    if new_elements_data is None:
        return existing_elements

    updated_elements = list(existing_elements) # Trabalha com uma cópia
    existing_ids_map = { _get_id(el): i for i, el in enumerate(updated_elements) if _get_id(el) is not None}

    for data in new_elements_data:
        try:
            new_element = element_model(**data)
            element_id = _get_id(new_element)

            if element_id is not None and element_id in existing_ids_map:
                # Atualiza o elemento existente
                index = existing_ids_map[element_id]
                updated_elements[index] = new_element
                logger.debug(f"Elemento '{element_id}' ({element_model.__name__}) atualizado.")
            elif element_id is not None:
                # Adiciona novo elemento se o ID não existir (ou se não tiver ID, apenas adiciona)
                updated_elements.append(new_element)
                existing_ids_map[element_id] = len(updated_elements) -1 # Atualiza o mapa
                logger.debug(f"Elemento '{element_id}' ({element_model.__name__}) adicionado.")
            else: # Elemento sem ID, apenas adiciona (menos comum para nós principais)
                updated_elements.append(new_element)
                logger.debug(f"Elemento sem ID ({element_model.__name__}) adicionado.")
        except ValidationError as e:
            logger.warning(f"Erro de validação ao processar {element_model.__name__} com dados {data}: {e}")
        except Exception as e:
            logger.error(f"Erro inesperado ao mesclar {element_model.__name__} com dados {data}: {e}")


    return updated_elements

def _make_api_call(
    client: genai.Client, # Alterado para usar o objeto modelo diretamente
    prompt_content: str,
    output_schema: Type[BaseModel]
) -> Optional[Dict[str, Any]]:
    """Função auxiliar para fazer uma chamada à API e processar a resposta com retries."""
    contents = [
        genai_types.Content(
            role="user",
            parts=[genai_types.Part.from_text(text=prompt_content)],
        ),
    ]

    generation_config = genai_types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=output_schema,
        temperature=0.2
    )

    retries = 0
    max_retries = 3
    success = False
    parsed_json = None

    while retries < max_retries and not success:
        logger.info(f"Tentativa {retries + 1}/{max_retries} de chamar o modelo Gemini. Schema: {output_schema.__name__}")
        logger.debug(f"Prompt para API (primeiros 500 chars): {prompt_content[:500]}...")

        full_response_text = ""
        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=cast(List[genai_types.Content], contents), # type: ignore
                config=generation_config,
            )
            if response.text:
                 full_response_text = response.text
            else:
                logger.error("Resposta da API não contém o texto esperado ou estrutura de candidatos.")
                retries += 1
                time.sleep(2 ** retries) # Exponential backoff
                continue # Try again

        except Exception as e_gc:
            logger.error(f"Falha ao chamar client.generate_content (Tentativa {retries + 1}): {e_gc}", exc_info=True)
            if hasattr(e_gc, 'response') and hasattr(e_gc.response, 'text'): # type: ignore
                logger.error(f"Detalhes da resposta da API (erro): {e_gc.response.text}") # type: ignore
            retries += 1
            time.sleep(2 ** retries) # Exponential backoff
            continue # Try again

        logger.info(f"Resposta recebida do modelo para {output_schema.__name__} (Tentativa {retries + 1}).")

        if not full_response_text:
            logger.error("Resposta do modelo está vazia.")
            retries += 1
            time.sleep(2 ** retries) # Exponential backoff
            continue # Try again

        # Limpeza do JSON (comum em respostas de LLMs)
        json_text = full_response_text.strip()
        if json_text.startswith("```json"):
            json_text = json_text[7:-3].strip()
        elif json_text.startswith("```"):
            json_text = json_text[3:-3].strip()

        logger.debug(f"Texto JSON bruto recebido para {output_schema.__name__}: {json_text[:500]}...")

        try:
            parsed_json = json.loads(json_text)
            # Valida com o schema Pydantic após o parse
            output_schema(**parsed_json)
            logger.info(f"Raciocínio da Etapa: {parsed_json.get('raciocinio', 'N/A')}")
            success = True # JSON parsed and validated successfully
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON para {output_schema.__name__} (Tentativa {retries + 1}): {e}. Resposta: {json_text}")
            retries += 1
            time.sleep(2 ** retries) # Exponential backoff
            # Continue loop to retry
        except ValidationError as e:
            logger.error(f"Erro de validação Pydantic para {output_schema.__name__} (Tentativa {retries + 1}): {e}. JSON: {json_text}")
            retries += 1
            time.sleep(2 ** retries) # Exponential backoff
            # Continue loop to retry
        except Exception as e:
             logger.error(f"Erro inesperado ao processar resposta da API (Tentativa {retries + 1}): {e}", exc_info=True)
             retries += 1
             time.sleep(2 ** retries) # Exponential backoff
             # Continue loop to retry


    if not success:
        logger.error(f"Falha final ao processar resposta da API para {output_schema.__name__} após {max_retries} tentativas.")
        return None

    return parsed_json

# --- Funções de Extração por Etapa ---

def extrair_sujeitos(
    texto_narrativo: str,
    rede_atual: RedeContingencialOutput,
    client_model: genai.Client,
) -> RedeContingencialOutput:
    logger.info("Iniciando Etapa 1: Extração de Sujeitos")
    foco_da_etapa = (
        "FOCO DESTA ETAPA: Identifique os sujeitos (indivíduos, animais) principais na narrativa. "
        "Para cada sujeito, gere um objeto com `id_sujeito` (S1, S2...) e `nome_descritivo`. "
        "Outros campos como `idade`, `historico_relevante` são opcionais com base no texto."
        "\nReferência no Procedimento: Etapa 1.1."
    )
    prompt = (
        f"{SYSTEM_PROMPT}\n\n{PROCEDIMENTO_COMPLETO_AFC}\n\n{foco_da_etapa}\n\n"
        f"Texto narrativo para análise:\n```\n{texto_narrativo}\n```\n\n"
        "Contexto da rede atual (sujeitos existentes para evitar duplicação de IDs se aplicável):\n"
        f"```json\n{json.dumps({'sujeitos': [s.model_dump(exclude_none=True) for s in rede_atual.sujeitos]}, indent=2)}\n```"
    )
    
    json_data = _make_api_call(client_model, prompt, OutputEtapaSujeitos)
    if json_data:
        try:
            novos_sujeitos_data = json_data.get("sujeitos")
            rede_atual.sujeitos = _merge_element_list(rede_atual.sujeitos, novos_sujeitos_data, NoSujeito)
            logger.info(f"Etapa 1 concluída. Sujeitos atuais: {len(rede_atual.sujeitos)}")
        except Exception as e:
            logger.error(f"Erro ao processar dados da Etapa 1: {e}", exc_info=True)
    return rede_atual

def extrair_acoes_comportamentos(
    texto_narrativo: str,
    rede_atual: RedeContingencialOutput,
    client_model: genai.Client,
) -> RedeContingencialOutput:
    logger.info("Iniciando Etapa 2: Extração de Ações e Emissões Comportamentais")
    foco_da_etapa = (
        "FOCO DESTA ETAPA: Para cada sujeito identificado no contexto, liste as principais ações ou comportamentos que eles emitem. "
        "Gere um Nó `Acao_Comportamento` para cada ação (com `id_acao` AC1, AC2..., `descricao_topografica`). "
        "Crie também uma Aresta `Emissao_Comportamental` (com `id_aresta` EM1, EM2...) ligando o `id_sujeito` (origem) ao `id_acao` (destino)."
        "\nReferência no Procedimento: Etapa 1.2."
    )
    contexto_json = {
        "sujeitos": [s.model_dump(exclude_none=True) for s in rede_atual.sujeitos],
        "acoes_comportamentos_existentes": [ac.model_dump(exclude_none=True) for ac in rede_atual.acoes_comportamentos],
        "emissoes_comportamentais_existentes": [em.model_dump(exclude_none=True) for em in rede_atual.emissoes_comportamentais]
    }
    prompt = (
        f"{SYSTEM_PROMPT}\n\n{PROCEDIMENTO_COMPLETO_AFC}\n\n{foco_da_etapa}\n\n"
        f"Texto narrativo para análise:\n```\n{texto_narrativo}\n```\n\n"
        "Contexto da rede atual:\n"
        f"```json\n{json.dumps(contexto_json, indent=2)}\n```"
    )

    json_data = _make_api_call(client_model, prompt, OutputEtapaAcoes)
    if json_data:
        try:
            novas_acoes_data = json_data.get("acoes_comportamentos")
            novas_emissoes_data = json_data.get("emissoes_comportamentais")
            
            rede_atual.acoes_comportamentos = _merge_element_list(rede_atual.acoes_comportamentos, novas_acoes_data, NoAcaoComportamento)
            rede_atual.emissoes_comportamentais = _merge_element_list(rede_atual.emissoes_comportamentais, novas_emissoes_data, ArestaEmissaoComportamental)
            logger.info(f"Etapa 2 concluída. Ações: {len(rede_atual.acoes_comportamentos)}, Emissões: {len(rede_atual.emissoes_comportamentais)}")
        except Exception as e:
            logger.error(f"Erro ao processar dados da Etapa 2: {e}", exc_info=True)
    return rede_atual

def extrair_eventos_ambientais_e_relacoes_temporais(
    texto_narrativo: str,
    rede_atual: RedeContingencialOutput,
    client_model: genai.Client,
) -> RedeContingencialOutput:
    logger.info("Iniciando Etapa 3: Extração de Eventos Ambientais e Relações Temporais")
    foco_da_etapa = (
        "FOCO DESTA ETAPA: Para cada `Acao_Comportamento` identificada no contexto, identifique `Estímulos_Evento` (E1, E2...) e outros `Acao_Comportamento` que *precedem* (antecedentes) e que *procedem* (consequentes) a tal `Acao_Comportamento`. "
        "Nenhum `Acao_Comportamento` deve ser deixado sem pelo menos um `Estímulos_Evento` antecedente e um consequente. Busque associá-los primeiro com os nós, mas caso não sejam suficientes extraia ou deduza novos."
        "Comece descrevendo `Estímulos_Evento` antecedentes e consequentes para cada `Acao_Comportamento`. A seguir, crie `ArestasRelacaoTemporal` (RT1, RT2...) indicando se o estímulo `PRECEDE_IMEDIATAMENTE` a ação ou se a ação `SUCEDE_IMEDIATAMENTE` o estímulo. "
        "Use os IDs das ações do contexto."
        "\nReferência no Procedimento: Etapas 2.1 e 2.2."
    )
    contexto_json = {
        "acoes_comportamentos": [ac.model_dump(exclude_none=True) for ac in rede_atual.acoes_comportamentos],
        "estimulos_eventos_existentes": [e.model_dump(exclude_none=True) for e in rede_atual.estimulos_eventos],
        "relacoes_temporais_existentes": [rt.model_dump(exclude_none=True) for rt in rede_atual.relacoes_temporais]
    }
    prompt = (
        f"{SYSTEM_PROMPT}\n\n{PROCEDIMENTO_COMPLETO_AFC}\n\n{foco_da_etapa}\n\n"
        f"Texto narrativo para análise:\n```\n{texto_narrativo}\n```\n\n"
        "Contexto da rede atual:\n"
        f"```json\n{json.dumps(contexto_json, indent=2)}\n```"
    )
    
    json_data = _make_api_call(client_model, prompt, OutputEtapaEventosTemporais)
    if json_data:
        try:
            novos_estimulos_data = json_data.get("estimulos_eventos")
            novas_rel_temporais_data = json_data.get("relacoes_temporais")

            rede_atual.estimulos_eventos = _merge_element_list(rede_atual.estimulos_eventos, novos_estimulos_data, NoEstimuloEvento)
            rede_atual.relacoes_temporais = _merge_element_list(rede_atual.relacoes_temporais, novas_rel_temporais_data, ArestaRelacaoTemporal)
            logger.info(f"Etapa 3 concluída. Estímulos: {len(rede_atual.estimulos_eventos)}, Relações Temporais: {len(rede_atual.relacoes_temporais)}")
        except Exception as e:
            logger.error(f"Erro ao processar dados da Etapa 3: {e}", exc_info=True)
    return rede_atual

def inferir_relacoes_funcionais_antecedentes(
    texto_narrativo: str,
    rede_atual: RedeContingencialOutput,
    client_model: genai.Client,
) -> RedeContingencialOutput:
    logger.info("Iniciando Etapa 4: Inferência de Relações Funcionais Antecedentes")
    foco_da_etapa = (
        "FOCO DESTA ETAPA: Considerando os `Estímulos_Evento` que, de acordo com as `Relacoes_Temporais`, precedem imediatamente as `Acoes_Comportamento` (ambos fornecidos no contexto), "
        "infira a `funcao_antecedente` (e.g., ESTÍMULO_DISCRIMINATIVO_SD, ESTÍMULO_ELICIADOR_CONDICIONADO_CS) de cada estímulo em relação à ação que ele precede. "
        "Crie `ArestasRelacaoFuncionalAntecedente` (RFA1, RFA2...). Use os IDs dos estímulos e ações do contexto."
        "\nReferência no Procedimento: Etapa 3.1 (parte antecedente)."
    )
    # Filtrar estímulos que são antecedentes e ações relacionadas
    antecedentes_ids = set()
    acoes_pos_antecedente_ids = set()
    for rt in rede_atual.relacoes_temporais:
        if rt.tipo_temporalidade.value == "PRECEDE_IMEDIATAMENTE": # type: ignore
            antecedentes_ids.add(rt.id_origem_no)
            acoes_pos_antecedente_ids.add(rt.id_destino_no)

    contexto_json = {
        "estimulos_eventos_relevantes": [e.model_dump(exclude_none=True) for e in rede_atual.estimulos_eventos if _get_id(e) in antecedentes_ids],
        "acoes_comportamentos_relevantes": [ac.model_dump(exclude_none=True) for ac in rede_atual.acoes_comportamentos if _get_id(ac) in acoes_pos_antecedente_ids],
        "relacoes_temporais_relevantes": [rt.model_dump(exclude_none=True) for rt in rede_atual.relacoes_temporais if rt.tipo_temporalidade.value == "PRECEDE_IMEDIATAMENTE"], # type: ignore
        "relacoes_funcionais_antecedentes_existentes": [rfa.model_dump(exclude_none=True) for rfa in rede_atual.relacoes_funcionais_antecedentes]
    }
    prompt = (
        f"{SYSTEM_PROMPT}\n\n{PROCEDIMENTO_COMPLETO_AFC}\n\n{foco_da_etapa}\n\n"
        f"Texto narrativo para análise:\n```\n{texto_narrativo}\n```\n\n"
        "Contexto da rede atual (elementos relevantes para esta etapa):\n"
        f"```json\n{json.dumps(contexto_json, indent=2)}\n```"
    )

    json_data = _make_api_call(client_model, prompt, OutputEtapaFuncionaisAntecedentes)
    if json_data:
        try:
            novas_rfa_data = json_data.get("relacoes_funcionais_antecedentes")
            rede_atual.relacoes_funcionais_antecedentes = _merge_element_list(rede_atual.relacoes_funcionais_antecedentes, novas_rfa_data, ArestaRelacaoFuncionalAntecedente)
            
            # Opcional: atualizar nós se a API os retornou com modificações
            estimulos_atualizados_data = json_data.get("estimulos_eventos_atualizados")
            if estimulos_atualizados_data:
                rede_atual.estimulos_eventos = _merge_element_list(rede_atual.estimulos_eventos, estimulos_atualizados_data, NoEstimuloEvento)
            
            acoes_atualizadas_data = json_data.get("acoes_comportamentos_atualizados")
            if acoes_atualizadas_data:
                rede_atual.acoes_comportamentos = _merge_element_list(rede_atual.acoes_comportamentos, acoes_atualizadas_data, NoAcaoComportamento)

            logger.info(f"Etapa 4 concluída. Relações Funcionais Antecedentes: {len(rede_atual.relacoes_funcionais_antecedentes)}")
        except Exception as e:
            logger.error(f"Erro ao processar dados da Etapa 4: {e}", exc_info=True)
    return rede_atual

def inferir_relacoes_funcionais_consequentes(
    texto_narrativo: str,
    rede_atual: RedeContingencialOutput,
    client_model: genai.Client,
) -> RedeContingencialOutput:
    logger.info("Iniciando Etapa 5: Inferência de Relações Funcionais Consequentes")
    foco_da_etapa = (
        "FOCO DESTA ETAPA: Considerando as `Acoes_Comportamento` e os `Estímulos_Evento` que, de acordo com as `Relacoes_Temporais`, as sucedem imediatamente (ambos fornecidos no contexto), "
        "infira a `funcao_consequente` (e.g., REFORÇO_POSITIVO_SR+, PUNIÇÃO_NEGATIVA_SP-) de cada estímulo em relação à ação que ele sucede. "
        "Crie `ArestasRelacaoFuncionalConsequente` (RFC1, RFC2...). Use os IDs das ações e estímulos do contexto."
        "\nReferência no Procedimento: Etapa 3.1 (parte consequente)."
    )
    
    consequentes_ids = set()
    acoes_pre_consequente_ids = set()
    for rt in rede_atual.relacoes_temporais:
        if rt.tipo_temporalidade.value == "SUCEDE_IMEDIATAMENTE": # type: ignore
            acoes_pre_consequente_ids.add(rt.id_origem_no)
            consequentes_ids.add(rt.id_destino_no)

    contexto_json = {
        "acoes_comportamentos_relevantes": [ac.model_dump(exclude_none=True) for ac in rede_atual.acoes_comportamentos if _get_id(ac) in acoes_pre_consequente_ids],
        "estimulos_eventos_relevantes": [e.model_dump(exclude_none=True) for e in rede_atual.estimulos_eventos if _get_id(e) in consequentes_ids],
        "relacoes_temporais_relevantes": [rt.model_dump(exclude_none=True) for rt in rede_atual.relacoes_temporais if rt.tipo_temporalidade.value == "SUCEDE_IMEDIATAMENTE"], # type: ignore
        "relacoes_funcionais_consequentes_existentes": [rfc.model_dump(exclude_none=True) for rfc in rede_atual.relacoes_funcionais_consequentes]
    }
    prompt = (
        f"{SYSTEM_PROMPT}\n\n{PROCEDIMENTO_COMPLETO_AFC}\n\n{foco_da_etapa}\n\n"
        f"Texto narrativo para análise:\n```\n{texto_narrativo}\n```\n\n"
        "Contexto da rede atual (elementos relevantes para esta etapa):\n"
        f"```json\n{json.dumps(contexto_json, indent=2)}\n```"
    )

    json_data = _make_api_call(client_model, prompt, OutputEtapaFuncionaisConsequentes)
    if json_data:
        try:
            novas_rfc_data = json_data.get("relacoes_funcionais_consequentes")
            rede_atual.relacoes_funcionais_consequentes = _merge_element_list(rede_atual.relacoes_funcionais_consequentes, novas_rfc_data, ArestaRelacaoFuncionalConsequente)

            estimulos_atualizados_data = json_data.get("estimulos_eventos_atualizados")
            if estimulos_atualizados_data:
                rede_atual.estimulos_eventos = _merge_element_list(rede_atual.estimulos_eventos, estimulos_atualizados_data, NoEstimuloEvento)
            
            acoes_atualizadas_data = json_data.get("acoes_comportamentos_atualizados")
            if acoes_atualizadas_data:
                rede_atual.acoes_comportamentos = _merge_element_list(rede_atual.acoes_comportamentos, acoes_atualizadas_data, NoAcaoComportamento)

            logger.info(f"Etapa 5 concluída. Relações Funcionais Consequentes: {len(rede_atual.relacoes_funcionais_consequentes)}")
        except Exception as e:
            logger.error(f"Erro ao processar dados da Etapa 5: {e}", exc_info=True)
    return rede_atual

def identificar_condicoes_estado(
    texto_narrativo: str,
    rede_atual: RedeContingencialOutput,
    client_model: genai.Client,
) -> RedeContingencialOutput:
    logger.info("Iniciando Etapa 6: Identificação de Condições/Estado")
    foco_da_etapa = (
        "FOCO DESTA ETAPA: Identifique `Condicoes_Estado` (CE1, CE2...) descritas na narrativa que podem estar influenciando os comportamentos e suas relações com antecedentes e consequentes. "
        "Classifique-as conforme o `tipo_condicao` (e.g., OPERACAO_MOTIVADORA, CONTEXTO_AMBIENTAL_GERAL, ESTADO_FISIOLOGICO). "
        "Forneça `id_condicao_estado`, `descricao` e `tipo_condicao`."
        "\nReferência no Procedimento: Etapa 4."
    )
    contexto_json = {
        "rede_parcial_existente_para_contexto": {
            "sujeitos": [s.model_dump(exclude_none=True) for s in rede_atual.sujeitos],
            "acoes_comportamentos": [ac.model_dump(exclude_none=True) for ac in rede_atual.acoes_comportamentos],
            "estimulos_eventos": [e.model_dump(exclude_none=True) for e in rede_atual.estimulos_eventos],
            "relacoes_funcionais_antecedentes": [rfa.model_dump(exclude_none=True) for rfa in rede_atual.relacoes_funcionais_antecedentes],
            "relacoes_funcionais_consequentes": [rfc.model_dump(exclude_none=True) for rfc in rede_atual.relacoes_funcionais_consequentes],
        },
        "condicoes_estados_existentes": [ce.model_dump(exclude_none=True) for ce in rede_atual.condicoes_estados]
    }
    prompt = (
        f"{SYSTEM_PROMPT}\n\n{PROCEDIMENTO_COMPLETO_AFC}\n\n{foco_da_etapa}\n\n"
        f"Texto narrativo para análise:\n```\n{texto_narrativo}\n```\n\n"
        "Contexto da rede atual (para identificar contextos que afetam as contingências já delineadas):\n"
        f"```json\n{json.dumps(contexto_json, indent=2)}\n```"
    )

    json_data = _make_api_call(client_model, prompt, OutputEtapaCondicoesEstado)
    if json_data:
        try:
            novas_ce_data = json_data.get("condicoes_estados")
            rede_atual.condicoes_estados = _merge_element_list(rede_atual.condicoes_estados, novas_ce_data, NoCondicaoEstado)
            logger.info(f"Etapa 6 concluída. Condições/Estado: {len(rede_atual.condicoes_estados)}")
        except Exception as e:
            logger.error(f"Erro ao processar dados da Etapa 6: {e}", exc_info=True)
    return rede_atual

def estabelecer_relacoes_moduladoras_estado(
    texto_narrativo: str,
    rede_atual: RedeContingencialOutput,
    client_model: genai.Client,
) -> RedeContingencialOutput:
    logger.info("Iniciando Etapa 7: Estabelecimento de Relações Moduladoras de Estado")
    foco_da_etapa = (
        "FOCO DESTA ETAPA: Para cada `Condicao_Estado` identificada no contexto (IDs: [CE1, CE2...]), determine como ela modula a rede. "
        "Ela altera o valor de um `Estímulo_Evento` consequente (referência `alvo_da_modulacao_valor_ref_id_estimulo`)? "
        "Ela altera a frequência de uma `Acao_Comportamento` (referência `alvo_da_modulacao_frequencia_ref_id_acao`)? "
        "Descreva o `tipo_modulacao_estado` e crie `ArestasRelacaoModuladoraEstado` (RME1, RME2...). "
        "Use os IDs dos elementos do contexto."
        "\nReferência no Procedimento: Etapa 5.3."
    )
    contexto_json = {
        "condicoes_estados": [ce.model_dump(exclude_none=True) for ce in rede_atual.condicoes_estados],
        "estimulos_eventos": [e.model_dump(exclude_none=True) for e in rede_atual.estimulos_eventos], # Especialmente consequentes
        "acoes_comportamentos": [ac.model_dump(exclude_none=True) for ac in rede_atual.acoes_comportamentos],
        "relacoes_funcionais_consequentes": [rfc.model_dump(exclude_none=True) for rfc in rede_atual.relacoes_funcionais_consequentes], # Para saber o que é reforçador/punitivo
        "relacoes_moduladoras_estado_existentes": [rme.model_dump(exclude_none=True) for rme in rede_atual.relacoes_moduladoras_estado]
    }
    prompt = (
        f"{SYSTEM_PROMPT}\n\n{PROCEDIMENTO_COMPLETO_AFC}\n\n{foco_da_etapa}\n\n"
        f"Texto narrativo para análise:\n```\n{texto_narrativo}\n```\n\n"
        "Contexto da rede atual:\n"
        f"```json\n{json.dumps(contexto_json, indent=2)}\n```"
    )

    json_data = _make_api_call(client_model, prompt, OutputEtapaRelacoesModuladoras)
    if json_data:
        try:
            novas_rme_data = json_data.get("relacoes_moduladoras_estado")
            rede_atual.relacoes_moduladoras_estado = _merge_element_list(rede_atual.relacoes_moduladoras_estado, novas_rme_data, ArestaRelacaoModuladoraEstado)
            
            # Opcional: atualizar nós se a API os retornou com modificações
            condicoes_atualizadas_data = json_data.get("condicoes_estados_atualizadas")
            if condicoes_atualizadas_data:
                 rede_atual.condicoes_estados = _merge_element_list(rede_atual.condicoes_estados, condicoes_atualizadas_data, NoCondicaoEstado)
            
            estimulos_atualizados_data = json_data.get("estimulos_eventos_atualizados")
            if estimulos_atualizados_data:
                rede_atual.estimulos_eventos = _merge_element_list(rede_atual.estimulos_eventos, estimulos_atualizados_data, NoEstimuloEvento)

            acoes_atualizadas_data = json_data.get("acoes_comportamentos_atualizados")
            if acoes_atualizadas_data:
                rede_atual.acoes_comportamentos = _merge_element_list(rede_atual.acoes_comportamentos, acoes_atualizadas_data, NoAcaoComportamento)

            logger.info(f"Etapa 7 concluída. Relações Moduladoras: {len(rede_atual.relacoes_moduladoras_estado)}")
        except Exception as e:
            logger.error(f"Erro ao processar dados da Etapa 7: {e}", exc_info=True)
    return rede_atual

def formular_hipoteses_analiticas_e_evidencias(
    texto_narrativo: str,
    rede_atual: RedeContingencialOutput,
    client_model: genai.Client,
) -> RedeContingencialOutput:
    logger.info("Iniciando Etapa 8: Formulação de Hipóteses Analíticas e Evidências")
    foco_da_etapa = (
        "FOCO DESTA ETAPA: Com base na análise completa da rede fornecida no contexto, formule `Hipoteses_Analiticas` (H1, H2...) sobre as principais funções dos comportamentos identificados. "
        "Para cada hipótese, forneça `id_hipotese`, `descricao_hipotese`, `nivel_confianca` e `data_formulacao` (use a data e hora atuais no formato ISO: YYYY-MM-DDTHH:MM:SS.ffffff). "
        "Crie também uma `ArestaEvidenciaParaHipotese` (EH1, EH2...) que a ligue ao `Acao_Comportamento` central da hipótese (origem da aresta = ID da Ação) e à Hipótese (destino da aresta = ID da Hipótese). "
        "Liste os `ids_elementos_contingencia_suporte` (outros nós e arestas da rede que evidenciam essa hipótese)."
        "\nReferência no Procedimento: Etapa 6."
    )
    # Gerar data_formulacao no momento da chamada
    data_formulacao_atual = datetime.datetime.now().isoformat()
    
    contexto_json = {
        "rede_completa_existente": rede_atual.model_dump(exclude_none=True), # Passa a rede toda
        "data_para_formulacao_hipotese": data_formulacao_atual,
        "hipoteses_existentes": [h.model_dump(exclude_none=True) for h in rede_atual.hipoteses_analiticas],
        "evidencias_existentes": [ev.model_dump(exclude_none=True) for ev in rede_atual.evidencias_para_hipoteses]

    }
    prompt = (
        f"{SYSTEM_PROMPT}\n\n{PROCEDIMENTO_COMPLETO_AFC}\n\n{foco_da_etapa}\n\n"
        f"Texto narrativo para análise:\n```\n{texto_narrativo}\n```\n\n"
        f"Data atual para `data_formulacao` das hipóteses: {data_formulacao_atual}\n\n"
        "Contexto da rede atual (rede completa para embasar as hipóteses):\n"
        f"```json\n{json.dumps(contexto_json, indent=2)}\n```"
    )

    json_data = _make_api_call(client_model, prompt, OutputEtapaHipoteses)
    if json_data:
        try:
            novas_hipoteses_data = json_data.get("hipoteses_analiticas")
            # Assegurar que data_formulacao está correta se a API não a preencheu ou preencheu errado
            if novas_hipoteses_data:
                for h_data in novas_hipoteses_data:
                    if not h_data.get("data_formulacao"):
                        h_data["data_formulacao"] = data_formulacao_atual
            
            novas_evidencias_data = json_data.get("evidencias_para_hipoteses")

            rede_atual.hipoteses_analiticas = _merge_element_list(rede_atual.hipoteses_analiticas, novas_hipoteses_data, NoHipoteseAnalitica)
            rede_atual.evidencias_para_hipoteses = _merge_element_list(rede_atual.evidencias_para_hipoteses, novas_evidencias_data, ArestaEvidenciaParaHipotese)
            logger.info(f"Etapa 8 concluída. Hipóteses: {len(rede_atual.hipoteses_analiticas)}, Evidências: {len(rede_atual.evidencias_para_hipoteses)}")
        except Exception as e:
            logger.error(f"Erro ao processar dados da Etapa 8: {e}", exc_info=True)
    return rede_atual

def ordenar_timeline(
    texto_narrativo: str,
    rede_atual: RedeContingencialOutput,
    client_model: genai.Client,
) -> RedeContingencialOutput:
    logger.info("Iniciando Etapa 9: Ordenação da Timeline")
    foco_da_etapa = (
        "FOCO DESTA ETAPA: Ordenar todos os Nós da rede de acordo com sua aparição no texto narrativo."
        "Cada nó deve ser identificado pelo seu ID e aparecer na lista apenas uma vez."
        "Todos os nós devem estar na lista final."
    )
    contexto_json = {
        "sujeitos" : [s.model_dump(exclude_none=True) for s in rede_atual.sujeitos],
        "acoes_comportamentos" : [ac.model_dump(exclude_none=True) for ac in rede_atual.acoes_comportamentos],
        "estimulos_eventos" : [e.model_dump(exclude_none=True) for e in rede_atual.estimulos_eventos],
    }
    prompt = (
        f"{SYSTEM_PROMPT}\n\n{PROCEDIMENTO_COMPLETO_AFC}\n\n{foco_da_etapa}\n\n"
        f"Texto narrativo para análise:\n```\n{texto_narrativo}\n```\n\n"
        "Contexto da rede atual:\n"
        f"```json\n{json.dumps(contexto_json, indent=2)}\n```"
    )

    json_data = _make_api_call(client_model, prompt, OutputEtapaTimeline)
    if json_data:
        try:
            timeline_data = json_data.get("timeline")
            if timeline_data is not None:
                # Assuming timeline_data is already a list of IDs (int or str)
                rede_atual.timeline = [str(item) for item in timeline_data] # Ensure all IDs are strings for consistency
            logger.info(f"Etapa 9 concluída. Nós na timeline: {len(rede_atual.timeline)}")
        except Exception as e:
            logger.error(f"Erro ao processar dados da Etapa 9: {e}", exc_info=True)
            logger.error(f"Resposta do modelo: {json_data}")
    return rede_atual

# --- Função Orquestradora Principal ---

def analisar(
    texto_narrativo: str,
    debug: bool = False
) -> Optional[Dict[str, Any]]:
    
    load_dotenv()
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("Variável de ambiente GEMINI_API_KEY não encontrada.")
        print("Erro: Chave da API Gemini não configurada na variável de ambiente GEMINI_API_KEY.")
        return None

    try:
        client_model = genai.Client(api_key=api_key) # Modelo é instanciado aqui
    except Exception as e:
        logger.error(f"Falha ao inicializar o modelo Gemini: {e}", exc_info=True)
        print(f"Erro ao inicializar o modelo Gemini: {e}")
        return None

    rede_final = RedeContingencialOutput()
    
    # Sequência de execução das etapas modulares
    etapas_de_extracao = [
        extrair_sujeitos,
        extrair_acoes_comportamentos,
        extrair_eventos_ambientais_e_relacoes_temporais,
        inferir_relacoes_funcionais_antecedentes,
        inferir_relacoes_funcionais_consequentes,
        #identificar_condicoes_estado,
        #estabelecer_relacoes_moduladoras_estado,
        formular_hipoteses_analiticas_e_evidencias,
        ordenar_timeline
    ]

    for i, etapa_func in enumerate(etapas_de_extracao):
        logger.info(f"--- Iniciando processamento da Etapa {i+1}: {etapa_func.__name__} ---")
        try:
            rede_final = etapa_func(texto_narrativo, rede_final, client_model) # Passa client_model
            logger.debug(f"Rede após Etapa {i+1} ({etapa_func.__name__}):\n{rede_final.model_dump_json(indent=2, exclude_none=True)}")
        except Exception as e:
            logger.error(f"Erro durante a execução da etapa {etapa_func.__name__}: {e}", exc_info=True)
            # Decide se quer parar ou continuar em caso de erro em uma etapa
            # Por enquanto, continua para tentar obter o máximo possível
    
    logger.info("Todas as etapas de extração foram processadas.")
    return json.loads(rede_final.model_dump_json(exclude_none=True))

# --- Exemplo de Uso ---
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Analisa um texto narrativo e gera uma rede contingencial em JSON.")
    parser.add_argument("input_filepath", help="Caminho para o arquivo de texto de entrada.")
    parser.add_argument("output_filepath", help="Caminho para salvar o arquivo JSON de saída.")
    parser.add_argument("--debug", action="store_true", help="Ativa o logging de debug.")

    args = parser.parse_args()

    try:
        with open(args.input_filepath, "r", encoding="utf-8") as f:
            texto_para_analise = f.read()
    except FileNotFoundError:
        print(f"Erro: Arquivo de entrada não encontrado em {args.input_filepath}")
        exit(1)
    except Exception as e:
        print(f"Erro ao ler o arquivo de entrada: {e}")
        exit(1)
    
    resultado_analise_modular = analisar(
        texto_narrativo=texto_para_analise,
        debug=args.debug 
    )

    if resultado_analise_modular:
        print(f"\n--- Análise da Rede Contingencial (JSON Final Agregado Modular para {args.input_filepath}) ---")
        # O resultado já é um dict
        resultado_analise_modular['texto_original'] = texto_para_analise
        output_json_string = json.dumps(resultado_analise_modular, indent=2, ensure_ascii=False)
        print(output_json_string) # Imprime no stdout também
        
        # Salvar em arquivo para inspeção
        try:
            # Garante que o diretório de saída exista
            os.makedirs(os.path.dirname(args.output_filepath), exist_ok=True)
            with open(args.output_filepath, "w", encoding="utf-8") as f:
                f.write(output_json_string)
            print(f"\nResultado salvo em: {args.output_filepath}")
        except Exception as e:
            print(f"Erro ao salvar o arquivo de saída: {e}")
            exit(1)
    else:
        print(f"\nA análise modular para {args.input_filepath} falhou ou não retornou dados válidos.")
