#!/usr/bin/env python3
"""
Pipeline Orchestrator - Orquestrador Central do Sistema de Edição de Vídeo com IA
=================================================================================

Este arquivo é o CENTRO DE COMANDO que:
1. Pede ao Coordinator para selecionar agentes necessários
2. Instancia APENAS os agentes selecionados (economia de recursos)
3. Executa o workflow em sequência conforme plano do Coordinator
4. Faz o Coordinator escutar feedbacks e atualizar status
5. Controla fluxo automático entre agentes

FLUXO INTELIGENTE:
1. Coordinator analisa instrução e seleciona agentes necessários
2. Orchestrator instancia APENAS agentes selecionados
3. Orchestrator executa agentes na sequência definida
4. Cada agente gera feedback automático
5. Coordinator recebe feedback e atualiza workflow
6. Orchestrator verifica próxima etapa e continua
7. Coordinator gera relatório final quando completo

OTIMIZAÇÕES:
- Instancia apenas agentes necessários (economia de memória)
- Não carrega APIs desnecessárias (economia de tempo)
- Escalável para muitos agentes futuros
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# Importar Coordinator (sempre necessário)
from agents.coordinator import Coordinator

class PipelineOrchestrator:
    """
    Orquestrador Central - Instancia e executa APENAS agentes selecionados.
    
    FILOSOFIA:
    - Coordinator decide QUAIS agentes usar
    - Orchestrator instancia APENAS os necessários
    - Executar pipeline de forma eficiente e econômica
    """
    
    def __init__(self):
        self.name = "PIPELINE_ORCHESTRATOR"
        self.start_time = time.time()
        
        # Coordinator (sempre necessário para decisões)
        self.coordinator = Coordinator()
        
        # Agentes serão instanciados sob demanda
        self.active_agents = {}
        self.current_workflow = None
        self.execution_log = []
        
        print(f"🎭 {self.name}: Orquestrador inicializado")
        print(f"🧠 Coordinator carregado para tomada de decisões")
    
    def _instantiate_agent(self, agent_name: str) -> bool:
        """
        Instancia um agente específico sob demanda.
        Só carrega o que realmente vai usar!
        """
        print(f"🤖 Instanciando {agent_name}...")
        
        try:
            if agent_name == 'DAVID':
                from agent_david import AgentDavid
                self.active_agents[agent_name] = AgentDavid()
                print(f"   ✅ Agent David carregado")
                return True
                
            elif agent_name == 'RICO':
                from agent_rico import AgenteRico
                self.active_agents[agent_name] = AgenteRico()
                print(f"   ✅ Agent Rico carregado")
                return True
                
            elif agent_name == 'SAIMON':
                # from agent_saimon import AgentSaimon
                # self.active_agents[agent_name] = AgentSaimon()
                print(f"   ⚠️ Agent Saimon ainda não implementado")
                return False
                
            elif agent_name == 'CLOE':
                # from agent_cloe import AgentCloe
                # self.active_agents[agent_name] = AgentCloe()
                print(f"   ⚠️ Agent Cloe ainda não implementado")
                return False
                
            elif agent_name == 'SHEYLA':
                # from agent_sheyla import AgentSheyla
                # self.active_agents[agent_name] = AgentSheyla()
                print(f"   ⚠️ Agent Sheyla ainda não implementado")
                return False
                
            else:
                print(f"   ❌ Agente desconhecido: {agent_name}")
                return False
                
        except ImportError as e:
            print(f"   ❌ Erro ao importar {agent_name}: {e}")
            return False
        except Exception as e:
            print(f"   ❌ Erro ao instanciar {agent_name}: {e}")
            return False
    
    def create_intelligent_plan(self, user_instruction: str) -> bool:
        """
        Usa o Coordinator para criar plano inteligente com seleção de agentes.
        """
        print(f"\n{'='*60}")
        print(f"🎬 {self.name}: CRIANDO PLANO INTELIGENTE")
        print(f"{'='*60}")
        
        try:
            # Coordinator faz toda análise e seleção inteligente
            success = self.coordinator.coordinate_processing(user_instruction)
            
            if success:
                # Carregar workflow criado
                self.current_workflow = self._load_current_workflow()
                if self.current_workflow:
                    selected_agents = self.current_workflow['selected_agents']
                    skipped_agents = self.current_workflow.get('skipped_agents', [])
                    
                    print(f"✅ Plano inteligente criado!")
                    print(f"   🎯 Agentes selecionados: {', '.join(selected_agents)}")
                    print(f"   ⏭️ Agentes pulados: {', '.join(skipped_agents)}")
                    print(f"   💰 Otimização: {self.current_workflow.get('optimization_summary', 'N/A')}")
                    
                    return True
                else:
                    print(f"❌ Falha ao carregar workflow criado")
                    return False
            else:
                print(f"❌ Falha na criação do plano")
                return False
                
        except Exception as e:
            print(f"❌ Erro na criação do plano: {e}")
            return False
    
    def _load_current_workflow(self) -> Optional[Dict[str, Any]]:
        """Carrega workflow atual do Coordinator"""
        workflow_file = Path('processing/coordinator/workflow_plan.json')
        
        if not workflow_file.exists():
            return None
        
        try:
            with open(workflow_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Erro ao carregar workflow: {e}")
            return None
    
    def instantiate_selected_agents(self) -> bool:
        """
        Instancia APENAS os agentes selecionados pelo Coordinator.
        Esta é a otimização chave!
        """
        if not self.current_workflow:
            print(f"❌ Nenhum workflow carregado")
            return False
        
        selected_agents = self.current_workflow['selected_agents']
        
        print(f"\n🎯 {self.name}: INSTANCIANDO APENAS AGENTES SELECIONADOS")
        print(f"   Total a instanciar: {len(selected_agents)}")
        
        success_count = 0
        
        for agent_name in selected_agents:
            if self._instantiate_agent(agent_name):
                success_count += 1
        
        print(f"\n📊 Resultado da instanciação:")
        print(f"   ✅ Sucesso: {success_count}/{len(selected_agents)}")
        print(f"   🧠 Memória economizada: Não instanciou {5 - len(selected_agents)} agentes desnecessários")
        
        return success_count > 0
    
    def execute_pipeline(self) -> bool:
        """
        Executa pipeline com os agentes ativos.
        """
        if not self.current_workflow:
            print(f"❌ Nenhum workflow carregado")
            return False
        
        print(f"\n{'='*60}")
        print(f"🚀 {self.name}: EXECUTANDO PIPELINE OTIMIZADO")
        print(f"{'='*60}")
        
        workflow_steps = self.current_workflow['workflow_steps']
        
        print(f"📋 Executando {len(workflow_steps)} etapas otimizadas")
        print(f"🤖 Agentes ativos: {', '.join(self.active_agents.keys())}")
        
        # Executar cada etapa em sequência
        for step in workflow_steps:
            agent_name = step['agent']
            
            print(f"\n--- ETAPA {step['step_number']}: {agent_name} ---")
            
            # Verificar se agente foi instanciado
            if agent_name not in self.active_agents:
                print(f"⚠️ {agent_name} não foi instanciado - pulando")
                self._update_step_status(agent_name, 'SKIPPED', 'Agente não instanciado')
                continue
            
            # Atualizar status para IN_PROGRESS
            self._update_step_status(agent_name, 'IN_PROGRESS')
            
            # Executar agente
            success = self._execute_agent(agent_name, step)
            
            if success:
                # Agente foi executado, processar feedback
                self._process_agent_feedback(agent_name)
                self._update_step_status(agent_name, 'COMPLETED')
                print(f"✅ {agent_name} concluído com sucesso")
            else:
                self._update_step_status(agent_name, 'FAILED', 'Falha na execução')
                print(f"❌ {agent_name} falhou")
                
                # Decidir se continua ou para
                if step.get('required', True):
                    print(f"💥 Etapa obrigatória falhou - parando pipeline")
                    return False
                else:
                    print(f"⚠️ Etapa opcional falhou - continuando")
        
        # Pipeline concluído
        print(f"\n🎉 PIPELINE OTIMIZADO CONCLUÍDO!")
        self._generate_final_report()
        return True
    
    def _execute_agent(self, agent_name: str, step: Dict[str, Any]) -> bool:
        """Executa um agente específico"""
        try:
            agent = self.active_agents[agent_name]
            
            print(f"🤖 Executando {agent_name}...")
            print(f"   📝 Descrição: {step.get('description', 'N/A')}")
            print(f"   💰 Impacto de custo: {step.get('cost_impact', 'medium')}")
            
            # Executar método execute() do agente (BaseAgent pattern)
            if hasattr(agent, 'execute'):
                return agent.execute()
            else:
                print(f"⚠️ Agente {agent_name} não implementa execute() - usando método legado")
                # Fallback para métodos específicos do agente
                if agent_name == 'DAVID' and hasattr(agent, 'execute_ai_audio_cleaning'):
                    return agent.execute_ai_audio_cleaning()
                else:
                    print(f"❌ Não foi possível executar {agent_name}")
                    return False
                    
        except Exception as e:
            print(f"❌ Erro ao executar {agent_name}: {e}")
            return False
    
    def _process_agent_feedback(self, agent_name: str):
        """Processa feedback do agente através do Coordinator"""
        print(f"📨 Processando feedback do {agent_name}...")
        
        try:
            # Coordinator recebe e processa feedback
            feedback = self.coordinator.receive_agent_feedback(agent_name)
            
            if feedback:
                # Coordinator avalia trabalho do agente
                evaluation = self.coordinator.evaluate_agent_work(feedback)
                
                # Adicionar ao log de execução
                self.execution_log.append({
                    'agent': agent_name,
                    'timestamp': time.time(),
                    'feedback_processed': True,
                    'evaluation_score': evaluation.get('overall_score', 0),
                    'coordinator_decision': evaluation.get('coordinator_decision', 'UNKNOWN')
                })
                
                print(f"   ✅ Feedback processado - Score: {evaluation.get('overall_score', 0):.2f}")
            else:
                print(f"   ⚠️ Nenhum feedback encontrado para {agent_name}")
                
        except Exception as e:
            print(f"   ❌ Erro ao processar feedback: {e}")
    
    def _update_step_status(self, agent_name: str, status: str, message: str = None):
        """Atualiza status da etapa no workflow"""
        try:
            self.coordinator.update_workflow_step(agent_name, status)
            
            if message:
                print(f"   📊 {agent_name}: {status} - {message}")
                
        except Exception as e:
            print(f"   ⚠️ Erro ao atualizar status: {e}")
    
    def _generate_final_report(self):
        """Gera relatório final através do Coordinator"""
        print(f"\n📋 Gerando relatório final...")
        
        try:
            # Coletar avaliações de todos os agentes executados
            executed_agents = [log['agent'] for log in self.execution_log if log.get('feedback_processed')]
            
            if executed_agents:
                self.coordinator.evaluate_complete_pipeline(executed_agents)
                print(f"✅ Relatório final gerado")
            else:
                print(f"⚠️ Nenhum agente executado - relatório não gerado")
                
        except Exception as e:
            print(f"❌ Erro ao gerar relatório: {e}")
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Retorna status atual do pipeline"""
        if not self.current_workflow:
            return {'status': 'NO_WORKFLOW'}
        
        workflow_status = self.coordinator.get_workflow_status()
        
        return {
            'orchestrator': self.name,
            'execution_time': time.time() - self.start_time,
            'workflow_status': workflow_status,
            'active_agents': list(self.active_agents.keys()),
            'total_agents_available': 5,  # Rico, David, Saimon, Cloe, Sheyla
            'memory_saved_agents': 5 - len(self.active_agents),
            'execution_log': self.execution_log
        }
    
    def run_complete_pipeline(self, user_instruction: str) -> bool:
        """
        Método principal - executa pipeline completo otimizado.
        """
        print(f"\n{'='*80}")
        print(f"🎭 {self.name}: PIPELINE INTELIGENTE E OTIMIZADO")
        print(f"{'='*80}")
        print(f"💬 Instrução: {user_instruction}")
        
        # Etapa 1: Coordinator cria plano inteligente
        if not self.create_intelligent_plan(user_instruction):
            print(f"❌ Falha na criação do plano")
            return False
        
        # Etapa 2: Instanciar APENAS agentes selecionados
        if not self.instantiate_selected_agents():
            print(f"❌ Falha na instanciação dos agentes")
            return False
        
        # Etapa 3: Executar pipeline otimizado
        if not self.execute_pipeline():
            print(f"❌ Falha na execução do pipeline")
            return False
        
        # Etapa 4: Mostrar status final
        final_status = self.get_pipeline_status()
        print(f"\n📊 PIPELINE INTELIGENTE FINALIZADO!")
        print(f"⏱️ Tempo total: {final_status['execution_time']:.1f}s")
        print(f"🤖 Agentes usados: {len(final_status['active_agents'])}/{final_status['total_agents_available']}")
        print(f"💾 Economia de memória: {final_status['memory_saved_agents']} agentes não instanciados")
        print(f"📋 Status: {final_status['workflow_status']['current_status']}")
        
        return True

def main():
    """Função principal do Pipeline Orchestrator"""
    print("🎭 PIPELINE ORCHESTRATOR INTELIGENTE - Sistema de Edição de Vídeo com IA")
    print("=" * 80)
    print("🎯 OTIMIZADO: Instancia apenas agentes necessários!")
    
    orchestrator = PipelineOrchestrator()
    
    print("\n🎬 OPÇÕES DISPONÍVEIS:")
    print("1. Executar pipeline completo otimizado (automático)")
    print("2. Criar apenas plano inteligente")
    print("3. Ver status do pipeline atual")
    
    choice = input("\nEscolha uma opção (1, 2 ou 3): ").strip()
    
    if choice == "1":
        # Pipeline completo otimizado
        user_instruction = input("\n💬 Digite sua instrução: ")
        
        if not user_instruction.strip():
            user_instruction = "Crie um video de no maximo 30 segundos com os lances chave dessa partida"
            print(f"📝 Usando instrução padrão: {user_instruction}")
        
        success = orchestrator.run_complete_pipeline(user_instruction)
        
        if success:
            print(f"\n🎉 Pipeline otimizado executado com sucesso!")
        else:
            print(f"\n💥 Pipeline falhou")
    
    elif choice == "2":
        # Apenas criar plano
        user_instruction = input("\n💬 Digite sua instrução: ")
        
        if not user_instruction.strip():
            user_instruction = "Crie um video de no maximo 30 segundos com os lances chave dessa partida"
            print(f"📝 Usando instrução padrão: {user_instruction}")
        
        success = orchestrator.create_intelligent_plan(user_instruction)
        
        if success:
            print(f"\n✅ Plano inteligente criado!")
            print(f"💡 Use opção 1 para executar com instanciação otimizada")
        else:
            print(f"\n❌ Falha ao criar plano")
    
    elif choice == "3":
        # Ver status
        status = orchestrator.get_pipeline_status()
        
        if status['status'] == 'NO_WORKFLOW':
            print(f"\n📋 Nenhum workflow ativo")
        else:
            print(f"\n📊 STATUS DO PIPELINE OTIMIZADO:")
            print(f"   Tempo de execução: {status['execution_time']:.1f}s")
            print(f"   Agentes ativos: {len(status['active_agents'])}/{status['total_agents_available']}")
            print(f"   Economia de memória: {status['memory_saved_agents']} agentes não instanciados")
            print(f"   Status do workflow: {status['workflow_status']['current_status']}")
    
    else:
        print("❌ Opção inválida!")

if __name__ == "__main__":
    main()