SYSTEM_PROMPT = """
Você é um assistente especializado em Análise do Comportamento. Sua tarefa é aplicar um procedimento metodológico para extrair e estruturar informações de um texto narrativo ou descritivo, transformando-o em uma representação de rede contingencial.

Esta rede é composta por Nós (objetos da análise: Sujeitos, Estímulos_Evento, Acoes_Comportamento, Condicoes_Estado, Hipoteses_Analiticas) e Arestas (relações funcionais e temporais entre os nós).

Você receberá instruções para focar em etapas específicas do procedimento e gerar apenas as partes do JSON correspondentes a essas etapas. Use os IDs dos nós e arestas de forma consistente e incremental (S1, S2, E1, E2, AC1, AR1, etc.). Gere `data_formulacao` para Hipoteses_Analiticas com a data e hora atuais no formato ISO (YYYY-MM-DDTHH:MM:SS.ffffff).

Se um ID fornecido no contexto já existir e você estiver descrevendo o mesmo elemento, reutilize esse ID para indicar uma atualização. Se for um novo elemento, crie um novo ID.

Se informações cruciais não estiverem explícitas no texto, você pode fazer inferências cautelosas, mas deve indicar o nível de inferência ou a fonte da informação nos atributos apropriados. Se uma informação for ambígua, registre a ambiguidade.
Certifique-se de que o JSON de saída para cada chamada seja um objeto único contendo APENAS as listas de nós e arestas relevantes para as etapas solicitadas nessa chamada. O JSON deve começar com '{' e terminar com '}'. Não adicione nenhum texto explicativo antes ou depois do JSON.
"""

PROCEDIMENTO_COMPLETO_AFC = """
### Conceitos Fundamentais da Análise Funcional do Comportamento (AFC)

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

### Procedimento de Extração de Nós e Arestas

Com base no texto narrativo fornecido, siga as etapas abaixo para construir a rede contingencial.

**Etapa 1: Leitura Inicial e Identificação de Entidades Centrais**
* **Objetivo:** Identificar os atores principais e suas ações mais evidentes.
* **1.1: Identificar `Sujeito(s)`:**
    * Localize os indivíduos centrais na narrativa.
    * Para cada um, crie um **Nó `Sujeito`** e preencha seus atributos (`id_sujeito`, `nome_descritivo`, `idade`, `historico_relevante`, `especie`, `observacoes_adicionais`).
* **1.2: Identificar `Acao_Comportamento(s)` Principais:**
    * Liste as ações ou comportamentos emitidos pelo(s) `Sujeito(s)`.
    * Para cada ação, crie um **Nó `Acao_Comportamento`** e preencha seus atributos (`id_acao`, `descricao_topografica`, `tipo_observabilidade`, `frequencia_base_periodo`, `duracao_media_seg`, `intensidade_media`, `latencia_tipica_resposta_seg`, `classe_funcional_hipotetica`, `observacoes_adicionais`).
    * Crie uma **Aresta `Emissao_Comportamental`** (com `id`, `id_origem_no` = ID do Sujeito, `id_destino_no` = ID da Acao_Comportamento, `data_hora_especifica_emissao`, `observacoes_adicionais`).

**Etapa 2: Mapeamento de `Estímulos_Evento` Imediatamente Associados às `Acoes_Comportamento`**
* **Objetivo:** Identificar eventos que ocorrem imediatamente antes e depois das ações.
* **2.1: Identificar Antecedentes Imediatos:**
    * Para cada `Acao_Comportamento`, identifique eventos/objetos/ações de outros que ocorreram logo antes.
    * Crie **Nós `Estímulo_Evento`** para esses antecedentes e preencha seus atributos (`id_estimulo_evento`, `descricao`, `tipo_fisico`, `modalidade_sensorial_primaria`, `intensidade_percebida_inicial`, `duracao_estimulo_evento_seg`, `localizacao`, `data_hora_ocorrencia`, `observacoes_adicionais`).
    * Crie uma **Aresta `Relacao_Temporal`** (com `id`, `id_origem_no` = ID do Estímulo_Evento antecedente, `id_destino_no` = ID da Acao_Comportamento, `tipo_temporalidade = "PRECEDE_IMEDIATAMENTE"`, `intervalo_atraso_seg`, `contiguidade_percebida`, `observacoes_adicionais`).
* **2.2: Identificar Consequências Imediatas:**
    * Para cada `Acao_Comportamento`, identifique eventos/objetos/ações de outros que ocorreram logo depois.
    * Crie **Nós `Estímulo_Evento`** para essas consequências e preencha seus atributos.
    * Crie uma **Aresta `Relacao_Temporal`** (com `id`, `id_origem_no` = ID da Acao_Comportamento, `id_destino_no` = ID do Estímulo_Evento consequente, `tipo_temporalidade = "SUCEDE_IMEDIATAMENTE"`, `intervalo_atraso_seg`, `contiguidade_percebida`, `observacoes_adicionais`).

**Etapa 3: Estabelecimento de Sequências Contingenciais Básicas (Cadeias A-B-C)**
* **Objetivo:** Formar as unidades básicas da análise (Antecedente-Comportamento-Consequência).
* **3.1: Formar Tríades A-B-C:**
    * Crie **Arestas `Relacao_Funcional_Antecedente`** (com `id`, `id_origem_no` = ID do Estímulo_Evento antecedente, `id_destino_no` = ID da Acao_Comportamento, `funcao_antecedente` - pode ser "A_DEFINIR" inicialmente, `prob_resposta_na_presenca`, `prob_resposta_na_ausencia`, `historico_pareamento`, `observacoes_adicionais`).
    * Crie **Arestas `Relacao_Funcional_Consequente`** (com `id`, `id_origem_no` = ID da Acao_Comportamento, `id_destino_no` = ID do Estímulo_Evento consequente, `funcao_consequente` - pode ser "A_DEFINIR" inicialmente, `imediatismo_consequencia`, `magnitude_consequencia`, `esquema_de_entrega`, `parametro_esquema`, `efeito_observado_na_frequencia_futura`, `observacoes_adicionais`).
* **3.2: Identificar Cadeias Comportamentais:**
    * Observe se a consequência de uma A-B-C serve como antecedente para a próxima.

**Etapa 4: Identificação de `Condicoes_Estado` (Moduladores)**
* **Objetivo:** Identificar contextos mais amplos, estados do sujeito ou OMs que influenciam as relações A-B-C.
* **4.1: Identificar Operações Motivadoras (OMs):**
    * Procure menções a privação, saciação, eventos aversivos antecedentes.
    * Crie **Nós `Condicao_Estado`** e preencha `id_condicao_estado`, `descricao`, `tipo_condicao = "Operação Motivadora"`, `duracao_condicao_desc`, `data_hora_inicio`, `observacoes_adicionais`).
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
    * Crie **Arestas `Relacao_Moduladora_Estado`** (com `id`, `id_origem_no` = ID da Condicao_Estado, `id_destino_no` = ID do Nó modulado) entre as `Condicoes_Estado` e os `Estímulos_Evento` ou `Acoes_Comportamento` que elas modulam.
    * Preencha os atributos da aresta (`tipo_modulacao_estado`, `alvo_da_modulacao_valor_ref_id_estimulo`, `descricao_efeito_modulatorio_valor`, `alvo_da_modulacao_frequencia_ref_id_acao`, `descricao_efeito_modulatorio_frequencia`, `observacoes_adicionais`).

**Etapa 6: Formulação e Adição de Nós `Hipotese_Analitica`**
* **Objetivo:** Formular hipóteses sobre as funções do comportamento com base na análise.
* **Como:** Para cada função comportamental principal inferida ou conjunto significativo de relações A-B-C-OM, formule uma declaração de hipótese.
* **Saída:**
    * Crie **Nós `Hipotese_Analitica`** e preencha seus atributos (`id_hipotese`, `descricao_hipotese`, `nivel_confianca`, `data_formulacao` - use a data e hora atuais no formato ISO, `status_hipotese`, `observacoes_adicionais`).
    * Crie **Arestas `Evidencia_Para_Hipotese`** (com `id`, `id_origem_no` - pode ser o ID da Acao_Comportamento central da hipótese, `id_destino_no` = ID da Hipotese_Analitica, `ids_elementos_contingencia_suporte` - lista de IDs de Nós e Arestas que suportam a hipótese, `tipo_evidencia`, `fonte_dados = "Narrativa Textual"`, `observacoes_adicionais`).
"""

FOCO_ETAPA_SUJEITOS = (
    "FOCO DESTA ETAPA: Identifique os sujeitos (indivíduos, animais) principais na narrativa. "
    "Para cada sujeito, gere um objeto com `id` (S1, S2...) e `descricao` (ambos obrigatórios). "
    "A saída JSON DEVE ser um objeto com a chave principal 'sujeitos' contendo uma lista de objetos `NoSujeito`. "
    "Inclua o campo `raciocinio` no objeto JSON de nível superior, descrevendo a lógica para a extração nesta etapa."
    "\nReferência no Procedimento: Etapa 1.1."
)

FOCO_ETAPA_ACOES = (
    "FOCO DESTA ETAPA: Para cada sujeito identificado no contexto, liste as principais ações ou comportamentos que eles emitem. "
    "Gere um Nó `Acao_Comportamento` para cada ação (com `id` e `descricao` obrigatórios). "
    "Crie também uma Aresta `Emissao_Comportamental` (com `id`, `id_origem_no` = ID do Sujeito, `id_destino_no` = ID da Acao_Comportamento, todos obrigatórios). "
    "A saída JSON DEVE ser um objeto com as chaves principais 'acoes_comportamentos' e 'emissoes_comportamentais' contendo listas de objetos `NoAcaoComportamento` e `ArestaEmissaoComportamental` respectivamente. "
    "Inclua o campo `raciocinio` no objeto JSON de nível superior, descrevendo a lógica para a extração nesta etapa. "
    "Ao identificar elementos que já podem existir no `Contexto da rede atual`, reutilize seus IDs (`id`, `id_acao`, etc.) em vez de criar novos, a menos que seja um elemento distinto."
    "\nReferência no Procedimento: Etapa 1.2."
)

FOCO_ETAPA_EVENTOS_TEMPORAIS = (
    "FOCO DESTA ETAPA: Para cada `Acao_Comportamento` identificada no contexto, identifique `Estímulos_Evento` (E1, E2...) e outros `Acao_Comportamento` que *precedem* (antecedentes) e que *procedem* (consequentes) a tal `Acao_Comportamento`. "
    "Nenhum `Acao_Comportamento` deve ser deixado sem pelo menos um `Estímulos_Evento` antecedente e um consequente. Busque associá-los primeiro com os nós, mas caso não sejam suficientes extraia ou deduza novos."
    "Comece descrevendo `Estímulos_Evento` antecedentes e consequentes para cada `Acao_Comportamento`. A seguir, crie `ArestasRelacaoTemporal` (RT1, RT2...) indicando se o estímulo `PRECEDE_IMEDIATAMENTE` a ação ou se a ação `SUCEDE_IMEDIATAMENTE` o estímulo. "
    "Para cada `NoEstimuloEvento`, forneça `id` e `descricao` (ambos obrigatórios). "
    "Para cada `ArestaRelacaoTemporal`, forneça `id`, `id_origem_no`, `id_destino_no`, e `tipo_temporalidade` (todos obrigatórios). "
    "A saída JSON DEVE ser um objeto com as chaves principais 'estimulos_eventos' e 'relacoes_temporais' contendo listas de objetos `NoEstimuloEvento` e `ArestaRelacaoTemporal` respectivamente. "
    "Inclua o campo `raciocinio` no objeto JSON de nível superior, descrevendo a lógica para a extração nesta etapa. "
    "Ao identificar elementos que já podem existir no `Contexto da rede atual`, reutilize seus IDs (`id`, `id_acao`, etc.) em vez de criar novos, a menos que seja um elemento distinto."
    "Use os IDs das ações do contexto."
    "\nReferência no Procedimento: Etapas 2.1 e 2.2."
)

FOCO_ETAPA_FUNCIONAIS_ANTECEDENTES = (
    "FOCO DESTA ETAPA: Considerando os `Estímulos_Evento` que, de acordo com as `Relacoes_Temporais`, precedem imediatamente as `Acoes_Comportamento` (ambos fornecidos no contexto), "
    "infira a `funcao_antecedente` (e.g., ESTÍMULO_DISCRIMINATIVO_SD, ESTÍMULO_ELICIADOR_CONDICIONADO_CS) de cada estímulo em relação à ação que ele precede. "
    "Crie `ArestasRelacaoFuncionalAntecedente` (RFA1, RFA2...). "
    "Para cada `ArestaRelacaoFuncionalAntecedente`, forneça `id`, `id_origem_no`, `id_destino_no`, e `funcao_antecedente` (todos obrigatórios). "
    "A saída JSON DEVE ser um objeto com a chave principal 'relacoes_funcionais_antecedentes' contendo uma lista de objetos `ArestaRelacaoFuncionalAntecedente`. "
    "Inclua o campo `raciocinio` no objeto JSON de nível superior, descrevendo a lógica para a extração nesta etapa. "
    "Ao identificar elementos que já podem existir no `Contexto da rede atual`, reutilize seus IDs (`id`, `id_acao`, etc.) em vez de criar novos, a menos que seja um elemento distinto."
    "Use os IDs dos estímulos e ações do contexto."
    "\nReferência no Procedimento: Etapa 3.1 (parte antecedente)."
)

FOCO_ETAPA_FUNCIONAIS_CONSEQUENTES = (
    "FOCO DESTA ETAPA: Considerando as `Acoes_Comportamento` e os `Estímulos_Evento` que, de acordo com as `Relacoes_Temporais`, as sucedem imediatamente (ambos fornecidos no contexto), "
    "infira a `funcao_consequente` (e.g., REFORÇO_POSITIVO_SR+, PUNIÇÃO_NEGATIVA_SP-) de cada estímulo em relação à ação que ele sucede. "
    "Crie `ArestasRelacaoFuncionalConsequente` (RFC1, RFC2...). "
    "Para cada `ArestaRelacaoFuncionalConsequente`, forneça `id`, `id_origem_no`, `id_destino_no`, e `funcao_consequente` (todos obrigatórios). "
    "A saída JSON DEVE ser um objeto com a chave principal 'relacoes_funcionais_consequentes' contendo uma lista de objetos `ArestaRelacaoFuncionalConsequente`. "
    "Inclua o campo `raciocinio` no objeto JSON de nível superior, descrevendo a lógica para a extração nesta etapa. "
    "Ao identificar elementos que já podem existir no `Contexto da rede atual`, reutilize seus IDs (`id`, `id_acao`, etc.) em vez de criar novos, a menos que seja um elemento distinto."
    "Use os IDs das ações e estímulos do contexto."
    "\nReferência no Procedimento: Etapa 3.1 (parte consequente)."
)

FOCO_ETAPA_CONDICOES_ESTADO = (
    "FOCO DESTA ETAPA: Identifique `Condicoes_Estado` (CE1, CE2...) descritas na narrativa que podem estar influenciando os comportamentos e suas relações com antecedentes e consequentes. "
    "Classifique-as conforme o `tipo_condicao` (e.g., OPERACAO_MOTIVADORA, CONTEXTO_AMBIENTAL_GERAL, ESTADO_FISIOLOGICO). "
    "Forneça `id` (obrigatório), `descricao` (obrigatório) e `tipo_condicao` (obrigatório). "
    "A saída JSON DEVE ser um objeto com a chave principal 'condicoes_estados' contendo uma lista de objetos `NoCondicaoEstado`. "
    "Inclua o campo `raciocinio` no objeto JSON de nível superior, descrevendo a lógica para a extração nesta etapa. "
    "Ao identificar elementos que já podem existir no `Contexto da rede atual`, reutilize seus IDs (`id`, `id_acao`, etc.) em vez de criar novos, a menos que seja um elemento distinto."
    "\nReferência no Procedimento: Etapa 4."
)

FOCO_ETAPA_RELACOES_MODULADORAS = (
    "FOCO DESTA ETAPA: Para cada `Condicao_Estado` identificada no contexto (IDs: [CE1, CE2...]), determine como ela modula a rede. "
    "Ela altera o valor de um `Estímulo_Evento` consequente (referência `alvo_da_modulacao_valor_ref_id_estimulo`)? "
    "Ela altera a frequência de uma `Acao_Comportamento` (referência `alvo_da_modulacao_frequencia_ref_id_acao`)? "
    "Descreva o `tipo_modulacao_estado` e crie `ArestasRelacaoModuladoraEstado` (RME1, RME2...). "
    "Para cada `ArestaRelacaoModuladoraEstado`, forneça `id`, `id_origem_no`, `id_destino_no`, e `tipo_modulacao_estado` (todos obrigatórios). "
    "A saída JSON DEVE ser um objeto com a chave principal 'relacoes_moduladoras_estado' contendo uma lista de objetos `ArestaRelacaoModuladoraEstado`. "
    "Inclua o campo `raciocinio` no objeto JSON de nível superior, descrevendo a lógica para a extração nesta etapa. "
    "Ao identificar elementos que já podem existir no `Contexto da rede atual`, reutilize seus IDs (`id`, `id_acao`, etc.) em vez de criar novos, a menos que seja um elemento distinto."
    "Use os IDs dos elementos do contexto."
    "\nReferência no Procedimento: Etapa 5.3."
)

FOCO_ETAPA_HIPOTESES = (
    "FOCO DESTA ETAPA: Com base na análise completa da rede fornecida no contexto, formule `Hipoteses_Analiticas` (H1, H2...) sobre as principais funções dos comportamentos identificados. "
    "Para cada hipótese, forneça `id` (obrigatório), `descricao` (obrigatório) e `nivel_confianca` (obrigatório). "
    "Crie também uma `ArestaEvidenciaParaHipotese` (EH1, EH2...) que a ligue ao `Acao_Comportamento` central da hipótese (origem da aresta = ID da Ação) e à Hipótese (destino da aresta = ID da Hipótese). "
    "Para cada `ArestaEvidenciaParaHipotese`, forneça `id`, `id_origem_no`, `id_destino_no`, `ids_elementos_contingencia_suporte`, e `tipo_evidencia` (todos obrigatórios). "
    "Liste os `ids_elementos_contingencia_suporte` (outros nós e arestas da rede que evidenciam essa hipótese)."
    "A saída JSON DEVE ser um objeto com as chaves principais 'hipoteses_analiticas' e 'evidencias_para_hipoteses' contendo listas de objetos `NoHipoteseAnalitica` e `ArestaEvidenciaParaHipotese` respectivamente. "
    "Inclua o campo `raciocinio` no objeto JSON de nível superior, descrevendo a lógica para a extração nesta etapa. "
    "Ao identificar elementos que já podem existir no `Contexto da rede atual`, reutilize seus IDs (`id`, `id_acao`, etc.) em vez de criar novos, a menos que seja um elemento distinto."
    "\nReferência no Procedimento: Etapa 6."
)

FOCO_ETAPA_TIMELINE = (
    "FOCO DESTA ETAPA: Ordenar todos os objetos no CONTEXTO DA REDE de acordo com sua aparição no texto narrativo."
    "Cada objeto deve ser identificado pelo seu ID e aparecer na lista apenas uma vez."
    "Todos os nós devem estar na lista final."
    "A saída JSON DEVE ser um objeto com a chave principal 'timeline' contendo uma lista de strings (IDs dos nós)."
    "Inclua o campo `raciocinio` no objeto JSON de nível superior, descrevendo a lógica para a extração nesta etapa. "
    "Ao identificar elementos que já podem existir no `Contexto da rede atual`, reutilize seus IDs (`id`, `id_acao`, etc.) em vez de criar novos, a menos que seja um elemento distinto."
)

PROCEDIMENTO_COMPLETO_AFC = """
### Conceitos Fundamentais da Análise Funcional do Comportamento (AFC)

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

### Procedimento de Extração de Nós e Arestas

Com base no texto narrativo fornecido, siga as etapas abaixo para construir a rede contingencial.

**Etapa 1: Leitura Inicial e Identificação de Entidades Centrais**
* **Objetivo:** Identificar os atores principais e suas ações mais evidentes.
* **1.1: Identificar `Sujeito(s)`:**
    * Localize os indivíduos centrais na narrativa.
    * Para cada um, crie um **Nó `Sujeito`** e preencha seus atributos (`id_sujeito`, `nome_descritivo`, `idade`, `historico_relevante`, `especie`, `observacoes_adicionais`).
* **1.2: Identificar `Acao_Comportamento(s)` Principais:**
    * Liste as ações ou comportamentos emitidos pelo(s) `Sujeito(s)`.
    * Para cada ação, crie um **Nó `Acao_Comportamento`** e preencha seus atributos (`id_acao`, `descricao_topografica`, `tipo_observabilidade`, `frequencia_base_periodo`, `duracao_media_seg`, `intensidade_media`, `latencia_tipica_resposta_seg`, `classe_funcional_hipotetica`, `observacoes_adicionais`).
    * Crie uma **Aresta `Emissao_Comportamental`** (com `id`, `id_origem_no` = ID do Sujeito, `id_destino_no` = ID da Acao_Comportamento, `data_hora_especifica_emissao`, `observacoes_adicionais`).

**Etapa 2: Mapeamento de `Estímulos_Evento` Imediatamente Associados às `Acoes_Comportamento`**
* **Objetivo:** Identificar eventos que ocorrem imediatamente antes e depois das ações.
* **2.1: Identificar Antecedentes Imediatos:**
    * Para cada `Acao_Comportamento`, identifique eventos/objetos/ações de outros que ocorreram logo antes.
    * Crie **Nós `Estímulo_Evento`** para esses antecedentes e preencha seus atributos (`id_estimulo_evento`, `descricao`, `tipo_fisico`, `modalidade_sensorial_primaria`, `intensidade_percebida_inicial`, `duracao_estimulo_evento_seg`, `localizacao`, `data_hora_ocorrencia`, `observacoes_adicionais`).
    * Crie uma **Aresta `Relacao_Temporal`** (com `id`, `id_origem_no` = ID do Estímulo_Evento antecedente, `id_destino_no` = ID da Acao_Comportamento, `tipo_temporalidade = "PRECEDE_IMEDIATAMENTE"`, `intervalo_atraso_seg`, `contiguidade_percebida`, `observacoes_adicionais`).
* **2.2: Identificar Consequências Imediatas:**
    * Para cada `Acao_Comportamento`, identifique eventos/objetos/ações de outros que ocorreram logo depois.
    * Crie **Nós `Estímulo_Evento`** para essas consequências e preencha seus atributos.
    * Crie uma **Aresta `Relacao_Temporal`** (com `id`, `id_origem_no` = ID da Acao_Comportamento, `id_destino_no` = ID do Estímulo_Evento consequente, `tipo_temporalidade = "SUCEDE_IMEDIATAMENTE"`, `intervalo_atraso_seg`, `contiguidade_percebida`, `observacoes_adicionais`).

**Etapa 3: Estabelecimento de Sequências Contingenciais Básicas (Cadeias A-B-C)**
* **Objetivo:** Formar as unidades básicas da análise (Antecedente-Comportamento-Consequência).
* **3.1: Formar Tríades A-B-C:**
    * Crie **Arestas `Relacao_Funcional_Antecedente`** (com `id`, `id_origem_no` = ID do Estímulo_Evento antecedente, `id_destino_no` = ID da Acao_Comportamento, `funcao_antecedente` - pode ser "A_DEFINIR" inicialmente, `prob_resposta_na_presenca`, `prob_resposta_na_ausencia`, `historico_pareamento`, `observacoes_adicionais`).
    * Crie **Arestas `Relacao_Funcional_Consequente`** (com `id`, `id_origem_no` = ID da Acao_Comportamento, `id_destino_no` = ID do Estímulo_Evento consequente, `funcao_consequente` - pode ser "A_DEFINIR" inicialmente, `imediatismo_consequencia`, `magnitude_consequencia`, `esquema_de_entrega`, `parametro_esquema`, `efeito_observado_na_frequencia_futura`, `observacoes_adicionais`).
* **3.2: Identificar Cadeias Comportamentais:**
    * Observe se a consequência de uma A-B-C serve como antecedente para a próxima.

**Etapa 4: Identificação de `Condicoes_Estado` (Moduladores)**
* **Objetivo:** Identificar contextos mais amplos, estados do sujeito ou OMs que influenciam as relações A-B-C.
* **4.1: Identificar Operações Motivadoras (OMs):**
    * Procure menções a privação, saciação, eventos aversivos antecedentes.
    * Crie **Nós `Condicao_Estado`** e preencha `id_condicao_estado`, `descricao`, `tipo_condicao = "Operação Motivadora"`, `duracao_condicao_desc`, `data_hora_inicio`, `observacoes_adicionais`).
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
    * Crie **Arestas `Relacao_Moduladora_Estado`** (com `id`, `id_origem_no` = ID da Condicao_Estado, `id_destino_no` = ID do Nó modulado) entre as `Condicoes_Estado` e os `Estímulos_Evento` ou `Acoes_Comportamento` que elas modulam.
    * Preencha os atributos da aresta (`tipo_modulacao_estado`, `alvo_da_modulacao_valor_ref_id_estimulo`, `descricao_efeito_modulatorio_valor`, `alvo_da_modulacao_frequencia_ref_id_acao`, `descricao_efeito_modulatorio_frequencia`, `observacoes_adicionais`).

**Etapa 6: Formulação e Adição de Nós `Hipotese_Analitica`**
* **Objetivo:** Formular hipóteses sobre as funções do comportamento com base na análise.
* **Como:** Para cada função comportamental principal inferida ou conjunto significativo de relações A-B-C-OM, formule uma declaração de hipótese.
* **Saída:**
    * Crie **Nós `Hipotese_Analitica`** e preencha seus atributos (`id_hipotese`, `descricao_hipotese`, `nivel_confianca`, `data_formulacao` - use a data e hora atuais no formato ISO, `status_hipotese`, `observacoes_adicionais`).
    * Crie **Arestas `Evidencia_Para_Hipotese`** (com `id`, `id_origem_no` - pode ser o ID da Acao_Comportamento central da hipótese, `id_destino_no` = ID da Hipotese_Analitica, `ids_elementos_contingencia_suporte` - lista de IDs de Nós e Arestas que suportam a hipótese, `tipo_evidencia`, `fonte_dados = "Narrativa Textual"`, `observacoes_adicionais`).
"""
