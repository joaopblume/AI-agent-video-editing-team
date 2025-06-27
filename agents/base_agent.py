#!/usr/bin/env python3
"""
Base Agent - Abstract class used to standardize the architecture of all agents
=================================================================

This class defines the mandatory structure and methods that all agents must implement.

MANDATORY RESPONSIBILITIES:
- Standardized folder structure
- JSON reporting system for the Coordinator
- Structured feedback between agents
- Loading instructions from the Coordinator
- Saving results and analyses

AGENTS IN THE SYSTEM:
- RICO: Video Chunking Specialist
- FOSTER: Soundtrack Specialist
- DAVID: Audio Cleaning Specialist  
- SAIMON: Content Selection Specialist
- CLOE: Dynamic Editing Specialist
- SHEYLA: Quality Control Specialist
- NIALL: Subtitle Specialist
"""

import os
import json
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any, Optional

class BaseAgent(ABC):
    """
    Abstract class for all agents in the video editing system.

    MANDATORY STRUCTURE:
    ====================

    1. DIRECTORIES:
       - processing/{agent_name}/     # Main folder for the agent
       - processing/chunks/           # Video chunks (Rico)
       - processing/coordinator/      # Plans and reports from the Coordinator

    2. MANDATORY FILES:
       - {agent_name}_analysis_*.json      # Detailed analyses
       - {agent_name}_results.json         # Consolidated results
       - {agent_name}_feedback.json        # Feedback for Coordinator

    3. MANDATORY METHODS:
       - load_processing_plan()            # Loads instructions from the Coordinator
       - execute()                         # Método principal de processamento
       - generate_feedback()               # Feedback para Coordinator
       - save_results()                    # Salva resultados finais
    """
    
    def __init__(self, agent_name: str, role: str):
        """
        Initializes the BaseAgent with the agent's name and role.
        
        Args:
            agent_name: (RICO, DAVID, SAIMON, CLOE, SHEYLA)
            role: (eg: AUDIO_CLEANING_SPECIALIST)
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
        
        print(f"🤖 {self.name} initializing")
        print(f"📋 Role: {self.role}")
    
    def load_processing_plan(self) -> Optional[Dict[str, Any]]:
        """
        Loads processing plan from the Coordinator.

        Returns:
            Dict com instruções do Coordinator ou None se não encontrado
        """
        print(f"\n📋 {self.name}: Loading processing plan...")
        
        if not self.workflow_plan_file.exists():
            print(f"Plan not found: {self.workflow_plan_file}")
            return None
        
        try:
            with open(self.workflow_plan_file, 'r', encoding='utf-8') as f:
                plan = json.load(f)
            
            # Verificar se este agente está na lista de agentes selecionados
            if self.name not in plan.get('selected_agents', []):
                print(f"{self.name} was not selected for this plan.")
                return None

            print(f"Plan loaded - {self.name} selected for processing")
            return plan
            
        except Exception as e:
            print(f"Error loading plan: {e}")
            return None
    
    @abstractmethod
    def execute(self) -> bool:
        """
        Main processing method for the agent.
        
        Must implements:
        1. Load processing plan from the Coordinator
        2. Process according to instructions
        3. Save detailed analyses
        4. Generate feedback for Coordinator
        5. Save final results
        
        Returns:
            bool: True if processing was successful, False otherwise
        """
        pass
    
    def save_analysis(self, analysis_data: Dict[str, Any], item_name: str) -> str:
        """
        Saves detailed analysis for a specific item.

        Args:
            analysis_data: Analysis data
            item_name: Name of the analyzed item

        Returns:
            Path to the saved file
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

        print(f"Saved Analysis: {analysis_file.name}")
        return str(analysis_file)
    
    def save_results(self, results: Dict[str, Any]) -> str:
        """
        Saves consolidated results from the agent.

        Args:
            results: Processing results

        Returns:
            Path to the results file
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

        print(f"Saved Results: {self.results_file}")
        return str(self.results_file)
    
    def generate_feedback(self, 
                         success: bool,
                         decisions_made: List[Dict[str, Any]],
                         problems_found: List[str] = None,
                         recommendations: List[str] = None,
                         metrics: Dict[str, Any] = None) -> str:
        """
        Generates structured feedback for the Coordinator.

        Args:
            success: If the processing was successful
            decisions_made: List of decisions made by the agent
            problems_found: Problems found during processing
            recommendations: Recommendations for next agents
            metrics: Performance and confidence metrics

        Returns:
            Path to the feedback file
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

        print(f"Generated Feedback: {self.feedback_file}")
        return str(self.feedback_file)
    
    def get_agent_instructions(self, processing_plan: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extracts specific instructions for this agent.

        Args:
            processing_plan: Complete plan from the Coordinator

        Returns:
            Specific instructions for the agent or None
        """
        return processing_plan['strategy']['agent_instructions'].get(self.name)
    
    def create_decision_record(self, 
                              decision_type: str,
                              decision: str,
                              reasoning: str,
                              confidence: float,
                              data_used: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a structured record of a decision made by the agent.
        
        Args:
            decision_type: Decision Type (ex: "audio_processing", "content_selection")
            decision: Decision made
            reasoning: Justification for the decision
            confidence: Confidence level (0.0 to 1.0)
            data_used: Data that influenced the decision

        Returns:
            Structured record of the decision
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
        Standardized logging for processing steps.
        
        Args:
            step_name: Name of the step
            status: Status (SUCCESS, ERROR, WARNING, INFO)
            details: Additional details
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
    """Agent status constants"""
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"

class DecisionTypes:
    """Decision types constants"""
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