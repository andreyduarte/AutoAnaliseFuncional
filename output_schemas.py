from typing import List, Optional, Union, Literal, Dict, Any, cast
from pydantic import BaseModel, Field, ValidationError # type: ignore
from enum import Enum # Corrigido de pydantic.types import Enum
import datetime

# --- Enumerações para Tipos (Pydantic Models) ---

class TipoEstimuloEventoFisico(str, Enum):
    SOCIAL = "Social"
    NAO_SOCIAL = "Não-Social"
    VERBAL = "Verbal"
    NAO_VERBAL = "Não-Verbal"
    INTEROCEPTIVO = "Interoceptivo"
    PROPRIOCEPTIVO = "Proprioceptivo"
    MISTO = "Misto"

class TipoModalidadeSensorial(str, Enum):
    VISUAL = "Visual"
    AUDITIVO = "Auditivo"
    TATIL = "Tátil"
    OLFATIVO = "Olfativo"
    GUSTATIVO = "Gustativo"
    INTEROCEPTIVO = "Interoceptivo"
    PROPRIOCEPTIVO = "Proprioceptivo"
    MISTO = "Misto"
    NENHUMA_APLICAVEL = "Nenhuma Aplicável"

class TipoObservabilidadeAcao(str, Enum):
    PUBLICO_OBSERVAVEL = "Observável"
    PRIVADO_ENCOBERTO = "Encoberto"

class TipoCondicao(str, Enum):
    OPERACAO_MOTIVADORA = "Operação Motivadora"
    CONTEXTO_AMBIENTAL_GERAL = "Contexto Ambiental Geral"
    ESTADO_FISIOLOGICO = "Estado Fisiológico"
    ESTADO_EMOCIONAL_DURADOURO = "Estado Emocional Duradouro"

class NivelConfiancaHipotese(str, Enum):
    BAIXO = "Baixo"
    MEDIO = "Médio"
    ALTO = "Alto"

class StatusHipotese(str, Enum):
    AGUARDANDO_TESTE = "Aguardando teste"
    SUPORTADA_POR_DADOS = "Suportada por dados"
    REFUTADA_POR_DADOS = "Refutada por dados"
    MODIFICADA = "Modificada"

class TipoTemporalidade(str, Enum):
    PRECEDE_IMEDIATAMENTE = "PRECEDE_IMEDIATAMENTE"
    PRECEDE_COM_ATRASO = "PRECEDE_COM_ATRASO"
    COOCORRE = "COOCORRE"
    SUCEDE_IMEDIATAMENTE = "SUCEDE_IMEDIATAMENTE"
    SUCEDE_COM_ATRASO = "SUCEDE_COM_ATRASO"

class FuncaoAntecedente(str, Enum):
    ESTIMULO_DISCRIMINATIVO_SD = "ESTÍMULO_DISCRIMINATIVO_SD"
    ESTIMULO_DELTA_SDELTA = "ESTÍMULO_DELTA_SDELTA"
    ESTIMULO_CONDICIONAL_SCS = "ESTÍMULO_CONDICIONAL_SCS"
    ESTIMULO_NEUTRO_SN = "ESTÍMULO_NEUTRO_SN"
    ESTIMULO_ELICIADOR_INCONDICIONADO_US = "ESTÍMULO_ELICIADOR_INCONDICIONADO_US"
    ESTIMULO_ELICIADOR_CONDICIONADO_CS = "ESTÍMULO_ELICIADOR_CONDICIONADO_CS"
    A_DEFINIR = "A_DEFINIR"

class FuncaoConsequente(str, Enum):
    REFORCO_POSITIVO_SR_MAIS = "REFORÇO_POSITIVO_SR+"
    REFORCO_NEGATIVO_SR_MENOS = "REFORÇO_NEGATIVO_SR-"
    PUNICAO_POSITIVA_SP_MAIS = "PUNIÇÃO_POSITIVA_SP+"
    PUNICAO_NEGATIVA_SP_MENOS = "PUNIÇÃO_NEGATIVA_SP-"
    EXTINCAO_EXT = "EXTINÇÃO_EXT"
    SEM_CONSEQUENCIA_PROGRAMADA_OU_IDENTIFICADA = "SEM_CONSEQUENCIA_PROGRAMADA_OU_IDENTIFICADA"
    A_DEFINIR = "A_DEFINIR"

class ImediatismoConsequencia(str, Enum):
    IMEDIATA = "Imediata"
    ATRASADA = "Atrasada"

class EsquemaDeEntrega(str, Enum):
    CONTINUO_CRF = "Contínuo_CRF"
    INTERMITENTE_FR = "Intermitente_FR"
    INTERMITENTE_VR = "Intermitente_VR"
    INTERMITENTE_FI = "Intermitente_FI"
    INTERMITENTE_VI = "Intermitente_VI"
    DRL = "DRL"
    DRO = "DRO"
    DRA = "DRA"
    DRI = "DRI"
    OUTRO = "Outro"
    NAO_APLICAVEL = "Não Aplicável"
    DESCONHECIDO = "Desconhecido"

class EfeitoObservadoFrequencia(str, Enum):
    AUMENTO = "Aumento"
    DIMINUICAO = "Diminuição"
    MANUTENCAO = "Manutenção"
    SEM_EFEITO_APARENTE = "Sem efeito aparente"
    VARIABILIDADE = "Variabilidade"
    A_INVESTIGAR = "A investigar"

class TipoModulacaoEstado(str, Enum):
    OPERACAO_MOTIVADORA_ESTABELECEDORA_OE = "OPERAÇÃO_MOTIVADORA_ESTABELECEDORA_OE"
    OPERACAO_MOTIVADORA_ABOLIDORA_OA = "OPERAÇÃO_MOTIVADORA_ABOLIDORA_OA"
    CONTEXTO_FACILITADOR = "CONTEXTO_FACILITADOR"
    CONTEXTO_INIBIDOR = "CONTEXTO_INIBIDOR"
    ESTADO_AUMENTA_SENSIBILIDADE_A_REFORCO = "ESTADO_AUMENTA_SENSIBILIDADE_A_REFORÇO"
    ESTADO_DIMINUI_SENSIBILIDADE_A_PUNICAO = "ESTADO_DIMINUI_SENSIBILIDADE_A_PUNIÇÃO"
    OUTRO = "Outro"

class TipoEvidenciaHipotese(str, Enum):
    SUPORTE_DIRETO = "SUPORTE_DIRETO"
    SUPORTE_INDIRETO = "SUPORTE_INDIRETO"
    CONTRADICAO_PARCIAL = "CONTRADICAO_PARCIAL"
    CONTRADICAO_FORTE = "CONTRADICAO_FORTE"

class FonteDadosEvidencia(str, Enum):
    NARRATIVA_TEXTUAL = "Narrativa Textual"
    OBSERVACAO_DIRETA_DESCRITIVA = "Observação Direta Descritiva"
    ENTREVISTA = "Entrevista"
    QUESTIONARIO = "Questionário"
    ANALISE_FUNCIONAL_EXPERIMENTAL = "Análise Funcional Experimental"

# --- Modelos de Nós ---

class NoBase(BaseModel):
    id: str
    raciocinio:str = Field(..., description="A lógica que justifica a inserção do nó e sua relevância pra análise.")

class NoSujeito(NoBase):
    id: str = Field(..., description="Identificador único do sujeito (e.g., S1, S2).")
    descricao: str = Field(None, description="Nome ou descrição curta do sujeito (e.g., 'João', 'Criança A').")
    historico_relevante: Optional[str] = Field(None, description="Breve resumo de informações contextuais importantes.")

class NoEstimuloEvento(NoBase):
    id: str = Field(..., description="Identificador único do estímulo/evento (e.g., E1, E2).")
    descricao: str = Field(..., description="Descrição textual objetiva do estímulo/evento.")

class NoAcaoComportamento(NoBase):
    id: str = Field(..., description="Identificador único da ação/comportamento (e.g., AC1, AC2).")
    descricao: str = Field(..., description="Descrição objetiva e mensurável da forma da ação.")
    tipo_observabilidade: Optional[TipoObservabilidadeAcao] = None
    classe_funcional_hipotetica: Optional[List[str]] = Field(None, description="Possíveis funções inferidas (e.g., ['Busca de atenção', 'Fuga de tarefa']).")

class NoCondicaoEstado(NoBase):
    id: str = Field(..., description="Identificador único da condição/estado (e.g., CE1, CE2).")
    descricao: str = Field(..., description="Descrição da condição/estado.")
    tipo_condicao: Optional[TipoCondicao] = None
    duracao_condicao_desc: Optional[str] = Field(None, description="Descrição da duração, e.g., 'aproximadamente 2 horas', 'durante a aula'.")

class NoHipoteseAnalitica(NoBase):
    id: str = Field(..., description="Identificador único da hipótese (e.g., H1, H2).")
    descricao: str = Field(..., description="Texto da hipótese funcional.")
    nivel_confianca: Optional[NivelConfiancaHipotese] = NivelConfiancaHipotese.BAIXO

# --- Modelos de Arestas ---
class ArestaBase(BaseModel):
    id: str = Field(..., description="Identificador único da aresta (e.g., AR1, AR2).")
    id_origem_no: str = Field(..., description="ID do nó de origem.")
    id_destino_no: str = Field(..., description="ID do nó de destino.")
    raciocinio:str = Field(..., description="A lógica que justifica a inserção da aresta e sua relevância pra análise.")

class ArestaEmissaoComportamental(ArestaBase):
    tipo_aresta: Literal["EMISSAO_COMPORTAMENTAL"] = "EMISSAO_COMPORTAMENTAL"

class ArestaRelacaoTemporal(ArestaBase):
    tipo_aresta: Literal["RELACAO_TEMPORAL"] = "RELACAO_TEMPORAL"
    tipo_temporalidade: TipoTemporalidade
    contiguidade_percebida: Optional[str] = Field(None, description="Alta, Média, Baixa.")

class ArestaRelacaoFuncionalAntecedente(ArestaBase):
    tipo_aresta: Literal["RELACAO_FUNCIONAL_ANTECEDENTE"] = "RELACAO_FUNCIONAL_ANTECEDENTE"
    funcao_antecedente: FuncaoAntecedente
    prob_resposta_na_presenca: Optional[float] = Field(None, ge=0, le=1)
    prob_resposta_na_ausencia: Optional[float] = Field(None, ge=0, le=1)

class ArestaRelacaoFuncionalConsequente(ArestaBase):
    tipo_aresta: Literal["RELACAO_FUNCIONAL_CONSEQUENTE"] = "RELACAO_FUNCIONAL_CONSEQUENTE"
    funcao_consequente: FuncaoConsequente
    imediatismo_consequencia: Optional[ImediatismoConsequencia] = None
    magnitude_consequencia: Optional[str] = Field(None, description="Baixa, Média, Alta, ou escala.")
    parametro_esquema: Optional[Union[int, str]] = Field(None, description="e.g., Se FR, o número de respostas.")

class ArestaRelacaoModuladoraEstado(ArestaBase):
    tipo_aresta: Literal["RELACAO_MODULADORA_ESTADO"] = "RELACAO_MODULADORA_ESTADO"
    tipo_modulacao_estado: TipoModulacaoEstado
    alvo_da_modulacao_valor_ref_id_estimulo: Optional[str] = Field(None, description="ID do Estímulo_Evento consequente cujo valor é alterado.")
    descricao_efeito_modulatorio_valor: Optional[str] = Field(None, description="e.g., 'Aumenta valor reforçador de X'.")
    alvo_da_modulacao_frequencia_ref_id_acao: Optional[str] = Field(None, description="ID da Acao_Comportamento cuja frequência é alterada.")
    descricao_efeito_modulatorio_frequencia: Optional[str] = Field(None, description="e.g., 'Aumenta frequência de Y'.")

class ArestaEvidenciaParaHipotese(ArestaBase):
    tipo_aresta: Literal["EVIDENCIA_PARA_HIPOTESE"] = "EVIDENCIA_PARA_HIPOTESE"
    ids_elementos_contingencia_suporte: List[str] = Field(..., description="Lista de IDs de Nós e Arestas que formam a contingência que suporta/refuta a hipótese.")
    tipo_evidencia: TipoEvidenciaHipotese

# --- Modelo de Resposta Final ---
class RedeContingencialOutput(BaseModel):
    sujeitos: List[NoSujeito] = Field(default_factory=list)
    acoes_comportamentos: List[NoAcaoComportamento] = Field(default_factory=list)
    emissoes_comportamentais: List[ArestaEmissaoComportamental] = Field(default_factory=list)
    estimulos_eventos: List[NoEstimuloEvento] = Field(default_factory=list)
    relacoes_temporais: List[ArestaRelacaoTemporal] = Field(default_factory=list)

    condicoes_estados: List[NoCondicaoEstado] = Field(default_factory=list)
    relacoes_funcionais_antecedentes: List[ArestaRelacaoFuncionalAntecedente] = Field(default_factory=list)
    relacoes_funcionais_consequentes: List[ArestaRelacaoFuncionalConsequente] = Field(default_factory=list)

    relacoes_moduladoras_estado: List[ArestaRelacaoModuladoraEstado] = Field(default_factory=list)
    hipoteses_analiticas: List[NoHipoteseAnalitica] = Field(default_factory=list)
    evidencias_para_hipoteses: List[ArestaEvidenciaParaHipotese] = Field(default_factory=list)

    timeline:List[str] = Field(default_factory=str)
    # analise_metadados: Optional[Dict[str, Any]] = Field(None, description="Metadados sobre a análise, e.g., ID da análise, data, nome do analista (LLM).")