from typing import List, Optional, Dict, Any, Type
from pydantic import BaseModel, ValidationError # Added ValidationError
import logging

logger = logging.getLogger(__name__)

def _get_id(element: BaseModel) -> Optional[str]:
    """Retorna o valor do campo ID do elemento Pydantic, se existir."""
    for field_name in ["id_sujeito", "id_acao", "id_estimulo_evento", "id_condicao_estado", "id_hipotese", "id"]:
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


def transformar_para_vis(json_data: dict):
    """
    Transforma o JSON da análise em um formato compatível com Vis.js (nodes e edges).
    Garante que os IDs das arestas sejam únicos.
    """
    nodes = []
    edges = []
    node_ids = set() # Para rastrear IDs de nós e evitar duplicatas
    edge_ids = set() # Para rastrear IDs de arestas e garantir unicidade

    # Mapeamento de cores para diferentes tipos de nós
    colors = {
        'sujeito': '#FFD700',    # Gold
        'acao': '#ADD8E6',       # LightBlue
        'estimulo': '#90EE90',   # LightGreen
        'condicao': '#FFA07A',   # LightSalmon
    }

    # Processar Sujeitos
    for s_idx, s in enumerate(json_data.get("sujeitos", [])):
        node_id = s.get("id", f"s_fallback_{s_idx}")
        if node_id not in node_ids:
            nodes.append({
                "id": node_id,
                "label": s.get("descricao", "Sujeito Desconhecido"),
                "group": "sujeito",
                "info": {
                    "ID": node_id,
                    "Histórico Relevante": s.get('historico_relevante', 'N/A'),
                    "Raciocínio": s.get('raciocinio', 'N/A')
                },
                "color": colors['sujeito']
            })
            node_ids.add(node_id)

    # Processar Ações/Comportamentos
    for ac_idx, ac in enumerate(json_data.get("acoes_comportamentos", [])):
        node_id = ac.get("id", f"ac_fallback_{ac_idx}")
        if node_id not in node_ids:
            nodes.append({
                "id": node_id,
                "label": ac.get("descricao", "Ação Desconhecida"),
                "group": "acao",
                "info": {
                    "ID": node_id,
                    "Tipo Observabilidade": ac.get('tipo_observabilidade', 'N/A'),
                    "Classe Funcional Hipotética": ', '.join(ac.get('classe_funcional_hipotetica', ['N/A'])),
                    "Raciocínio": ac.get('raciocinio', 'N/A')
                },
                "color": colors['acao'],
                "shape": "box"
            })
            node_ids.add(node_id)

    # Processar Estímulos/Eventos
    for e_idx, e in enumerate(json_data.get("estimulos_eventos", [])):
        node_id = e.get("id", f"e_fallback_{e_idx}")
        if node_id not in node_ids:
            nodes.append({
                "id": node_id,
                "label": e.get("descricao", "Estímulo Desconhecido"),
                "group": "estimulo",
                "info": {
                    "ID": node_id,
                    "Raciocínio": e.get('raciocinio', 'N/A')
                },
                "color": colors['estimulo'],
                "shape": "ellipse"
            })
            node_ids.add(node_id)

    # Processar Condições/Estados
    for ce_idx, ce in enumerate(json_data.get("condicoes_estados", [])):
        node_id = ce.get("id", f"ce_fallback_{ce_idx}")
        if node_id not in node_ids:
            nodes.append({
                "id": node_id,
                "label": ce.get("descricao", "Condição Desconhecida"),
                "group": "condicao",
                "info": {
                    "ID": node_id,
                    "Tipo Condição": ce.get('tipo_condicao', 'N/A'),
                    "Duração": ce.get('duracao_condicao_desc', 'N/A'),
                    "Raciocínio": ce.get('raciocinio', 'N/A')
                },
                "color": colors['condicao'],
                "shape": "diamond"
            })
            node_ids.add(node_id)

    # Processar Hipóteses Analíticas
    for h_idx, h in enumerate(json_data.get("hipoteses_analiticas", [])):
        node_id = h.get("id", f"h_fallback_{h_idx}")
        if node_id not in node_ids:
            nodes.append({
                "id": node_id,
                "label": h.get("descricao", "Hipótese Desconhecida"),
                "group": "hipotese",
                "info": {
                    "ID": node_id,
                    "Descrição": h.get('descricao', 'N/A'),
                    "Confiança": h.get('nivel_confianca', 'N/A'),
                    "Raciocínio": h.get('raciocinio', 'N/A')
                },
                "color": '#a753f5', # Purple
                "shape": "box"
            })
            node_ids.add(node_id)
    
    # Função auxiliar para adicionar arestas garantindo ID único
    def add_edge(edge_data, default_prefix="edge"):
        original_id = edge_data.get("id")
        new_id = original_id
        counter = 0
        while new_id in edge_ids: # Garante que o ID da aresta seja único
            counter += 1
            new_id = f"{original_id}_{counter}" if original_id else f"{default_prefix}_{len(edge_ids)}_{counter}"
        
        edge_ids.add(new_id)
        
        # Verifica se os nós de origem e destino existem
        if edge_data.get("id_origem_no") not in node_ids or edge_data.get("id_destino_no") not in node_ids:
            print(f"Aviso: Nós para a aresta '{new_id}' (origem: {edge_data.get('id_origem_no')}, destino: {edge_data.get('id_destino_no')}) não encontrados. Aresta ignorada.")
            return

        
        label = edge_data.get("label", "").replace("_", " ").title()
        # Adiciona quebra de linha se o label for muito longo
        if len(label) > 10: # Ajuste o valor conforme necessário
            label = label.replace(" ", "\n", 1) # Quebra na primeira ocorrência de espaço

        edges.append({
            "id": new_id,
            "from": edge_data.get("id_origem_no"),
            "to": edge_data.get("id_destino_no"),
            "label": label,
            "arrows": edge_data.get("arrows", "to"),
            "title": edge_data.get("title", ""),
            "color": edge_data.get("color", {"color": "#848484", "highlight": "#848484", "hover": "#848484"}),
            "dashes": edge_data.get("dashes", False)
        })

    # Processar Emissões Comportamentais
    for em_idx, em in enumerate(json_data.get("emissoes_comportamentais", [])):
        add_edge({
            "id": em.get("id", f"em_edge_{em_idx}"),
            "id_origem_no": em.get("id_origem_no"),
            "id_destino_no": em.get("id_destino_no"),
            "label": "Emite",
            "info": {
                "ID Aresta": em.get('id', f'em_edge_{em_idx}').replace('_', ' ').title(),
                "Tipo": em.get('tipo_aresta', 'N/A'),
                "Raciocínio": em.get('raciocinio', 'N/A')
            },
        }, "emissao")

    # Processar Relações Temporais
    for rt_idx, rt in enumerate(json_data.get("relacoes_temporais", [])):
        temporal_label = rt.get("tipo_temporalidade", "Temporal").replace("_", " ").title()
        # Adiciona quebra de linha se o label for muito longo
        if len(temporal_label) > 15: # Ajuste o valor conforme necessário
            temporal_label = temporal_label.replace(" ", "\n", 1) # Quebra na primeira ocorrência de espaço

        add_edge({
            "id": rt.get("id", f"rt_edge_{rt_idx}"),
            "id_origem_no": rt.get("id_origem_no"),
            "id_destino_no": rt.get("id_destino_no"),
            "label": temporal_label,
            "dashes": True,
            "info": {
                "ID Aresta": rt.get('id', f'rt_edge_{rt_idx}').replace('_', ' ').title(),
                "Tipo": rt.get('tipo_aresta', 'N/A'),
                "Contiguidade Percebida": rt.get('contiguidade_percebida', 'N/A'),
                "Raciocínio": rt.get('raciocinio', 'N/A')
            },
            "color": {"color": "#50C878", "highlight": "#3AA05A", "hover": "#3AA05A"}
        }, "temporal")

    # Processar Relações Funcionais Antecedentes
    for rfa_idx, rfa in enumerate(json_data.get("relacoes_funcionais_antecedentes", [])):
        add_edge({
            "id": rfa.get("id", f"rfa_edge_{rfa_idx}"),
            "id_origem_no": rfa.get("id_origem_no"),
            "id_destino_no": rfa.get("id_destino_no"),
            "label": f"Antecedente: {rfa.get('funcao_antecedente', 'N/A')}",
            "info": {
                "ID Aresta": rfa.get('id', f'rfa_edge_{rfa_idx}').replace('_', ' ').title(),
                "Função": rfa.get('funcao_antecedente', 'N/A'),
                "Prob. Resposta na Presença": rfa.get('prob_resposta_na_presenca', 'N/A'),
                "Prob. Resposta na Ausência": rfa.get('prob_resposta_na_ausencia', 'N/A'),
                "Raciocínio": rfa.get('raciocinio', 'N/A')
            },
            "color": {"color": "#4682B4", "highlight": "#3671A2", "hover": "#3671A2"}
        }, "antecedente")

    # Processar Relações Funcionais Consequentes
    for rfc_idx, rfc in enumerate(json_data.get("relacoes_funcionais_consequentes", [])):
        add_edge({
            "id": rfc.get("id", f"rfc_edge_{rfc_idx}"),
            "id_origem_no": rfc.get("id_origem_no"),
            "id_destino_no": rfc.get("id_destino_no"),
            "label": f"Consequente: {rfc.get('funcao_consequente', 'N/A')}",
            "info": {
                "ID Aresta": rfc.get('id', f'rfc_edge_{rfc_idx}').replace('_', ' ').title(),
                "Função": rfc.get('funcao_consequente', 'N/A'),
                "Imediatismo": rfc.get('imediatismo_consequencia', 'N/A'),
                "Magnitude": rfc.get('magnitude_consequencia', 'N/A'),
                "Parâmetro Esquema": rfc.get('parametro_esquema', 'N/A'),
                "Raciocínio": rfc.get('raciocinio', 'N/A')
            },
            "color": {"color": "#FF6347", "highlight": "#E05135", "hover": "#E05135"}
        }, "consequente")

    # Processar Relações Moduladoras de Estado
    for rms_idx, rms in enumerate(json_data.get("relacoes_moduladoras_estado", [])):
        add_edge({
            "id": rms.get("id", f"rms_edge_{rms_idx}"),
            "id_origem_no": rms.get("id_origem_no"),
            "id_destino_no": rms.get("id_destino_no"),
            "label": f"Modula: {rms.get('tipo_modulacao_estado', 'N/A')}",
            "info": {
                "ID Aresta": rms.get('id', f'rms_edge_{rms_idx}').replace('_', ' ').title(),
                "Tipo Modulação": rms.get('tipo_modulacao_estado', 'N/A'),
                "Alvo Modulação Valor": rms.get('alvo_da_modulacao_valor_ref_id_estimulo', 'N/A'),
                "Efeito Modulatório Valor": rms.get('descricao_efeito_modulatorio_valor', 'N/A'),
                "Alvo Modulação Frequência": rms.get('alvo_da_modulacao_frequencia_ref_id_acao', 'N/A'),
                "Efeito Modulatório Frequência": rms.get('descricao_efeito_modulatorio_frequencia', 'N/A'),
                "Raciocínio": rms.get('raciocinio', 'N/A')
            },
            "color": {"color": "#8A2BE2", "highlight": "#6A1AC2", "hover": "#6A1AC2"} # BlueViolet
        }, "moduladora_estado")

    # Processar Evidências para Hipóteses
    for eph_idx, eph in enumerate(json_data.get("evidencias_para_hipoteses", [])):
        add_edge({
            "id": eph.get("id", f"eph_edge_{eph_idx}"),
            "id_origem_no": eph.get("id_origem_no"),
            "id_destino_no": eph.get("id_destino_no"),
            "label": eph.get("tipo_evidencia", "Evidência"),
            "info": {
                "ID Aresta": eph.get('id', f'eph_edge_{eph_idx}').replace('_', ' ').title(),
                "Tipo": eph.get('tipo_evidencia', 'N/A'),
                "Elementos Suporte": ', '.join(eph.get('ids_elementos_contingencia_suporte', [])),
                "Raciocínio": eph.get('raciocinio', 'N/A')
            },
            "color": {"color": "#8B4513", "highlight": "#6F360F", "hover": "#6F360F"} # SaddleBrown
        }, "evidencia_hipotese")
    
    # Identificar nós conectados
    connected_node_ids = set()
    for edge in edges:
        connected_node_ids.add(edge["from"])
        connected_node_ids.add(edge["to"])
    
    # Filtrar nós para remover isolados
    filtered_nodes = [node for node in nodes if node["id"] in connected_node_ids]
        
    return filtered_nodes, edges
