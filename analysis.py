# analysis_modular.py
from output_schemas import RedeContingencialOutput
from typing import List, Optional, Dict, Any, Type, Union, cast, Callable
from dotenv import load_dotenv
from google import genai
import logging
import json
import os
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
logger = logging.getLogger(__name__)

from prompt import (
    SYSTEM_PROMPT,
    PROCEDIMENTO_COMPLETO_AFC,
    FOCO_ETAPA_SUJEITOS,
    FOCO_ETAPA_ACOES,
    FOCO_ETAPA_EVENTOS_TEMPORAIS,
    FOCO_ETAPA_FUNCIONAIS_ANTECEDENTES,
    FOCO_ETAPA_FUNCIONAIS_CONSEQUENTES,
    FOCO_ETAPA_CONDICOES_ESTADO,
    FOCO_ETAPA_RELACOES_MODULADORAS,
    FOCO_ETAPA_HIPOTESES,
    FOCO_ETAPA_TIMELINE
)
from output_schemas import (
    OutputEtapaSujeitos,
    OutputEtapaAcoes,
    OutputEtapaEventosTemporais,
    OutputEtapaFuncionaisAntecedentes,
    OutputEtapaFuncionaisConsequentes,
    OutputEtapaCondicoesEstado,
    OutputEtapaRelacoesModuladoras,
    OutputEtapaHipoteses,
    OutputEtapaTimeline,
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

from utils import _get_id, _merge_element_list
from llm_inference import _make_api_call

def _processar_etapa(
    texto_narrativo: str,
    rede_atual: RedeContingencialOutput,
    client_model: genai.Client, # Type hint kept as genai.Client for now
    foco_etapa: str,
    output_schema: Type[Union[
        OutputEtapaSujeitos,
        OutputEtapaAcoes,
        OutputEtapaEventosTemporais,
        OutputEtapaFuncionaisAntecedentes,
        OutputEtapaFuncionaisConsequentes,
        OutputEtapaCondicoesEstado,
        OutputEtapaRelacoesModuladoras,
        OutputEtapaHipoteses,
        OutputEtapaTimeline
    ]],
    context_builder_func: callable,
    update_rede_func: callable, # Will now return a string
    etapa_name: str,
) -> RedeContingencialOutput:
    logger.info(f"Iniciando Etapa: {etapa_name}")

    contexto_json = context_builder_func(rede_atual)

    # Corrected prompt to use
    prompt = (
        f"{SYSTEM_PROMPT}\n\n{PROCEDIMENTO_COMPLETO_AFC}\n\n{foco_etapa}\n\n"
        f"Texto narrativo para análise:\n```\n{texto_narrativo}\n```\n\n"
        "Contexto da rede atual (elementos relevantes para esta etapa):\n"
        f"```json\n{json.dumps(contexto_json, indent=2)}\n```"
    )
    
    json_data = _make_api_call(client_model, prompt, output_schema) # type: ignore

    if json_data:
        try:
            log_details = update_rede_func(rede_atual, json_data) # update_rede_func returns string
            logger.info(f"Etapa {etapa_name} concluída. {log_details}") # Use returned string
        except Exception as e:
            logger.error(f"Erro ao processar dados da Etapa {etapa_name}: {e}", exc_info=True)
            if isinstance(json_data, dict) and json_data.get("error_details"):
                 logger.error(f"Detalhes do erro da API: {json_data['error_details']}")
    return rede_atual

# --- Funções de Extração por Etapa ---

def extrair_sujeitos(
    texto_narrativo: str,
    rede_atual: RedeContingencialOutput,
    client_model: genai.Client, # Type hint kept as genai.Client for now
) -> RedeContingencialOutput:
    def context_builder_func(rede: RedeContingencialOutput) -> dict:
        return {'sujeitos': [s.model_dump(exclude_none=True) for s in rede.sujeitos]}

    def update_rede_func(rede: RedeContingencialOutput, json_data: dict) -> str: # Returns string for log
        novos_sujeitos_data = json_data.get("sujeitos")
        if novos_sujeitos_data is None:
            novos_sujeitos_data = []
        rede.sujeitos = _merge_element_list(rede.sujeitos, novos_sujeitos_data, NoSujeito)
        return f"Sujeitos atuais: {len(rede.sujeitos)}"

    return _processar_etapa(
        texto_narrativo=texto_narrativo,
        rede_atual=rede_atual,
        client_model=client_model,
        foco_etapa=FOCO_ETAPA_SUJEITOS,
        output_schema=OutputEtapaSujeitos,
        context_builder_func=context_builder_func,
        update_rede_func=update_rede_func,
        etapa_name="Extração de Sujeitos"
    )

def extrair_acoes_comportamentos(
    texto_narrativo: str,
    rede_atual: RedeContingencialOutput,
    client_model: genai.Client, # Type hint kept as genai.Client for now
) -> RedeContingencialOutput:
    def context_builder_func(rede: RedeContingencialOutput) -> dict:
        return {
            "sujeitos": [s.model_dump(exclude_none=True) for s in rede.sujeitos],
            "acoes_comportamentos_existentes": [ac.model_dump(exclude_none=True) for ac in rede.acoes_comportamentos],
            "emissoes_comportamentais_existentes": [em.model_dump(exclude_none=True) for em in rede.emissoes_comportamentais]
        }

    def update_rede_func(rede: RedeContingencialOutput, json_data: dict) -> str: # Returns string for log
        novas_acoes_data = json_data.get("acoes_comportamentos")
        novas_emissoes_data = json_data.get("emissoes_comportamentais")

        if novas_acoes_data is None:
            novas_acoes_data = []
        if novas_emissoes_data is None:
            novas_emissoes_data = []
            
        rede.acoes_comportamentos = _merge_element_list(rede.acoes_comportamentos, novas_acoes_data, NoAcaoComportamento)
        rede.emissoes_comportamentais = _merge_element_list(rede.emissoes_comportamentais, novas_emissoes_data, ArestaEmissaoComportamental)

        return f"Ações: {len(rede.acoes_comportamentos)}, Emissões: {len(rede.emissoes_comportamentais)}"

    return _processar_etapa(
        texto_narrativo=texto_narrativo,
        rede_atual=rede_atual,
        client_model=client_model,
        foco_etapa=FOCO_ETAPA_ACOES,
        output_schema=OutputEtapaAcoes,
        context_builder_func=context_builder_func,
        update_rede_func=update_rede_func,
        etapa_name="Extração de Ações e Emissões Comportamentais"
    )

def extrair_eventos_ambientais_e_relacoes_temporais(
    texto_narrativo: str,
    rede_atual: RedeContingencialOutput,
    client_model: genai.Client, # Type hint kept as genai.Client for now
) -> RedeContingencialOutput:
    def context_builder_func(rede: RedeContingencialOutput) -> dict:
        return {
            "acoes_comportamentos": [ac.model_dump(exclude_none=True) for ac in rede.acoes_comportamentos],
            "estimulos_eventos_existentes": [e.model_dump(exclude_none=True) for e in rede.estimulos_eventos],
            "relacoes_temporais_existentes": [rt.model_dump(exclude_none=True) for rt in rede.relacoes_temporais]
        }

    def update_rede_func(rede: RedeContingencialOutput, json_data: dict) -> str: # Returns string for log
        novos_estimulos_data = json_data.get("estimulos_eventos")
        novas_rel_temporais_data = json_data.get("relacoes_temporais")

        if novos_estimulos_data is None:
            novos_estimulos_data = []
        if novas_rel_temporais_data is None:
            novas_rel_temporais_data = []

        rede.estimulos_eventos = _merge_element_list(rede.estimulos_eventos, novos_estimulos_data, NoEstimuloEvento)
        rede.relacoes_temporais = _merge_element_list(rede.relacoes_temporais, novas_rel_temporais_data, ArestaRelacaoTemporal)

        return f"Estímulos: {len(rede.estimulos_eventos)}, Relações Temporais: {len(rede.relacoes_temporais)}"

    return _processar_etapa(
        texto_narrativo=texto_narrativo,
        rede_atual=rede_atual,
        client_model=client_model,
        foco_etapa=FOCO_ETAPA_EVENTOS_TEMPORAIS,
        output_schema=OutputEtapaEventosTemporais,
        context_builder_func=context_builder_func,
        update_rede_func=update_rede_func,
        etapa_name="Extração de Eventos Ambientais e Relações Temporais" # Original log started with "Iniciando:", name matches previous "Etapa concluída."
    )

def inferir_relacoes_funcionais_antecedentes(
    texto_narrativo: str,
    rede_atual: RedeContingencialOutput,
    client_model: genai.Client, # Type hint kept as genai.Client for now
) -> RedeContingencialOutput:
    def context_builder_func(rede: RedeContingencialOutput) -> dict:
        antecedentes_ids = set()
        acoes_pos_antecedente_ids = set()
        for rt in rede.relacoes_temporais:
            if rt.tipo_temporalidade.value == "PRECEDE_IMEDIATAMENTE": # type: ignore
                antecedentes_ids.add(rt.id_origem_no)
                acoes_pos_antecedente_ids.add(rt.id_destino_no)

        return {
            "estimulos_eventos_relevantes": [e.model_dump(exclude_none=True) for e in rede.estimulos_eventos if _get_id(e) in antecedentes_ids],
            "acoes_comportamentos_relevantes": [ac.model_dump(exclude_none=True) for ac in rede.acoes_comportamentos if _get_id(ac) in acoes_pos_antecedente_ids],
            "relacoes_temporais_relevantes": [rt.model_dump(exclude_none=True) for rt in rede.relacoes_temporais if rt.tipo_temporalidade.value == "PRECEDE_IMEDIATAMENTE"], # type: ignore
            "relacoes_funcionais_antecedentes_existentes": [rfa.model_dump(exclude_none=True) for rfa in rede.relacoes_funcionais_antecedentes]
        }

    def update_rede_func(rede: RedeContingencialOutput, json_data: dict) -> str: # Returns string for log
        novas_rfa_data = json_data.get("relacoes_funcionais_antecedentes")
        if novas_rfa_data is None:
            novas_rfa_data = []
        rede.relacoes_funcionais_antecedentes = _merge_element_list(rede.relacoes_funcionais_antecedentes, novas_rfa_data, ArestaRelacaoFuncionalAntecedente)

        # Opcional: atualizar nós se a API os retornou com modificações
        estimulos_atualizados_data = json_data.get("estimulos_eventos_atualizados")
        if estimulos_atualizados_data:
            rede.estimulos_eventos = _merge_element_list(rede.estimulos_eventos, estimulos_atualizados_data, NoEstimuloEvento)

        acoes_atualizadas_data = json_data.get("acoes_comportamentos_atualizados")
        if acoes_atualizadas_data:
            rede.acoes_comportamentos = _merge_element_list(rede.acoes_comportamentos, acoes_atualizadas_data, NoAcaoComportamento)
            
        return f"Relações Funcionais Antecedentes: {len(rede.relacoes_funcionais_antecedentes)}"

    return _processar_etapa(
        texto_narrativo=texto_narrativo,
        rede_atual=rede_atual,
        client_model=client_model,
        foco_etapa=FOCO_ETAPA_FUNCIONAIS_ANTECEDENTES,
        output_schema=OutputEtapaFuncionaisAntecedentes,
        context_builder_func=context_builder_func,
        update_rede_func=update_rede_func,
        etapa_name="Inferência de Relações Funcionais Antecedentes"
    )

def inferir_relacoes_funcionais_consequentes(
    texto_narrativo: str,
    rede_atual: RedeContingencialOutput,
    client_model: genai.Client, # Type hint kept as genai.Client for now
) -> RedeContingencialOutput:
    def context_builder_func(rede: RedeContingencialOutput) -> dict:
        consequentes_ids = set()
        acoes_pre_consequente_ids = set()
        for rt in rede.relacoes_temporais:
            if rt.tipo_temporalidade.value == "SUCEDE_IMEDIATAMENTE": # type: ignore
                acoes_pre_consequente_ids.add(rt.id_origem_no)
                consequentes_ids.add(rt.id_destino_no)

        return {
            "acoes_comportamentos_relevantes": [ac.model_dump(exclude_none=True) for ac in rede.acoes_comportamentos if _get_id(ac) in acoes_pre_consequente_ids],
            "estimulos_eventos_relevantes": [e.model_dump(exclude_none=True) for e in rede.estimulos_eventos if _get_id(e) in consequentes_ids],
            "relacoes_temporais_relevantes": [rt.model_dump(exclude_none=True) for rt in rede.relacoes_temporais if rt.tipo_temporalidade.value == "SUCEDE_IMEDIATAMENTE"], # type: ignore
            "relacoes_funcionais_consequentes_existentes": [rfc.model_dump(exclude_none=True) for rfc in rede.relacoes_funcionais_consequentes]
        }

    def update_rede_func(rede: RedeContingencialOutput, json_data: dict) -> str: # Returns string for log
        novas_rfc_data = json_data.get("relacoes_funcionais_consequentes")
        if novas_rfc_data is None:
            novas_rfc_data = []
        rede.relacoes_funcionais_consequentes = _merge_element_list(rede.relacoes_funcionais_consequentes, novas_rfc_data, ArestaRelacaoFuncionalConsequente)

        estimulos_atualizados_data = json_data.get("estimulos_eventos_atualizados")
        if estimulos_atualizados_data:
            rede.estimulos_eventos = _merge_element_list(rede.estimulos_eventos, estimulos_atualizados_data, NoEstimuloEvento)

        acoes_atualizadas_data = json_data.get("acoes_comportamentos_atualizados")
        if acoes_atualizadas_data:
            rede.acoes_comportamentos = _merge_element_list(rede.acoes_comportamentos, acoes_atualizadas_data, NoAcaoComportamento)
            
        return f"Relações Funcionais Consequentes: {len(rede.relacoes_funcionais_consequentes)}"

    return _processar_etapa(
        texto_narrativo=texto_narrativo,
        rede_atual=rede_atual,
        client_model=client_model,
        foco_etapa=FOCO_ETAPA_FUNCIONAIS_CONSEQUENTES,
        output_schema=OutputEtapaFuncionaisConsequentes,
        context_builder_func=context_builder_func,
        update_rede_func=update_rede_func,
        etapa_name="Inferência de Relações Funcionais Consequentes"
    )

def identificar_condicoes_estado(
    texto_narrativo: str,
    rede_atual: RedeContingencialOutput,
    client_model: genai.Client, # Type hint kept as genai.Client for now
) -> RedeContingencialOutput:
    def context_builder_func(rede: RedeContingencialOutput) -> dict:
        return {
            "rede_parcial_existente_para_contexto": {
                "sujeitos": [s.model_dump(exclude_none=True) for s in rede.sujeitos],
                "acoes_comportamentos": [ac.model_dump(exclude_none=True) for ac in rede.acoes_comportamentos],
                "estimulos_eventos": [e.model_dump(exclude_none=True) for e in rede.estimulos_eventos],
                "relacoes_funcionais_antecedentes": [rfa.model_dump(exclude_none=True) for rfa in rede.relacoes_funcionais_antecedentes],
                "relacoes_funcionais_consequentes": [rfc.model_dump(exclude_none=True) for rfc in rede.relacoes_funcionais_consequentes],
            },
            "condicoes_estados_existentes": [ce.model_dump(exclude_none=True) for ce in rede.condicoes_estados]
        }

    def update_rede_func(rede: RedeContingencialOutput, json_data: dict) -> str: # Returns string for log
        novas_ce_data = json_data.get("condicoes_estados")
        if novas_ce_data is None:
            novas_ce_data = []
        rede.condicoes_estados = _merge_element_list(rede.condicoes_estados, novas_ce_data, NoCondicaoEstado)
        return f"Condições/Estado: {len(rede.condicoes_estados)}"

    return _processar_etapa(
        texto_narrativo=texto_narrativo,
        rede_atual=rede_atual,
        client_model=client_model,
        foco_etapa=FOCO_ETAPA_CONDICOES_ESTADO,
        output_schema=OutputEtapaCondicoesEstado,
        context_builder_func=context_builder_func,
        update_rede_func=update_rede_func,
        etapa_name="Identificação de Condições/Estado"
    )

def estabelecer_relacoes_moduladoras_estado(
    texto_narrativo: str,
    rede_atual: RedeContingencialOutput,
    client_model: genai.Client, # Type hint kept as genai.Client for now
) -> RedeContingencialOutput:
    def context_builder_func(rede: RedeContingencialOutput) -> dict:
        return {
            "condicoes_estados": [ce.model_dump(exclude_none=True) for ce in rede.condicoes_estados],
            "estimulos_eventos": [e.model_dump(exclude_none=True) for e in rede.estimulos_eventos], # Especialmente consequentes
            "acoes_comportamentos": [ac.model_dump(exclude_none=True) for ac in rede.acoes_comportamentos],
            "relacoes_funcionais_consequentes": [rfc.model_dump(exclude_none=True) for rfc in rede.relacoes_funcionais_consequentes], # Para saber o que é reforçador/punitivo
            "relacoes_moduladoras_estado_existentes": [rme.model_dump(exclude_none=True) for rme in rede.relacoes_moduladoras_estado]
        }

    def update_rede_func(rede: RedeContingencialOutput, json_data: dict) -> str: # Returns string for log
        novas_rme_data = json_data.get("relacoes_moduladoras_estado")
        if novas_rme_data is None:
            novas_rme_data = []
        rede.relacoes_moduladoras_estado = _merge_element_list(rede.relacoes_moduladoras_estado, novas_rme_data, ArestaRelacaoModuladoraEstado)

        # Opcional: atualizar nós se a API os retornou com modificações
        condicoes_atualizadas_data = json_data.get("condicoes_estados_atualizadas")
        if condicoes_atualizadas_data:
             rede.condicoes_estados = _merge_element_list(rede.condicoes_estados, condicoes_atualizadas_data, NoCondicaoEstado)

        estimulos_atualizados_data = json_data.get("estimulos_eventos_atualizados")
        if estimulos_atualizados_data:
            rede.estimulos_eventos = _merge_element_list(rede.estimulos_eventos, estimulos_atualizados_data, NoEstimuloEvento)

        acoes_atualizadas_data = json_data.get("acoes_comportamentos_atualizados")
        if acoes_atualizadas_data:
            rede.acoes_comportamentos = _merge_element_list(rede.acoes_comportamentos, acoes_atualizadas_data, NoAcaoComportamento)
            
        return f"Relações Moduladoras: {len(rede.relacoes_moduladoras_estado)}"

    return _processar_etapa(
        texto_narrativo=texto_narrativo,
        rede_atual=rede_atual,
        client_model=client_model,
        foco_etapa=FOCO_ETAPA_RELACOES_MODULADORAS,
        output_schema=OutputEtapaRelacoesModuladoras,
        context_builder_func=context_builder_func,
        update_rede_func=update_rede_func,
        etapa_name="Estabelecimento de Relações Moduladoras de Estado"
    )

def formular_hipoteses_analiticas_e_evidencias(
    texto_narrativo: str,
    rede_atual: RedeContingencialOutput,
    client_model: genai.Client, # Type hint kept as genai.Client for now
) -> RedeContingencialOutput:
    def context_builder_func(rede: RedeContingencialOutput) -> dict:
        # Ensure datetime is available in this scope if not already imported globally
        # It is imported globally in the file.
        data_formulacao_atual = datetime.datetime.now().isoformat()
        return {
            "rede_completa_existente": rede.model_dump(exclude_none=True), # Passa a rede toda
            "data_para_formulacao_hipotese": data_formulacao_atual,
            "hipoteses_existentes": [h.model_dump(exclude_none=True) for h in rede.hipoteses_analiticas],
            "evidencias_existentes": [ev.model_dump(exclude_none=True) for ev in rede.evidencias_para_hipoteses]
        }

    def update_rede_func(rede: RedeContingencialOutput, json_data: dict) -> str: # Returns string for log
        novas_hipoteses_data = json_data.get("hipoteses_analiticas")
        novas_evidencias_data = json_data.get("evidencias_para_hipoteses")

        if novas_hipoteses_data is None:
            novas_hipoteses_data = []
        if novas_evidencias_data is None:
            novas_evidencias_data = []

        rede.hipoteses_analiticas = _merge_element_list(rede.hipoteses_analiticas, novas_hipoteses_data, NoHipoteseAnalitica)
        rede.evidencias_para_hipoteses = _merge_element_list(rede.evidencias_para_hipoteses, novas_evidencias_data, ArestaEvidenciaParaHipotese)

        return f"Hipóteses: {len(rede.hipoteses_analiticas)}, Evidências: {len(rede.evidencias_para_hipoteses)}"

    return _processar_etapa(
        texto_narrativo=texto_narrativo,
        rede_atual=rede_atual,
        client_model=client_model,
        foco_etapa=FOCO_ETAPA_HIPOTESES,
        output_schema=OutputEtapaHipoteses,
        context_builder_func=context_builder_func,
        update_rede_func=update_rede_func,
        etapa_name="Formulação de Hipóteses Analíticas e Evidências"
    )

def ordenar_timeline(
    texto_narrativo: str,
    rede_atual: RedeContingencialOutput,
    client_model: genai.Client, # Type hint kept as genai.Client for now
) -> RedeContingencialOutput:
    def context_builder_func(rede: RedeContingencialOutput) -> dict:
        # Helper to extract id and descricao, ensuring items are dicts with these keys
        def name_id_extractor(key_name: str) -> list:
            items_list = []
            raw_items = rede.model_dump().get(key_name, [])
            for item_model in raw_items:
                # item_model is already a dict here due to model_dump()
                if isinstance(item_model, dict) and 'id' in item_model and 'descricao' in item_model:
                    items_list.append((item_model['id'], item_model['descricao']))
                # If item_model is not a dict (e.g. if the list contains non-dict elements unexpectedly), skip.
            return items_list

        return {
            "sujeitos" : name_id_extractor('sujeitos'),
            "acoes_comportamentos" : name_id_extractor('acoes_comportamentos'),
            "estimulos_eventos" : name_id_extractor('estimulos_eventos'),
            "hipoteses_analiticas" : name_id_extractor('hipoteses_analiticas')
        }

    def update_rede_func(rede: RedeContingencialOutput, json_data: dict) -> str: # Returns string for log
        timeline_data = json_data.get("timeline")

        # Initialize timeline if it's None
        if rede.timeline is None:
            rede.timeline = []

        if timeline_data is not None:
            # Ensure all IDs are strings for consistency
            rede.timeline = [str(item) for item in timeline_data]

        # Add Hipoteses_Analiticas nodes to the end of the timeline if not already included
        # _get_id is imported from utils
        hipoteses_ids = {_get_id(h) for h in rede.hipoteses_analiticas if _get_id(h) is not None}
        current_timeline_ids = set(rede.timeline) # rede.timeline is guaranteed to be a list here

        for h_id in hipoteses_ids:
            if h_id not in current_timeline_ids:
                rede.timeline.append(h_id)
                # Original logger.debug(f"Adicionado Hipotese_Analitica '{h_id}' ao final da timeline.")
                # This debug log can be omitted for brevity as the main function logs completion.

        return f"Nós na timeline: {len(rede.timeline)}"

    return _processar_etapa(
        texto_narrativo=texto_narrativo,
        rede_atual=rede_atual,
        client_model=client_model,
        foco_etapa=FOCO_ETAPA_TIMELINE,
        output_schema=OutputEtapaTimeline,
        context_builder_func=context_builder_func,
        update_rede_func=update_rede_func,
        etapa_name="Ordenação da Timeline"
    )

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
