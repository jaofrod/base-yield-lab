"""
engine.py — O Cerebro do bot. Usa Claude (LLM) para tomar decisoes.

CONCEITO: Tool Use (Function Calling)
Em vez de pedir pro LLM responder em texto livre ("acho que deveria mover
para o Aave"), definimos "tools" — funcoes estruturadas que o LLM pode
chamar. O LLM retorna um JSON com o nome da tool e os parametros.

Vantagem: resposta 100% parseavel. Sem regex, sem "extraia o numero do
texto". O LLM retorna exatamente {tool: "move_funds", from: "aave_v3",
to: "compound_iii", amount: 50}.

CONCEITO: Safe defaults
Se a API do Claude falhar, se o LLM nao retornar tool_use, se o JSON
vier malformado — o fallback e SEMPRE "hold" (nao fazer nada).
Errar por inacao e infinitamente melhor que errar por acao quando
estamos mexendo com dinheiro real.
"""

import json
import logging
from dataclasses import asdict

import anthropic

from config import (
    ANTHROPIC_API_KEY,
    MIN_APY_DIFF,
    MIN_APY_ABSOLUTE,
    MAX_SINGLE_TX_USDC,
    MIN_TIME_BETWEEN_MOVES,
    MAX_GAS_COST_USD,
)
from state import BotState, LLMAction

logger = logging.getLogger(__name__)

# ============================================================
# CLIENT
# ============================================================

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

MODEL = "claude-sonnet-4-20250514"

# ============================================================
# SYSTEM PROMPT
#
# CONCEITO: Prompting para agentes financeiros
# O system prompt define as "regras do jogo". Interpolamos os
# thresholds reais para que o LLM nao invente numeros proprios.
# Quanto mais especifico o prompt, menos margem pra alucinacao.
# ============================================================

SYSTEM_PROMPT = f"""Voce e um agente DeFi que gerencia uma posicao de USDC na rede Base.
Seu objetivo e maximizar o rendimento (APY) movendo capital entre Aave V3
e Compound III, minimizando custos de gas e riscos.

Regras:
- So opere com USDC nos protocolos aprovados (Aave V3, Compound III)
- So mova capital se a diferenca de APY for >= {MIN_APY_DIFF}%
- Sempre considere o custo de gas antes de decidir
- Se ambos APYs estiverem abaixo de {MIN_APY_ABSOLUTE}%, mantenha posicao atual
- Nunca mova mais que {MAX_SINGLE_TX_USDC} USDC por transacao
- Respeite o cooldown minimo de {MIN_TIME_BETWEEN_MOVES}s entre movimentacoes
- Custo maximo de gas aceitavel: ${MAX_GAS_COST_USD}
- Se estiver em duvida, escolha "hold" (nao fazer nada)
- Se USDC estiver livre na wallet (nao depositado), deposite no protocolo com melhor APY
- Se detectar anomalias (APY zerado, ETH baixo), use "alert"

Analise os dados fornecidos e use UMA das tools disponiveis para agir."""

# ============================================================
# TOOLS (schemas para o Anthropic tool_use)
# ============================================================

TOOLS = [
    {
        "name": "hold",
        "description": "Manter posicao atual sem mudancas neste ciclo",
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Explicacao da decisao de nao agir",
                }
            },
            "required": ["reason"],
        },
    },
    {
        "name": "move_funds",
        "description": "Sacar USDC de um protocolo e depositar em outro",
        "input_schema": {
            "type": "object",
            "properties": {
                "from_protocol": {
                    "type": "string",
                    "enum": ["aave_v3", "compound_iii", "wallet"],
                    "description": "De onde sacar",
                },
                "to_protocol": {
                    "type": "string",
                    "enum": ["aave_v3", "compound_iii"],
                    "description": "Onde depositar",
                },
                "amount_usdc": {
                    "type": "number",
                    "description": "Quanto mover em USDC (usar -1 para mover tudo)",
                },
                "reason": {
                    "type": "string",
                    "description": "Explicacao da decisao",
                },
            },
            "required": ["from_protocol", "to_protocol", "amount_usdc", "reason"],
        },
    },
    {
        "name": "alert",
        "description": "Sinalizar situacao que precisa atencao humana",
        "input_schema": {
            "type": "object",
            "properties": {
                "severity": {
                    "type": "string",
                    "enum": ["info", "warning", "critical"],
                    "description": "Gravidade do alerta",
                },
                "message": {
                    "type": "string",
                    "description": "Descricao do que foi detectado",
                },
            },
            "required": ["severity", "message"],
        },
    },
]


# ============================================================
# FUNCOES INTERNAS
# ============================================================


def _state_to_prompt(state: BotState) -> str:
    """Converte BotState em texto legivel para o LLM."""
    data = asdict(state)
    return json.dumps(data, indent=2, default=str)


def _parse_response(response) -> LLMAction:
    """Extrai a tool_use do response do Claude e converte em LLMAction.

    CONCEITO: stop_reason
    O Claude retorna um "stop_reason" que indica POR QUE parou de gerar:
    - "tool_use": ele quer chamar uma tool (o que esperamos)
    - "end_turn": ele respondeu em texto livre (sem tool)
    - "max_tokens": cortou por limite

    Se nao for "tool_use", algo deu errado e retornamos hold por seguranca.
    """
    # Procurar bloco de tool_use no response
    tool_block = None
    for block in response.content:
        if block.type == "tool_use":
            tool_block = block
            break

    if tool_block is None:
        logger.warning("LLM nao retornou tool_use. Fallback para hold.")
        # Extrair texto se houver, para log
        text = ""
        for block in response.content:
            if block.type == "text":
                text = block.text
                break
        return LLMAction(action="hold", reason=f"LLM sem tool_use: {text[:200]}")

    tool_name = tool_block.name
    tool_input = tool_block.input

    if tool_name == "hold":
        return LLMAction(
            action="hold",
            reason=tool_input.get("reason", ""),
        )

    elif tool_name == "move_funds":
        return LLMAction(
            action="move_funds",
            from_protocol=tool_input.get("from_protocol", ""),
            to_protocol=tool_input.get("to_protocol", ""),
            amount_usdc=tool_input.get("amount_usdc", 0),
            reason=tool_input.get("reason", ""),
        )

    elif tool_name == "alert":
        return LLMAction(
            action="alert",
            severity=tool_input.get("severity", "info"),
            message=tool_input.get("message", ""),
        )

    else:
        logger.warning(f"Tool desconhecida: {tool_name}. Fallback para hold.")
        return LLMAction(action="hold", reason=f"Tool desconhecida: {tool_name}")


# ============================================================
# FUNCAO PUBLICA: get_decision()
# ============================================================


def get_decision(state: BotState) -> LLMAction:
    """Envia estado para o Claude e retorna a decisao como LLMAction.

    Esta e a UNICA funcao publica do engine. Ela:
    1. Serializa o BotState em texto
    2. Chama a API do Claude com tool_use
    3. Parseia o response
    4. Retorna LLMAction

    Se QUALQUER coisa falhar, retorna hold (safe default).
    """
    logger.info("Consultando Claude para decisao...")

    state_text = _state_to_prompt(state)
    user_message = f"Estado atual do bot:\n\n{state_text}\n\nAnalise e decida a acao."

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=[{"role": "user", "content": user_message}],
        )

        action = _parse_response(response)

        logger.info(f"Decisao do LLM: {action.action}")
        if action.action == "hold":
            logger.info(f"  Motivo: {action.reason}")
        elif action.action == "move_funds":
            logger.info(f"  {action.from_protocol} -> {action.to_protocol} | {action.amount_usdc} USDC")
            logger.info(f"  Motivo: {action.reason}")
        elif action.action == "alert":
            logger.info(f"  [{action.severity}] {action.message}")

        return action

    except anthropic.APIError as e:
        logger.error(f"Erro na API do Claude: {e}")
        return LLMAction(action="hold", reason=f"API error: {e}")
    except Exception as e:
        logger.error(f"Erro inesperado no engine: {e}")
        return LLMAction(action="hold", reason=f"Unexpected error: {e}")
