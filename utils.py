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
        node_id = s.get("id_sujeito", f"s_fallback_{s_idx}")
        if node_id not in node_ids:
            nodes.append({
                "id": node_id,
                "label": s.get("nome_descritivo", "Sujeito Desconhecido"),
                "group": "sujeito",
                "title": f"ID: {node_id}\nEspécie: {s.get('especie', 'N/A')}\nIdade: {s.get('idade', 'N/A')}",
                "color": colors['sujeito']
            })
            node_ids.add(node_id)

    # Processar Ações/Comportamentos
    for ac_idx, ac in enumerate(json_data.get("acoes_comportamentos", [])):
        node_id = ac.get("id_acao", f"ac_fallback_{ac_idx}")
        if node_id not in node_ids:
            nodes.append({
                "id": node_id,
                "label": ac.get("descricao_topografica", "Ação Desconhecida"),
                "group": "acao",
                "title": f"ID: {node_id}\nTipo: {ac.get('tipo_observabilidade', 'N/A')}",
                "color": colors['acao'],
                "shape": "box"
            })
            node_ids.add(node_id)

    # Processar Estímulos/Eventos
    for e_idx, e in enumerate(json_data.get("estimulos_eventos", [])):
        node_id = e.get("id_estimulo_evento", f"e_fallback_{e_idx}")
        if node_id not in node_ids:
            nodes.append({
                "id": node_id,
                "label": e.get("descricao", "Estímulo Desconhecido"),
                "group": "estimulo",
                "title": f"ID: {node_id}\nTipo: {e.get('tipo_fisico', 'N/A')}\nModalidade: {e.get('modalidade_sensorial_primaria', 'N/A')}",
                "color": colors['estimulo'],
                "shape": "ellipse"
            })
            node_ids.add(node_id)

    # Processar Condições/Estados
    for ce_idx, ce in enumerate(json_data.get("condicoes_estados", [])):
        node_id = ce.get("id_condicao_estado", f"ce_fallback_{ce_idx}")
        if node_id not in node_ids:
            nodes.append({
                "id": node_id,
                "label": ce.get("descricao", "Condição Desconhecida"),
                "group": "condicao",
                "title": f"ID: {node_id}\nTipo: {ce.get('tipo_condicao', 'N/A')}",
                "color": colors['condicao'],
                "shape": "diamond"
            })
            node_ids.add(node_id)

    # Processar Hipóteses Analíticas
    for h_idx, h in enumerate(json_data.get("hipoteses_analiticas", [])):
        node_id = h.get("id_hipotese", f"h_fallback_{h_idx}")
        if node_id not in node_ids:
            nodes.append({
                "id": node_id,
                "label": h.get("descricao_hipotese", "Hipótese Desconhecida"),
                "group": "hipotese",
                "title": f"ID: {node_id}\nDescrição: {h.get('descricao_hipotese', 'N/A')}\nConfiança: {h.get('nivel_confianca', 'N/A')}\nStatus: {h.get('status_hipotese', 'N/A')}",
                "color": '#a753f5', # Purple
                "shape": "box"
            })
            node_ids.add(node_id)
    
    # Função auxiliar para adicionar arestas garantindo ID único
    def add_edge(edge_data, default_prefix="edge"):
        original_id = edge_data.get("id_aresta")
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
            "id_aresta": em.get("id_aresta", f"em_edge_{em_idx}"),
            "id_origem_no": em.get("id_origem_no"),
            "id_destino_no": em.get("id_destino_no"),
            "label": "Emite",
            "title": f"ID Aresta: {em.get('id_aresta', f'em_edge_{em_idx}').replace('_', ' ').title()}\nTipo: {em.get('tipo_aresta', 'N/A')}\nObs: {em.get('observacoes_adicionais', 'N/A')}",
        }, "emissao")

    # Processar Relações Temporais
    for rt_idx, rt in enumerate(json_data.get("relacoes_temporais", [])):
        temporal_label = rt.get("tipo_temporalidade", "Temporal").replace("_", " ").title()
        # Adiciona quebra de linha se o label for muito longo
        if len(temporal_label) > 15: # Ajuste o valor conforme necessário
            temporal_label = temporal_label.replace(" ", "\n", 1) # Quebra na primeira ocorrência de espaço

        add_edge({
            "id_aresta": rt.get("id_aresta", f"rt_edge_{rt_idx}"),
            "id_origem_no": rt.get("id_origem_no"),
            "id_destino_no": rt.get("id_destino_no"),
            "label": temporal_label,
            "dashes": True,
            "title": f"ID Aresta: {rt.get('id_aresta', f'rt_edge_{rt_idx}').replace('_', ' ').title()}\nTipo: {rt.get('tipo_aresta', 'N/A')}\nObs: {rt.get('observacoes_adicionais', 'N/A')}",
            "color": {"color": "#50C878", "highlight": "#3AA05A", "hover": "#3AA05A"}
        }, "temporal")

    # Processar Relações Funcionais Antecedentes
    for rfa_idx, rfa in enumerate(json_data.get("relacoes_funcionais_antecedentes", [])):
        add_edge({
            "id_aresta": rfa.get("id_aresta", f"rfa_edge_{rfa_idx}"),
            "id_origem_no": rfa.get("id_origem_no"),
            "id_destino_no": rfa.get("id_destino_no"),
            "label": f"Antecedente: {rfa.get('funcao_antecedente', 'N/A')}",
            "title": f"ID Aresta: {rfa.get('id_aresta', f'rfa_edge_{rfa_idx}').replace('_', ' ').title()}\nFunção: {rfa.get('funcao_antecedente', 'N/A')}",
            "color": {"color": "#4682B4", "highlight": "#3671A2", "hover": "#3671A2"}
        }, "antecedente")

    # Processar Relações Funcionais Consequentes
    for rfc_idx, rfc in enumerate(json_data.get("relacoes_funcionais_consequentes", [])):
        add_edge({
            "id_aresta": rfc.get("id_aresta", f"rfc_edge_{rfc_idx}"),
            "id_origem_no": rfc.get("id_origem_no"),
            "id_destino_no": rfc.get("id_destino_no"),
            "label": f"Consequente: {rfc.get('funcao_consequente', 'N/A')}",
            "title": f"ID Aresta: {rfc.get('id_aresta', f'rfc_edge_{rfc_idx}').replace('_', ' ').title()}\nFunção: {rfc.get('funcao_consequente', 'N/A')}\nImediatismo: {rfc.get('imediatismo_consequencia', 'N/A')}",
            "color": {"color": "#FF6347", "highlight": "#E05135", "hover": "#E05135"}
        }, "consequente")

    # Processar Evidências para Hipóteses
    for eph_idx, eph in enumerate(json_data.get("evidencias_para_hipoteses", [])):
        add_edge({
            "id_aresta": eph.get("id_aresta", f"eph_edge_{eph_idx}"),
            "id_origem_no": eph.get("id_origem_no"),
            "id_destino_no": eph.get("id_destino_no"),
            "label": eph.get("tipo_evidencia", "Evidência"),
            "title": f"ID Aresta: {eph.get('id_aresta', f'eph_edge_{eph_idx}').replace('_', ' ').title()}\nTipo: {eph.get('tipo_evidencia', 'N/A')}\nFonte: {eph.get('fonte_dados', 'N/A')}\nElementos Suporte: {', '.join(eph.get('ids_elementos_contingencia_suporte', []))}",
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
