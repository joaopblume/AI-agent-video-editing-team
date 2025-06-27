#!/usr/bin/env python3
"""
Base Agent - Classe Abstrata para Arquitetura Padrão dos Agentes
=================================================================

Esta classe define a arquitetura obrigatória que todos os agentes devem seguir
para funcionar no sistema de edição de vídeo com IA.

RESPONSABILIDADES OBRIGATÓRIAS:
- Estrutura de pastas padronizada
- Sistema de relatórios JSON para o Coordinator
- Feedback estruturado entre agentes
- Carregamento de instruções do Coordinator
- Salvamento de resultados e análises

AGENTES DO SISTEMA:
- RICO: Video Chunking Specialist
- DAVID: Audio Cleaning Specialist  
- SAIMON: Content Selection Specialist
- CLOE: Dynamic Editing Specialist
- SHEYLA: Quality Control Specialist
"""

import os
import json
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any, Optional

class BaseAgent(ABC):
    """
    Classe abstrata que define a arquitetura padrão para todos os agentes.
    
    ESTRUTURA OBRIGATÓRIA:
    =====================
    
    1. DIRETÓRIOS:
       - processing/{agent_name}/     # Pasta principal do agente
       - processing/chunks/           # Chunks de vídeo (Rico)
       - processing/coordinator/      # Planos e relatórios do Coordinator
    
    2. ARQUIVOS OBRIGATÓRIOS:
       - {agent_name}_analysis_*.json      # Análises detalhadas
       - {agent_name}_results.json         # Resultados consolidados
       - {agent_name}_feedback.json        # Feedback para Coordinator
    
    3. MÉTODOS OBRIGATÓRIOS:
       - load_processing_plan()            # Carrega instruções do Coordinator
       - execute()                         # Método principal de processamento
       - generate_feedback()               # Feedback para Coordinator
       - save_results()                    # Salva resultados finais
    """
    
    def __init__(self, agent_name: str, role: str):
        """
        Inicializa agente com estrutura padrão.
        
        Args:
            agent_name: Nome do agente (RICO, DAVID, SAIMON, CLOE, SHEYLA)
            role: Função do agente (ex: AUDIO_CLEANING_SPECIALIST)
        """
        self.name = agent_name.upper()
        self.role = role.upper()
        self.start_time = time.time()
        
        # Estrutura de diretórios obrigatória
        self.processing_dir = Path('processing')
        self.agent_dir = self.processing_dir / self.name.lower()
        self.chunks_dir = self.processing_dir / 'chunks'
        self.coordinator_dir = self.processing_dir / 'coordinator'
        
        # Criar diretórios obrigatórios
        self.agent_dir.mkdir(parents=True, exist_ok=True)
        self.coordinator_dir.mkdir(parents=True, exist_ok=True)
        
        # Arquivos padrão
        self.results_file = self.agent_dir / f'{self.name.lower()}_results.json'
        self.feedback_file = self.agent_dir / f'{self.name.lower()}_feedback.json'
        self.workflow_plan_file = self.coordinator_dir / 'workflow_plan.json'
        
        print(f"🤖 {self.name} inicializado")
        print(f"📋 Função: {self.role}")
        print(f"📁 Diretório: {self.agent_dir}")
    
    def load_processing_plan(self) -> Optional[Dict[str, Any]]:
        """
        OBRIGATÓRIO: Carrega plano de processamento do Coordinator.
        
        Returns:
            Dict com instruções do Coordinator ou None se não encontrado
        """
        print(f"\n📋 {self.name}: Carregando plano de processamento...")
        
        if not self.workflow_plan_file.exists():
            print(f"❌ Plano não encontrado: {self.workflow_plan_file}")
            return None
        
        try:
            with open(self.workflow_plan_file, 'r', encoding='utf-8') as f:
                plan = json.load(f)
            
            # Verificar se este agente está na lista de agentes selecionados
            if self.name not in plan.get('selected_agents', []):
                print(f"❌ {self.name} não foi selecionado para este workflow")
                return None
            
            print(f"✅ Plano carregado - {self.name} selecionado para processamento")
            return plan
            
        except Exception as e:
            print(f"❌ Erro ao carregar plano: {e}")
            return None
    
    @abstractmethod
    def execute(self) -> bool:
        """
        OBRIGATÓRIO: Método principal de execução do agente.
        
        Deve implementar:
        1. Carregar plano do Coordinator
        2. Processar conforme instruções
        3. Salvar análises detalhadas
        4. Gerar feedback para Coordinator
        5. Salvar resultados finais
        
        Returns:
            bool: True se sucesso, False se falha
        """
        pass
    
    def save_analysis(self, analysis_data: Dict[str, Any], item_name: str) -> str:
        """
        PADRÃO: Salva análise detalhada de item específico.
        
        Args:
            analysis_data: Dados da análise
            item_name: Nome do item analisado
            
        Returns:
            Caminho do arquivo salvo
        """
        analysis_file = self.agent_dir / f"{self.name.lower()}_analysis_{item_name}.json"
        
        analysis_with_metadata = {
            'agent': self.name,
            'item_name': item_name,
            'analysis_timestamp': time.time(),
            'analysis_data': analysis_data
        }
        
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_with_metadata, f, indent=2, ensure_ascii=False)
        
        print(f"   💾 Análise salva: {analysis_file.name}")
        return str(analysis_file)
    
    def save_results(self, results: Dict[str, Any]) -> str:
        """
        OBRIGATÓRIO: Salva resultados consolidados do agente.
        
        Args:
            results: Resultados do processamento
            
        Returns:
            Caminho do arquivo de resultados
        """
        results_with_metadata = {
            'agent': self.name,
            'role': self.role,
            'execution_timestamp': time.time(),
            'processing_time': time.time() - self.start_time,
            'results': results
        }
        
        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump(results_with_metadata, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Resultados salvos: {self.results_file}")
        return str(self.results_file)
    
    def generate_feedback(self, 
                         success: bool,
                         decisions_made: List[Dict[str, Any]],
                         problems_found: List[str] = None,
                         recommendations: List[str] = None,
                         metrics: Dict[str, Any] = None) -> str:
        """
        OBRIGATÓRIO: Gera feedback estruturado para o Coordinator.
        
        Args:
            success: Se o processamento foi bem-sucedido
            decisions_made: Lista de decisões tomadas pelo agente
            problems_found: Problemas encontrados durante processamento
            recommendations: Recomendações para próximos agentes
            metrics: Métricas de performance e confiança
            
        Returns:
            Caminho do arquivo de feedback
        """
        feedback = {
            'agent': self.name,
            'role': self.role,
            'feedback_timestamp': time.time(),
            'processing_time': time.time() - self.start_time,
            'execution_summary': {
                'success': success,
                'total_decisions': len(decisions_made),
                'problems_count': len(problems_found) if problems_found else 0,
                'recommendations_count': len(recommendations) if recommendations else 0
            },
            'decisions_made': decisions_made,
            'problems_found': problems_found or [],
            'recommendations_for_next_agents': recommendations or [],
            'performance_metrics': metrics or {},
            'coordinator_evaluation_needed': not success or len(problems_found or []) > 0
        }
        
        with open(self.feedback_file, 'w', encoding='utf-8') as f:
            json.dump(feedback, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Feedback gerado: {self.feedback_file}")
        return str(self.feedback_file)
    
    def get_agent_instructions(self, processing_plan: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        UTILITÁRIO: Extrai instruções específicas para este agente.
        
        Args:
            processing_plan: Plano completo do Coordinator
            
        Returns:
            Instruções específicas do agente ou None
        """
        return processing_plan['strategy']['agent_instructions'].get(self.name)
    
    def create_decision_record(self, 
                              decision_type: str,
                              decision: str,
                              reasoning: str,
                              confidence: float,
                              data_used: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        UTILITÁRIO: Cria registro estruturado de decisão.
        
        Args:
            decision_type: Tipo da decisão (ex: "audio_processing", "content_selection")
            decision: Decisão tomada
            reasoning: Justificativa da decisão
            confidence: Nível de confiança (0.0 a 1.0)
            data_used: Dados que influenciaram a decisão
            
        Returns:
            Registro estruturado da decisão
        """
        return {
            'decision_type': decision_type,
            'decision': decision,
            'reasoning': reasoning,
            'confidence': confidence,
            'timestamp': time.time(),
            'data_used': data_used or {}
        }
    
    def log_processing_step(self, step_name: str, status: str, details: str = ""):
        """
        UTILITÁRIO: Log padronizado de etapas de processamento.
        
        Args:
            step_name: Nome da etapa
            status: Status (SUCCESS, ERROR, WARNING, INFO)
            details: Detalhes adicionais
        """
        status_icons = {
            'SUCCESS': '✅',
            'ERROR': '❌', 
            'WARNING': '⚠️',
            'INFO': 'ℹ️'
        }
        
        icon = status_icons.get(status, '📝')
        print(f"   {icon} {step_name}: {details}")

# Exemplo de constantes para padronização
class AgentStatus:
    """Constantes para status de agentes"""
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"

class DecisionTypes:
    """Constantes para tipos de decisões"""
    AUDIO_PROCESSING = "audio_processing"
    CONTENT_SELECTION = "content_selection"
    VIDEO_ENHANCEMENT = "video_enhancement"
    QUALITY_EVALUATION = "quality_evaluation"
    CHUNKING_STRATEGY = "chunking_strategy"

# Exemplo de implementação (será removido quando agentes reais herdarem)
class ExampleAgent(BaseAgent):
    """Exemplo de como implementar um agente usando BaseAgent"""
    
    def __init__(self):
        super().__init__("EXAMPLE", "EXAMPLE_SPECIALIST")
    
    def execute(self) -> bool:
        """Implementação exemplo do método execute"""
        # 1. Carregar plano
        plan = self.load_processing_plan()
        if not plan:
            return False
        
        # 2. Processar conforme instruções
        decisions = []
        
        # Exemplo de decisão
        decision = self.create_decision_record(
            decision_type=DecisionTypes.AUDIO_PROCESSING,
            decision="preserve_original",
            reasoning="No speech detected in audio",
            confidence=0.95,
            data_used={"audio_duration": 60, "speech_segments": 0}
        )
        decisions.append(decision)
        
        # 3. Salvar resultados
        results = {
            "status": "completed",
            "items_processed": 1,
            "decisions_count": len(decisions)
        }
        self.save_results(results)
        
        # 4. Gerar feedback
        self.generate_feedback(
            success=True,
            decisions_made=decisions,
            recommendations=["Next agent should focus on visual elements"]
        )
        
        return True

if __name__ == "__main__":
    # Teste da classe base
    agent = ExampleAgent()
    print(f"\nTestando {agent.name}...")
    success = agent.execute()
    print(f"Resultado: {'✅ Sucesso' if success else '❌ Falha'}")