# ADR-001: Exceções à Regra de Tamanho de Arquivo

## Status
**Accepted** | Data: 2025-12-11

## Contexto

### Regra Geral de Tamanho
Conforme definido no CLAUDE.md e padrões do projeto:
- **Ideal:** 200-400 linhas por arquivo
- **Máximo:** 500 linhas
- **Justificativa:** Manutenibilidade, testabilidade, Single Responsibility Principle

### Necessidade de Exceções
Alguns arquivos excedem o limite devido à natureza complexa do domínio ou funcionalidade concentrada. Este ADR documenta exceções aprovadas e planos de remediação.

---

## Decisão

Aprovar exceções TEMPORÁRIAS para os seguintes arquivos, com planos de refatoração obrigatórios:

### 1. `application/common/services/generic_service.py` (668 linhas)

**Linhas:** 668
**Limite:** 500
**Excesso:** +33% (168 linhas)
**Severidade:** 🔴 **CRITICAL**

**Justificativa da Exceção:**
- Contém implementação completa de GenericService (CRUD base)
- Inclui definições de erro (ServiceError, NotFoundError, ValidationError, etc)
- Mixins de validação e publicação de eventos
- Protocolo IMapper embutido

**Problemas Identificados:**
- Violação de SRP (Single Responsibility Principle)
- Baixa coesão - múltiplas responsabilidades em um arquivo
- Dificulta testes unitários isolados
- Dificulta compreensão e manutenção

**Plano de Remediação (P1 - Alta Prioridade):**
```
Timeline: Sprint atual + 1 (2-3 semanas)
Owner: Tech Lead + Backend Team
Esforço: M (4-6 horas)

Estrutura Target:
application/common/services/
  ├── __init__.py (exports)
  ├── generic_service.py (~200 linhas) - apenas GenericService
  ├── service_errors.py (~100 linhas) - error hierarchy
  ├── protocols.py (~50 linhas) - IMapper, IEventPublisher
  └── mixins.py (~100 linhas) - ValidationMixin, EventMixin (se aplicável)

Total: ~450 linhas (distribuídas, -218 linhas vs atual)
```

**Critérios de Conclusão:**
- [ ] GenericService isolado em arquivo próprio (<250 linhas)
- [ ] Errors em módulo separado service_errors.py
- [ ] Todos os testes passando
- [ ] Coverage mantido em ≥95%
- [ ] Imports atualizados em dependentes
- [ ] ADR atualizado para Deprecated

---

### 2. `infrastructure/cache/providers/redis_jitter.py` (492 linhas)

**Linhas:** 492
**Limite:** 500
**Excesso:** -1.6% (8 linhas ABAIXO do limite)
**Severidade:** 🟡 **MONITOR**

**Justificativa da Exceção:**
- Algoritmos complexos de cache (jitter calculation, stampede prevention)
- Implementação de padrão Cache-Aside com garantias de consistência
- Múltiplos métodos de serialização (JSON, Pickle, MessagePack)
- TTL randomization para evitar thundering herd

**Análise de Complexidade:**
- Métodos individuais são focados (<50 linhas cada)
- Alta coesão - tudo relacionado a Redis com jitter
- Testes unitários cobrem 95%+ do arquivo

**Ação:**
- **Status:** ✅ **APROVADO** - está dentro do limite
- **Monitoramento:** Revisar trimestralmente (Q1 2025)
- **Threshold de Alerta:** >520 linhas → acionar refatoração

**Possível Refatoração Futura (baixa prioridade):**
- Extrair serializers para `cache/serializers.py`
- Extrair jitter algorithms para `cache/jitter_strategies.py`
- **Trigger:** Se crescer além de 520 linhas

---

### 3. `application/examples/order/use_cases/place_order.py` (464 linhas)

**Linhas:** 464
**Limite:** 500
**Excesso:** -7.2% (36 linhas ABAIXO)
**Severidade:** 🟢 **OK**

**Justificativa:**
- Use case complexo de pedido (validações, estoque, pagamento, eventos)
- Exemplo de implementação completa para referência
- Bem estruturado com early returns e guards

**Ação:** ✅ **APROVADO** - nenhuma ação necessária

---

### 4. `infrastructure/scylladb/repository.py` (458 linhas)

**Linhas:** 458
**Limite:** 500
**Excesso:** -8.4% (42 linhas ABAIXO)
**Severidade:** 🟢 **OK**

**Justificativa:**
- Implementação completa de repository pattern para ScyllaDB
- Operações CRUD + batch + queries customizadas
- Tratamento de consistência e retry logic

**Ação:** ✅ **APROVADO** - nenhuma ação necessária

---

### 5. `infrastructure/dapr/core/client.py` (451 linhas)

**Linhas:** 451
**Limite:** 500
**Excesso:** -9.8% (49 linhas ABAIXO)
**Severidade:** 🟢 **OK**

**Justificativa:**
- Wrapper completo do Dapr SDK
- Abstração de service invocation, state, pub/sub
- Tratamento de erros e retry logic

**Ação:** ✅ **APROVADO** - nenhuma ação necessária

---

## Consequências

### Positivas ✅
- **Transparência:** Exceções documentadas e rastreáveis
- **Accountability:** Owners e timelines definidos
- **Qualidade:** Planos de remediação garantem evolução
- **Governança:** Review trimestral previne deterioração

### Negativas ❌
- **Dívida Técnica:** generic_service.py é dívida P1 documentada
- **Risco de Precedente:** Exceções podem ser usadas como justificativa para novos casos
- **Overhead:** Requer review e atualização trimestral

### Neutras ⚪
- **Flexibilidade:** Permite pragmatismo sem comprometer padrões
- **Evolução:** ADR pode ser atualizado conforme novas exceções

---

## Processo de Exceção para Novos Arquivos

**Se um arquivo precisar exceder 500 linhas:**

1. **Criar PR com justificativa**
   - Por que não pode ser quebrado?
   - Qual a complexidade do domínio?
   - Impacto em manutenibilidade?

2. **Aprovar via Code Review**
   - Requer aprovação de 2+ tech leads
   - Análise de alternativas

3. **Atualizar este ADR**
   - Adicionar nova seção
   - Definir plano de remediação (se aplicável)
   - Estabelecer critérios de monitoramento

4. **Review Trimestral**
   - Q1, Q2, Q3, Q4
   - Verificar se exceções ainda são necessárias
   - Atualizar status (Approved → Deprecated → Resolved)

---

## Revisões e Histórico

| Data | Evento | Responsável |
|------|--------|-------------|
| 2025-12-11 | Criação do ADR | Tech Lead |
| 2025-Q1 | Review agendado | Backend Team |

---

## Alternativas Consideradas

### Alternativa 1: Forçar limite rígido de 500 linhas
**Rejeitada:** Pragmaticamente inviável para casos complexos de domínio. Resultaria em quebra artificial de módulos coesos.

### Alternativa 2: Aumentar limite para 700 linhas
**Rejeitada:** Enfraqueceria padrão de qualidade. 500 linhas é limite razoável para manutenibilidade.

### Alternativa 3: Exceções não documentadas (status quo)
**Rejeitada:** Falta de governança. Exceções devem ser explícitas e rastreáveis.

### Alternativa 4: ADR + Plano de Remediação (ESCOLHIDA)
**Aceita:** Balanceia pragmatismo com governança. Exceções temporárias com accountability.

---

## Referências

- CLAUDE.md - Regras globais de tamanho de arquivo
- [Clean Code by Robert C. Martin](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882) - Cap. 10: Classes
- [Code Complete 2 by Steve McConnell](https://www.amazon.com/Code-Complete-Practical-Handbook-Construction/dp/0735619670) - Seção sobre modularização

---

## Próxima Revisão
**Data:** 2025-Q1 (Março 2025)
**Responsável:** Backend Team Lead
**Checklist:**
- [ ] Verificar status de refatoração do generic_service.py
- [ ] Monitorar tamanho de redis_jitter.py
- [ ] Identificar novos arquivos acima de 500 linhas
- [ ] Atualizar ADR com novos achados
