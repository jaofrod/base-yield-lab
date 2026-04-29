# Grant Strategy: DeFAI Agent Framework

## Indice
1. [Reposicionamento](#1-reposicionamento)
2. [Proposta de Valor Publico](#2-proposta-de-valor-publico)
3. [Grants Alvo](#3-grants-alvo)
4. [Mudancas Arquiteturais Necessarias](#4-mudancas-arquiteturais-necessarias)
5. [Narrativa por Grant](#5-narrativa-por-grant)
6. [Roadmap Publico](#6-roadmap-publico)
7. [Template de Application](#7-template-de-application)

---

## 1. Reposicionamento

### De: Bot Pessoal de Yield Optimization
O projeto atual e um bot pessoal que monitora APYs entre Aave V3 e Compound III na Base e move USDC automaticamente para maximizar rendimento. Funciona, mas e fechado, hardcoded para uma estrategia, e beneficia apenas o operador.

### Para: DeFAI Agent Framework (Open-Source)
O reposicionamento transforma o bot num **framework open-source para construir agentes DeFi autonomos com IA**. Qualquer desenvolvedor pode:
- Criar estrategias custom via plugins
- Configurar protocolos/chains/tokens via YAML
- Reutilizar a infraestrutura de seguranca (Firewall, Executor, monitoramento)
- Contribuir novas estrategias e integrações para a comunidade

### Por que esse pivô faz sentido?
1. **O core ja existe** — Listener, Engine (LLM), Firewall, Executor ja estao arquitetados
2. **A demanda e real** — nao existe um framework open-source maduro para agentes DeFi com IA
3. **Alinhamento com grants** — foundations financiam infra publica, nao bots pessoais
4. **Escala o aprendizado** — ao invés de um bot, um ecossistema de estrategias

### O que NAO muda
- A estrategia pessoal de yield optimization continua funcionando — vira o "plugin exemplo"
- A seguranca (Firewall, chave privada isolada) permanece como principio core
- O foco em aprendizado e educacao se amplifica (docs, tutoriais, exemplos)

---

## 2. Proposta de Valor Publico

### O Problema
Agentes DeFi com IA estao surgindo, mas:
- **Sao fechados** — cada projeto reinventa a roda (monitoramento on-chain, execution engine, seguranca)
- **Sao inseguros** — muitos nao tem firewall deterministico, confiando 100% no LLM
- **Sao inacessiveis** — requerem conhecimento profundo de smart contracts E IA simultaneamente
- **Nao sao auditaveis** — closed-source torna impossivel verificar se o bot e seguro

### A Solucao: DeFAI Agent Framework
Um framework open-source que **separa concerns**:

| Camada | Responsabilidade | Quem contribui |
|---|---|---|
| **Core** | Listener, Firewall, Executor, State Builder | Framework maintainers |
| **Strategies** | Logica de decisao (plugins) | Comunidade |
| **Integrations** | Novos protocolos, chains, tokens | Comunidade |
| **Config** | Parametros, thresholds, alertas | Usuarios finais |

### Beneficios para o Ecossistema
1. **Para desenvolvedores:** infraestrutura pronta para criar agentes DeFi seguros sem começar do zero
2. **Para protocolos (Aave, Compound):** mais TVL organico via automação acessivel
3. **Para usuarios DeFi:** yield optimization automatizado com transparencia total (open-source)
4. **Para o ecossistema Base/L2:** mais atividade on-chain, mais usuarios sofisticados
5. **Para educacao:** documentacao didatica que ensina DeFi + IA simultaneamente (o projeto ja nasceu com esse DNA — ver design-doc.md e flow.md)

---

## 3. Grants Alvo

### 3.1 Base Builder Grants

| Campo | Detalhes |
|---|---|
| **Organizacao** | Base (Coinbase) |
| **URLs** | https://docs.base.org/get-started/get-funded |
| **Tracks disponiveis** | Builder Grants (1-5 ETH), CDP Builder Grants ($3k-$10k), Base Batches 2026 ($10k + possivel $50k invest) |
| **Foco** | Projetos **ja deployados** que trazem usuarios e atividade para a rede Base |
| **Ciclo** | Builder Grants: rolling (equipe Base escaneia Twitter/Farcaster e nomeia projetos). CDP: ciclos sazonais. Base Batches: deadlines fixos |

**IMPORTANTE — Como Base Grants funciona:**
A equipe de grants da Base **proativamente busca** builders no Twitter, Farcaster e via nominacoes da comunidade. NAO existe um formulario de aplicacao tradicional — eles encontram voce. Isso significa que **presenca publica e crucial**: ter o repo no GitHub, postar sobre o projeto no Twitter/Farcaster, e ter o bot rodando visivelmente.

**Base Batches 2026 (oportunidade imediata):**
- Deadline Startup track: **9 de marco de 2026**
- Deadline Student track: **27 de abril de 2026**
- URL: https://www.basebatches.xyz/
- Top 15 equipes recebem $10k + pelo menos 3 recebem $50k do Base Ecosystem Fund

**Por que nos qualificamos:**
- O framework gera atividade on-chain direta na Base (transacoes reais de DeFi)
- Aave V3 e Compound III ja estao deployados na Base — o framework aumenta o uso deles
- Educacao: docs didaticos ensinam devs a construir na Base
- Open-source: infra publica para o ecossistema Base

**Como enquadrar:**
> "DeFAI Agent Framework e infra open-source que permite qualquer dev criar agentes DeFi com IA na Base. O primeiro plugin (yield optimizer) ja gera atividade on-chain real entre Aave V3 e Compound III. Cada usuario do framework = mais transacoes e TVL na Base."

**Estrategia de abordagem:**
1. Publicar o repo open-source no GitHub com README profissional
2. Postar sobre o projeto no Twitter e Farcaster (a equipe Base escaneia la)
3. Aplicar para **Base Batches 2026** (deadline 9 de marco) como caminho mais direto
4. Manter presenca ativa para ser notado pelo time de Builder Grants

### 3.2 Aave Grants DAO

| Campo | Detalhes |
|---|---|
| **Organizacao** | Aave Grants DAO |
| **URL** | https://aavegrants.org |
| **Status** | **INATIVO** — AGD 1.0 foi encerrado em agosto de 2024 |
| **O que aconteceu** | A renovacao do programa foi votada em janeiro 2024. A maioria votou ABSTAIN, e o programa nao foi renovado. Em agosto 2024, a equipe anunciou o encerramento formal. O treasury restante foi devolvido ao Aave DAO em fevereiro 2025. |

**Situacao atual:**
O programa de grants do Aave esta **efetivamente morto**. Alem disso, a BGD Labs (principal contribuidora tecnica do Aave) anunciou que cessara contribuicoes em abril 2026, indicando turbulencia no ecossistema Aave.

**O que fazer:**
- Monitorar o Aave Governance Forum (https://governance.aave.com/) para possiveis novos programas
- NAO investir tempo preparando application para Aave grants agora
- Manter a integracao Aave V3 no framework (continua sendo um protocolo relevante para os usuarios), o que posiciona o projeto caso um novo programa surja

**Valor residual da integracao Aave:**
Mesmo sem grant, ter Aave V3 como integracao no framework:
- Demonstra capacidade tecnica para outros grants
- Educa devs sobre como aTokens, reserveData e liquidityRate funcionam
- E necessario para o plugin de yield optimization funcionar

### 3.3 Compound Grants Program

| Campo | Detalhes |
|---|---|
| **Organizacao** | Compound Finance |
| **URL** | https://www.comp.xyz (forum de governance) |
| **Status** | **INATIVO** — parou de aceitar propostas em maio de 2024 |
| **O que aconteceu** | CGP 2.0 (via Questbook) encerrou em maio 2024. Uma proposta de renovacao (#326) existe na governance, mas o status e incerto. |

**Situacao atual:**
O programa de grants do Compound esta **em limbo**. Nao ha processo de aplicacao ativo.

**O que fazer:**
- Monitorar o Compound Forum (https://www.comp.xyz/) e a proposta de renovacao no Tally
- NAO investir tempo preparando application agora
- Manter a integracao Compound III (Comet) no framework pelo valor tecnico

**Valor residual da integracao Compound:**
Mesmo sem grant, ter Compound III como integracao:
- Demonstra integracao deep com Comet (supply, withdraw, getUtilization, getSupplyRate)
- Documentacao didatica sobre como Comet funciona
- Necessario para o plugin de yield optimization

### 3.4 Optimism Retro Funding

| Campo | Detalhes |
|---|---|
| **Organizacao** | Optimism Foundation |
| **URL principal** | https://atlas.optimism.io/ (OP Atlas — portal de aplicacao) |
| **Tracks relevantes** | Retro Funding: Onchain Builders (8M OP) e Retro Funding: Dev Tooling (8M OP) |
| **Orcamento total comprometido** | 850M OP ao longo do tempo |
| **Modelo** | Rolling — recompensas mensais baseadas em impacto medido algoritmicamente |
| **Status** | **ATIVO** e expandido significativamente |

**EVOLUCAO IMPORTANTE (2025+):**
O Retro Funding evoluiu de rounds discretos anuais para um modelo **continuo e rolling**. Nao e mais um evento anual — e um sistema permanente de recompensas baseado em impacto real medido on-chain.

**Tracks relevantes para nos:**

**1. Onchain Builders** (https://atlas.optimism.io/missions/retro-funding-onchain-builders)
- Requer contrato verificado em chain OP elegivel (Base, OP Mainnet, Unichain, Zora, Mode, etc. — 19+ chains)
- Requisito: atividade minima nos ultimos 180 dias
- Bonus: projetos DeFi com $1M+ de TVL medio nos ultimos 180 dias ganham recompensas extras
- **Limitacao para nos:** o threshold de $1M TVL para bonus DeFi esta fora do nosso alcance com $50 de capital. Mas a participacao base (sem bonus TVL) ainda e possivel se tivermos contratos deployados

**2. Dev Tooling** (https://atlas.optimism.io/missions/retro-funding-dev-tooling)
- Para software open-source de toolchain que suporta desenvolvimento onchain no Superchain
- Compiladores, bibliotecas, debuggers, etc.
- **Nosso melhor fit:** framework como ferramenta de desenvolvimento para builders DeFi

**Como enquadrar:**
> "DeFAI Agent Framework e uma biblioteca open-source (MIT) que permite desenvolvedores criarem agentes DeFi com IA no Superchain. O framework abstrai a complexidade de monitoramento on-chain, execucao segura de transacoes e integracao com IA, permitindo que builders foquem na logica de estrategia. Rodando na Base (parte do Superchain), gera atividade on-chain real enquanto educa a proxima geracao de builders DeFi."

**Estrategia de abordagem:**
1. Registrar o projeto no OP Atlas (https://atlas.optimism.io/)
2. Focar no track **Dev Tooling** (mais alinhado com framework open-source)
3. Publicar no PyPI como pacote reutilizavel
4. Acumular metricas de impacto: downloads, forks, contratos deployados usando o framework
5. O impacto e medido **algoritmicamente** (nao por comite subjetivo) — metricas on-chain reais importam

**Nota sobre timing:**
Diferente dos grants tradicionais, Retro Funding recompensa impacto **ja demonstrado**. O framework precisa estar rodando e sendo usado antes de gerar recompensas significativas. E um jogo de longo prazo.

---

### 3.5 Resumo: Prioridade dos Grants

| Grant | Status | Prioridade | Acao Imediata |
|---|---|---|---|
| **Base Batches 2026** | ATIVO (deadline 9/mar) | **URGENTE** | Aplicar JA |
| **Base Builder Grants** | ATIVO (rolling) | **ALTA** | Publicar repo + presenca social |
| **Optimism Retro Funding** | ATIVO (rolling) | **MEDIA** | Registrar no OP Atlas, acumular impacto |
| **Aave Grants DAO** | INATIVO | **BAIXA** | Monitorar governance forum |
| **Compound Grants** | INATIVO | **BAIXA** | Monitorar governance forum |

**Conclusao: focar em Base (imediato) e Optimism (medio prazo).** Aave e Compound sao irrelevantes para grants no momento, mas manter as integrações no framework pelo valor tecnico e educacional.

---

## 4. Mudancas Arquiteturais Necessarias

Para ir de "bot pessoal" para "framework open-source", o codigo precisa das seguintes mudancas:

### 4.1 Plugin System para Estrategias

**Antes (hardcoded):**
```python
# A logica de yield optimization esta espalhada pelo codigo
if apy_diff > MIN_APY_DIFF:
    move_funds(from_protocol, to_protocol)
```

**Depois (plugin):**
```python
# strategies/yield_optimizer.py
class YieldOptimizerStrategy(BaseStrategy):
    """Move capital entre protocolos buscando melhor APY."""

    def analyze(self, state: ChainState) -> Action:
        best = max(state.positions, key=lambda p: p.apy)
        current = state.current_position
        if best.apy - current.apy >= self.config.min_apy_diff:
            return MoveFunds(from_=current.protocol, to=best.protocol)
        return Hold(reason="APY difference below threshold")

    def required_integrations(self) -> list[str]:
        return ["aave_v3", "compound_iii"]
```

**Interface base:**
```python
# core/strategy.py
from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    @abstractmethod
    def analyze(self, state: ChainState) -> Action:
        """Analisa o estado on-chain e retorna uma ação."""
        pass

    @abstractmethod
    def required_integrations(self) -> list[str]:
        """Lista os protocolos necessarios para essa estrategia."""
        pass
```

### 4.2 Configuracao via YAML

**Antes (constantes no codigo):**
```python
CHAIN_ID = 8453
MIN_APY_DIFF = 1.5
POLL_INTERVAL_SECONDS = 300
```

**Depois (config.yaml):**
```yaml
# config.yaml
agent:
  name: "my-yield-bot"
  strategy: "yield_optimizer"

chain:
  name: "base"
  chain_id: 8453
  rpc_url: "${ALCHEMY_RPC_URL}"  # variavel de ambiente

strategy:
  min_apy_diff: 1.5
  min_apy_absolute: 0.5
  poll_interval_seconds: 300
  min_time_between_moves: 3600

security:
  max_single_tx_usd: 50
  max_gas_cost_usd: 0.10
  approved_protocols:
    - aave_v3
    - compound_iii
  approved_tokens:
    - USDC

alerts:
  type: "telegram"  # ou discord, webhook
  config:
    bot_token: "${TELEGRAM_BOT_TOKEN}"
    chat_id: "${TELEGRAM_CHAT_ID}"
```

### 4.3 Integrações como Modulos

**Estrutura:**
```
integrations/
  base.py              # IntegrationBase ABC
  aave_v3/
    __init__.py
    provider.py         # AaveV3Provider(IntegrationBase)
    abi.py              # ABIs do Aave
  compound_iii/
    __init__.py
    provider.py         # CompoundIIIProvider(IntegrationBase)
    abi.py              # ABIs do Compound
  uniswap_v3/          # futuro: swap integration
    ...
```

**Interface:**
```python
# integrations/base.py
class IntegrationBase(ABC):
    @abstractmethod
    def get_apy(self) -> float:
        """Retorna APY atual do protocolo."""
        pass

    @abstractmethod
    def get_balance(self, wallet: str) -> int:
        """Retorna saldo depositado no protocolo."""
        pass

    @abstractmethod
    def deposit(self, amount: int) -> TxReceipt:
        """Deposita tokens no protocolo."""
        pass

    @abstractmethod
    def withdraw(self, amount: int) -> TxReceipt:
        """Saca tokens do protocolo."""
        pass
```

### 4.4 Suporte Multi-Chain

**Antes:** hardcoded para Base (chain_id 8453).

**Depois:** chain como configuracao, permitindo:
- Base (8453)
- Optimism (10)
- Arbitrum (42161)
- Ethereum mainnet (1)
- Qualquer EVM-compatible

```python
# core/chain.py
class ChainConfig:
    chain_id: int
    rpc_url: str
    block_time: float
    gas_token: str
    explorer_url: str

SUPPORTED_CHAINS = {
    "base": ChainConfig(chain_id=8453, ...),
    "optimism": ChainConfig(chain_id=10, ...),
    "arbitrum": ChainConfig(chain_id=42161, ...),
}
```

### 4.5 Estrutura Final do Repositorio

```
defai-agent-framework/
  README.md                    # Intro, quick start, badges
  LICENSE                      # MIT
  docs/
    getting-started.md
    architecture.md
    creating-strategies.md
    creating-integrations.md
    security-model.md
  core/
    __init__.py
    agent.py                   # Loop principal configuravel
    strategy.py                # BaseStrategy ABC
    firewall.py                # Firewall generico
    executor.py                # Executor generico
    state.py                   # ChainState builder
    config.py                  # YAML loader
  integrations/
    base.py                    # IntegrationBase ABC
    aave_v3/
    compound_iii/
    registry.py                # Auto-discovery de integrações
  strategies/
    yield_optimizer.py         # Plugin padrao (o bot original)
    registry.py                # Auto-discovery de estrategias
  config/
    base-yield-optimizer.yaml  # Config exemplo
  examples/
    simple-yield-bot/          # Exemplo minimo funcional
    paper-trading/             # Exemplo sem transacoes reais
  tests/
    core/
    integrations/
    strategies/
```

### 4.6 Resumo das Mudancas

| Mudanca | Esforco | Prioridade | Motivo |
|---|---|---|---|
| Plugin system (BaseStrategy) | Medio | Alta | Core do framework |
| Config YAML | Baixo | Alta | Usabilidade |
| Integrações como modulos | Medio | Alta | Extensibilidade |
| Multi-chain | Medio | Media | Amplia escopo de grants |
| Docs/README | Medio | Alta | Obrigatorio para open-source |
| Tests | Alto | Alta | Credibilidade |
| CI/CD (GitHub Actions) | Baixo | Media | Profissionalismo |

---

## 5. Narrativa por Grant

### 5.1 Para Base (Builder Grants + Base Batches)
**Angulo:** "Infraestrutura que gera atividade on-chain na Base"

> A rede Base tem protocolos DeFi maduros (Aave V3, Compound III) mas falta tooling para que desenvolvedores criem automacoes sofisticadas. DeFAI Agent Framework preenche esse gap: um framework open-source em Python que permite qualquer dev criar agentes DeFi com IA na Base.
>
> Cada instancia do framework gera transacoes reais na Base — depositos, saques, approvals. Com gas a $0.005 por TX, a barreira de entrada e quase zero. O plugin padrao (yield optimizer) ja roda em producao com capital real.
>
> O framework tem um Firewall deterministico que valida TODA decisao da IA antes de assinar qualquer transacao — o LLM sugere, mas codigo Python puro aprova. Isso resolve o maior risco de agentes DeFi com IA: alucinacao levando a perda de fundos.
>
> **Meta com o grant:** suportar 5+ protocolos na Base, lançar docs completos, e atingir 50+ forks no GitHub em 6 meses.

**Para Base Batches especificamente:**
> Somos um time early-stage construindo infra open-source para agentes DeFi com IA na Base. Prototipo funcional rodando com capital real. Buscamos mentoria e recursos para transformar o bot em framework e acelerar adocao.

### 5.2 Para Optimism Retro Funding
**Angulo:** "Dev tooling open-source para o Superchain"

> DeFAI Agent Framework e uma biblioteca open-source (MIT) que abstrai a complexidade de construir agentes DeFi autonomos no Superchain. Em vez de cada developer reimplementar monitoramento on-chain, execucao de transacoes e validacao de seguranca, o framework fornece isso como building blocks reutilizaveis.
>
> Impacto mensuravel: X downloads no PyPI, Y repositorios usando o framework, Z contratos deployados por agentes construidos com o framework, W transacoes on-chain geradas.
>
> O framework roda nativamente na Base e pode ser estendido para qualquer chain do Superchain (Optimism, Unichain, Zora, Mode, etc.) via configuracao YAML — sem mudanca de codigo.

---

## 6. Roadmap Publico

### Fase 1: Foundation (Meses 1-2) — EM ANDAMENTO
- [x] Arquitetura core: Listener, Engine, Firewall, Executor
- [x] Integracao Aave V3 (Base)
- [x] Integracao Compound III (Base)
- [x] Design doc e flow doc detalhados
- [ ] Refatorar para plugin system (BaseStrategy)
- [ ] Configuracao via YAML
- [ ] Primeiro plugin: yield_optimizer

### Fase 2: Framework (Meses 3-4)
- [ ] Integrações como modulos (IntegrationBase)
- [ ] Registro automatico de strategies e integrations
- [ ] Suporte multi-chain (Base + Optimism)
- [ ] Testes unitarios e de integracao
- [ ] CI/CD com GitHub Actions
- [ ] Documentacao completa (getting started, architecture, tutorials)

### Fase 3: Community (Meses 5-6)
- [ ] README profissional com badges e quick start
- [ ] Exemplos: simple-yield-bot, paper-trading
- [ ] Template para criar novas strategies
- [ ] Template para criar novas integrations
- [ ] Publicar no PyPI (`pip install defai-agent`)
- [ ] Submeter applications para grants (Base, Aave, Compound)

### Fase 4: Growth (Meses 7-12)
- [ ] Mais integrações: Uniswap V3, Morpho, Euler
- [ ] Estrategias avancadas: arbitragem, liquidacao, LP management
- [ ] Dashboard web para monitorar agentes
- [ ] Aplicar para Optimism RetroPGF (com metricas de impacto)
- [ ] Comunidade: Discord, contributing guide, bounties

---

## 7. Template de Application

### Template Generico (adaptar por grant)

---

**Project Name:** DeFAI Agent Framework

**One-liner:** Open-source Python framework for building AI-powered DeFi agents with built-in safety guardrails.

**Category:** Developer Tooling / DeFi Infrastructure

**License:** MIT

**Repository:** github.com/[usuario]/defai-agent-framework

---

**Problem:**

Building DeFi automation with AI requires solving three hard problems simultaneously: (1) reliable on-chain data reading, (2) safe transaction execution, and (3) intelligent decision-making. Today, every project reinvents this infrastructure from scratch, often with critical security gaps — LLMs can hallucinate invalid transactions, and without deterministic validation, user funds are at risk.

**Solution:**

DeFAI Agent Framework provides a modular, open-source foundation for AI-powered DeFi agents:

- **Core engine** handles on-chain monitoring, transaction building, and execution
- **Deterministic Firewall** validates every AI decision against hardcoded safety rules before any transaction is signed — the LLM can never bypass this layer
- **Plugin system** lets developers create custom strategies (yield optimization, arbitrage, liquidation) without rebuilding infrastructure
- **YAML configuration** makes it accessible to non-expert users
- **Multi-chain support** starting with [CHAIN_NAME] and expanding to the broader ecosystem

**Traction:**

- Functional prototype running on [CHAIN_NAME] with real capital
- Yield optimizer strategy in production (Aave V3 + Compound III)
- Architecture validated through [N] weeks of paper trading + [N] weeks of live trading
- Detailed documentation covering both the technical architecture and DeFi education

**Grant Usage:**

| Item | Amount | Description |
|---|---|---|
| Plugin system development | $X | Refactor core into extensible framework |
| Multi-chain support | $X | Add [CHAIN_2] support |
| Documentation & tutorials | $X | Comprehensive docs, video tutorials |
| Testing & security | $X | Unit tests, integration tests, security review |
| Community building | $X | Discord, bounties for first contributions |

**Milestones:**

1. **Month 1-2:** Framework core refactored, plugin system working, YAML config
2. **Month 3-4:** Multi-chain support, 3+ protocol integrations, full test suite
3. **Month 5-6:** Public launch, PyPI package, 50+ GitHub stars, 10+ forks

**Team:**

[Nome] — Full-stack developer with focus on DeFi and AI. Building this project to learn blockchain development deeply while creating useful open-source infrastructure. Currently running the prototype with personal capital on Base.

**Links:**
- Repository: [URL]
- Design Doc: [URL to design-doc.md]
- Flow Documentation: [URL to flow.md]
- Live Demo / Dashboard: [URL se existir]

---

### Dicas para a Application

1. **Seja especifico com metricas:** "50+ forks" e melhor que "crescimento do projeto"
2. **Mostre skin in the game:** mencione que voce roda o bot com capital proprio
3. **Destaque o Firewall:** seguranca e um diferencial ENORME — poucos projetos de agentes DeFi tem validacao deterministrica
4. **Customize por grant:** cada foundation se importa com coisas diferentes (Base = atividade on-chain, Aave = TVL, Compound = integracao, Optimism = bens publicos)
5. **Inclua o aspecto educacional:** o DNA educacional do projeto (docs que ensinam blockchain) e um ponto forte unico
6. **Comece pequeno:** peça $5k-$10k no primeiro grant. E mais facil aprovar, e abre portas para grants maiores depois
7. **Video demo:** grave um video curto (2-3 min) mostrando o bot rodando. Impacto visual >> texto

---

## Proximo Passo Imediato

1. **URGENTE (antes de 9 de marco):** Preparar application para Base Batches 2026
2. Criar o repositorio publico no GitHub com README profissional
3. Estabelecer presenca no Twitter e Farcaster (Base Builder Grants escaneia la)
4. Refatorar o codigo para plugin system (Fase 1 do roadmap)
5. Registrar o projeto no OP Atlas para Optimism Retro Funding
6. Acumular metricas de impacto para Retro Funding (downloads, forks, transacoes)
