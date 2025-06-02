# analysis_modular.py
from output_schemas import RedeContingencialOutput
from typing import List, Optional, Dict, Any, Type, Union, cast
from dotenv import load_dotenv
from google.genai import Client # NÃO MODIFICAR / DO NOT MODIFY
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

# --- Funções de Extração por Etapa ---

def extrair_sujeitos(
    texto_narrativo: str,
    rede_atual: RedeContingencialOutput,
    client_model: Client,
) -> RedeContingencialOutput:
    logger.info("Iniciando Etapa: Extração de Sujeitos")
    foco_da_etapa = FOCO_ETAPA_SUJEITOS
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
            logger.info(f"Etapa concluída. Sujeitos atuais: {len(rede_atual.sujeitos)}")
        except Exception as e:
            logger.error(f"Erro ao processar dados da Etapa: {e}", exc_info=True)
    return rede_atual

def extrair_acoes_comportamentos(
    texto_narrativo: str,
    rede_atual: RedeContingencialOutput,
    client_model: Client,
) -> RedeContingencialOutput:
    logger.info("Iniciando Etapa: Extração de Ações e Emissões Comportamentais")
    foco_da_etapa = FOCO_ETAPA_ACOES
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
            logger.info(f"Etapa concluída. Ações: {len(rede_atual.acoes_comportamentos)}, Emissões: {len(rede_atual.emissoes_comportamentais)}")
        except Exception as e:
            logger.error(f"Erro ao processar dados da Etapa: {e}", exc_info=True)
    return rede_atual

def extrair_eventos_ambientais_e_relacoes_temporais(
    texto_narrativo: str,
    rede_atual: RedeContingencialOutput,
    client_model: Client,
) -> RedeContingencialOutput:
    logger.info("Iniciando: Extração de Eventos Ambientais e Relações Temporais")
    foco_da_etapa = FOCO_ETAPA_EVENTOS_TEMPORAIS
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
            logger.info(f" concluída. Estímulos: {len(rede_atual.estimulos_eventos)}, Relações Temporais: {len(rede_atual.relacoes_temporais)}")
        except Exception as e:
            logger.error(f"Erro ao processar dados da etapa : {e}", exc_info=True)
    return rede_atual

def inferir_relacoes_funcionais_antecedentes(
    texto_narrativo: str,
    rede_atual: RedeContingencialOutput,
    client_model: Client,
) -> RedeContingencialOutput:
    logger.info("Iniciando: Inferência de Relações Funcionais Antecedentes")
    foco_da_etapa = FOCO_ETAPA_FUNCIONAIS_ANTECEDENTES
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

            logger.info(f" concluída. Relações Funcionais Antecedentes: {len(rede_atual.relacoes_funcionais_antecedentes)}")
        except Exception as e:
            logger.error(f"Erro ao processar dados da etapa : {e}", exc_info=True)
    return rede_atual

def inferir_relacoes_funcionais_consequentes(
    texto_narrativo: str,
    rede_atual: RedeContingencialOutput,
    client_model: Client,
) -> RedeContingencialOutput:
    logger.info("Iniciando: Inferência de Relações Funcionais Consequentes")
    foco_da_etapa = FOCO_ETAPA_FUNCIONAIS_CONSEQUENTES
    
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

            logger.info(f" concluída. Relações Funcionais Consequentes: {len(rede_atual.relacoes_funcionais_consequentes)}")
        except Exception as e:
            logger.error(f"Erro ao processar dados da etapa : {e}", exc_info=True)
    return rede_atual

def identificar_condicoes_estado(
    texto_narrativo: str,
    rede_atual: RedeContingencialOutput,
    client_model: Client,
) -> RedeContingencialOutput:
    logger.info("Iniciando: Identificação de Condições/Estado")
    foco_da_etapa = FOCO_ETAPA_CONDICOES_ESTADO
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
            logger.info(f" concluída. Condições/Estado: {len(rede_atual.condicoes_estados)}")
        except Exception as e:
            logger.error(f"Erro ao processar dados da etapa : {e}", exc_info=True)
    return rede_atual

def estabelecer_relacoes_moduladoras_estado(
    texto_narrativo: str,
    rede_atual: RedeContingencialOutput,
    client_model: Client,
) -> RedeContingencialOutput:
    logger.info("Iniciando: Estabelecimento de Relações Moduladoras de Estado")
    foco_da_etapa = FOCO_ETAPA_RELACOES_MODULADORAS
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

            logger.info(f" concluída. Relações Moduladoras: {len(rede_atual.relacoes_moduladoras_estado)}")
        except Exception as e:
            logger.error(f"Erro ao processar dados da etapa : {e}", exc_info=True)
    return rede_atual

def formular_hipoteses_analiticas_e_evidencias(
    texto_narrativo: str,
    rede_atual: RedeContingencialOutput,
    client_model: Client,
) -> RedeContingencialOutput:
    logger.info("Iniciando: Formulação de Hipóteses Analíticas e Evidências")
    foco_da_etapa = FOCO_ETAPA_HIPOTESES
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
        "Contexto da rede atual (rede completa para embasar as hipóteses):\n"
        f"```json\n{json.dumps(contexto_json, indent=2)}\n```"
    )

    json_data = _make_api_call(client_model, prompt, OutputEtapaHipoteses)
    if json_data:
        try:
            novas_hipoteses_data = json_data.get("hipoteses_analiticas")
            novas_evidencias_data = json_data.get("evidencias_para_hipoteses")

            rede_atual.hipoteses_analiticas = _merge_element_list(rede_atual.hipoteses_analiticas, novas_hipoteses_data, NoHipoteseAnalitica)
            rede_atual.evidencias_para_hipoteses = _merge_element_list(rede_atual.evidencias_para_hipoteses, novas_evidencias_data, ArestaEvidenciaParaHipotese)
            logger.info(f" concluída. Hipóteses: {len(rede_atual.hipoteses_analiticas)}, Evidências: {len(rede_atual.evidencias_para_hipoteses)}")
        except Exception as e:
            logger.error(f"Erro ao processar dados da etapa : {e}", exc_info=True)
    return rede_atual

def ordenar_timeline(
    texto_narrativo: str,
    rede_atual: RedeContingencialOutput,
    client_model: Client,
) -> RedeContingencialOutput:
    logger.info("Iniciando: Ordenação da Timeline")
    foco_da_etapa = FOCO_ETAPA_TIMELINE
    name_id = lambda key : [(item['id'], item['descricao']) for item in rede_atual.model_dump()[key]]
    contexto_json = {
        "sujeitos" : name_id('sujeitos'),
        "acoes_comportamentos" : name_id('acoes_comportamentos'),
        "estimulos_eventos" : name_id('estimulos_eventos'),
        "hipoteses_analiticas" : name_id('hipoteses_analiticas')
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
                # Ensure all IDs are strings for consistency
                rede_atual.timeline = [str(item) for item in timeline_data]

            # Add Hipotesis_Analiticas nodes to the end of the timeline if not already included
            hipoteses_ids = {_get_id(h) for h in rede_atual.hipoteses_analiticas if _get_id(h) is not None}
            current_timeline_ids = set(rede_atual.timeline)

            for h_id in hipoteses_ids:
                if h_id not in current_timeline_ids:
                    rede_atual.timeline.append(h_id)
                    logger.debug(f"Adicionado Hipotese_Analitica '{h_id}' ao final da timeline.")

            logger.info(f" concluída. Nós na timeline: {len(rede_atual.timeline)}")
        except Exception as e:
            logger.error(f"Erro ao processar dados da etapa : {e}", exc_info=True)
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
        client_model = Client(api_key=api_key) # Modelo é instanciado aqui
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
