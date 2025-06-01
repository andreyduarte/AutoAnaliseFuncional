from typing import Optional, Dict, Any, Type, cast, List
from pydantic import BaseModel, ValidationError
from google import genai
import google.genai.types as genai_types
import logging
import json
import time

# Configure logging
logger = logging.getLogger(__name__)

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
        temperature=0.01
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
                model='gemini-2.5-flash-preview-05-20',#'gemini-2.0-flash-exp',
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