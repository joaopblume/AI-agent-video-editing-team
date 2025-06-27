#!/usr/bin/env python3
"""
Coordinator - Agente coordenador do pipeline de edição de vídeo
Gerencia todo o fluxo entre agentes e executa instruções do usuário
"""

import os
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional

# Carregar variáveis do .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Se dotenv não estiver instalado, tentar carregar manualmente
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

class Coordinator:
    """
    Coordenador do Pipeline de Edição de Vídeo para YouTube
    
    MISSÃO: Coordenar todos os agentes para criar vídeos otimizados para YouTube
    seguindo instruções específicas do usuário
    """
    
    def __init__(self):
        self.name = "COORDINATOR"
        self.role = "PIPELINE_MANAGER"
        self.processing_dir = Path('processing')
        self.chunks_dir = self.processing_dir / 'chunks'
        self.coordinator_dir = self.processing_dir / 'coordinator'
        self.coordinator_dir.mkdir(parents=True, exist_ok=True)
        self.system_prompt = self._get_system_prompt()
        
        print(f"🤖 {self.name} inicializado")
        print(f"📋 Função: {self.role}")
    
    def _get_system_prompt(self) -> str:
        """Prompt completo do sistema para o Coordinator"""
        return """
        🎬 COORDINATOR - ESPECIALISTA EM EDIÇÃO DE VÍDEO PARA YOUTUBE

        IDENTIDADE:
        Você é um coordenador experiente de edição de vídeos para YouTube, especializado em criar conteúdo viral e engajante. Você gerencia uma equipe de agentes especialistas para transformar vídeos brutos em conteúdo otimizado para diferentes formatos do YouTube.

        SUA EQUIPE:
        - RICO: Especialista em chunking de vídeos (já processou os chunks)
        - DAVID: Especialista em limpeza de áudio (remove pausas, gagueiras, "hmm"s e vícios de linguagem)
        - SAIMON: Especialista em seleção de conteúdo (identifica os momentos relevantes do vídeo)
        - CLOE: Especialista em edição dinâmica (efeitos, música, cortes)
        - SHEYLA: Especialista em controle de qualidade (avalia resultado final)

        CONTEXTO DE TRABALHO:
        - Você recebe chunks de vídeo já processados pelo RICO
        - Você tem acesso a um manifesto com informações dos chunks
        - Você recebe instruções específicas do usuário sobre o que criar
        - Você coordena os agentes na ordem correta para atingir o objetivo

        TIPOS DE CONTEÚDO YOUTUBE:
        1. SHORTS (até 60s): Vertical, dinâmico, hooks rápidos
        2. VÍDEOS LONGOS (8-15min): Horizontal, ritmo variado, storytelling
        3. HIGHLIGHTS (2-5min): Momentos épicos, alta energia
        4. TUTORIAIS: Didático, pausado, explicativo

        FLUXO DE TRABALHO:
        1. Analisar chunks disponíveis e manifesto
        2. Compreender instrução específica do usuário
        3. Definir estratégia de edição baseada no tipo de conteúdo
        4. Coordenar agentes na sequência otimizada:
           - DAVID: Limpar áudio primeiro
           - SAIMON: Selecionar melhores momentos
           - CLOE: Aplicar edição dinâmica
           - SHEYLA: Avaliar qualidade final
        5. Iterar até atingir qualidade desejada

        EXPERTISE EM GAMING:
        - Identificar jogadas épicas (chutes bonitos, decisivos, jogadas de equipe, habilidades especiais)
        - Reconhecer momentos de tensão e alívio cômico
        - Otimizar para audiência gamer (18-35 anos)
        - Usar linguagem e referências da comunidade

        REGRAS DE OURO:
        - SEMPRE manter contexto entre os agentes
        - SEMPRE explicar decisões para a equipe
        - SEMPRE considerar métricas do YouTube (retenção, engagement)
        - NUNCA perder foco no objetivo final do usuário
        - SEMPRE adaptar estratégia conforme feedback dos agentes

        COMUNICAÇÃO:
        - Seja claro e direto com os agentes
        - Forneça contexto completo para cada tarefa
        - Monitore progresso e ajuste estratégia se necessário
        - Documente decisões para aprendizado futuro
        """
    
    def load_chunks_manifest(self) -> Optional[Dict[str, Any]]:
        """Carrega o manifesto de chunks criado pelo Agente Rico"""
        print(f"\n📋 {self.name}: Carregando manifesto de chunks...")
        
        manifest_files = list(self.chunks_dir.glob('*_manifest.json'))
        
        if not manifest_files:
            print(f"❌ Nenhum manifesto encontrado em {self.chunks_dir}")
            return None
        
        # Usar o manifesto mais recente
        latest_manifest = max(manifest_files, key=lambda f: f.stat().st_mtime)
        
        try:
            with open(latest_manifest, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            print(f"✅ Manifesto carregado: {latest_manifest.name}")
            print(f"📊 Total de chunks: {manifest['total_chunks']}")
            
            return manifest
            
        except Exception as e:
            print(f"❌ Erro ao carregar manifesto: {e}")
            return None
    
    def analyze_content_requirements(self, user_instruction: str) -> Dict[str, Any]:
        """
        Analisa o conteúdo disponível e requisitos do usuário para entender o contexto.
        """
        print(f"\n🔍 {self.name}: Analisando conteúdo e requisitos...")
        
        # Carregar manifesto de chunks para entender o conteúdo
        manifest = self.load_chunks_manifest()
        if not manifest:
            print("⚠️ Manifesto não encontrado - análise limitada")
            manifest = {'chunks': [], 'total_chunks': 0}
        
        # Análise básica do conteúdo disponível
        content_analysis = {
            'total_chunks': manifest.get('total_chunks', 0),
            'total_duration': sum(chunk.get('duration', 0) for chunk in manifest.get('chunks', [])),
            'has_audio_tracks': True,  # Assumir que sempre tem áudio
            'estimated_content_type': 'gameplay',  # Baseado no contexto atual
            'requires_chunking': manifest.get('total_chunks', 0) == 0
        }
        
        print(f"📊 Conteúdo disponível:")
        print(f"   Chunks: {content_analysis['total_chunks']}")
        print(f"   Duração total: {content_analysis['total_duration']:.1f}s")
        
        return content_analysis
    
    def select_required_agents(self, user_instruction: str, content_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Seleciona inteligentemente quais agentes são necessários baseado no objetivo.
        Usa IA para otimizar custos evitando etapas desnecessárias.
        """
        print(f"\n🎯 {self.name}: Selecionando agentes necessários com IA...")
        
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not gemini_api_key:
            raise Exception("❌ GEMINI_API_KEY obrigatória!")
        
        selection_prompt = f"""Você é um COORDINATOR especialista em edição de vídeo para YouTube. Analise a instrução do usuário e o conteúdo disponível para SELECIONAR APENAS os agentes necessários.

INSTRUÇÃO DO USUÁRIO:
"{user_instruction}"

ANÁLISE DO CONTEÚDO:
{json.dumps(content_analysis, indent=2, ensure_ascii=False)}

AGENTES DISPONÍVEIS:
1. RICO (Video Chunking): Divide vídeo em chunks para processamento otimizado
   - Necessário: Quando não há chunks disponíveis
   - Custo: Baixo (processamento local)

2. DAVID (Audio Cleaning): Remove pausas, gagueiras, vícios de linguagem
   - Necessário: Quando há narração do jogador/streamer
   - Custo: Médio (Whisper + Gemini)
   - Pular quando: Gameplay silencioso, apenas sons do jogo

3. SAIMON (Content Selection): Seleciona melhores momentos do vídeo
   - Necessário: Para highlights, compilation, moments épicos
   - Custo: Alto (Video Intelligence + Gemini)
   - Pular quando: Vídeo já tem duração desejada

4. CLOE (Video Enhancement): Adiciona música, efeitos, crop, transições
   - Necessário: Para conteúdo dinâmico, shorts, vídeos profissionais
   - Custo: Médio (Vision API + processamento local)
   - Pular quando: Usuário quer vídeo simples/raw

5. SHEYLA (Quality Evaluation): Avalia qualidade final e dá feedback
   - Necessário: Para produção profissional, controle de qualidade
   - Custo: Médio (Gemini + Vision API)
   - Opcional: Para testes rápidos

REGRAS DE OTIMIZAÇÃO:
- MINIMIZAR CUSTOS: Use apenas agentes essenciais
- GAMEPLAY SILENCIOSO: Pular DAVID se não há narração
- VÍDEO CURTO: Pular SAIMON se já tem duração desejada
- PRODUÇÃO SIMPLES: Pular CLOE se usuário não pede efeitos
- TESTE RÁPIDO: SHEYLA opcional

Retorne APENAS um JSON válido:
{{
    "selected_agents": ["RICO", "SAIMON", "CLOE"],
    "workflow_sequence": [
        {{
            "agent": "RICO",
            "reason": "necessário para criar chunks",
            "cost_impact": "low",
            "skippable": false
        }},
        {{
            "agent": "SAIMON", 
            "reason": "selecionar melhores momentos para highlights",
            "cost_impact": "high",
            "skippable": false
        }},
        {{
            "agent": "CLOE",
            "reason": "adicionar efeitos dinâmicos para short",
            "cost_impact": "medium", 
            "skippable": false
        }}
    ],
    "skipped_agents": [
        {{
            "agent": "DAVID",
            "reason": "gameplay silencioso sem narração detectada",
            "cost_saved": "medium"
        }},
        {{
            "agent": "SHEYLA",
            "reason": "produção simples não requer avaliação complexa",
            "cost_saved": "medium"
        }}
    ],
    "estimated_cost_category": "medium",
    "optimization_summary": "Economia de 40% pulando agentes desnecessários",
    "total_agents_needed": 3,
    "pipeline_complexity": "medium"
}}

IMPORTANTE: Seja conservador mas eficiente. Melhor incluir um agente a mais que faltar um essencial."""
        
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_api_key}"
            
            headers = {'Content-Type': 'application/json'}
            
            payload = {
                "contents": [{"parts": [{"text": selection_prompt}]}],
                "generationConfig": {
                    "temperature": 0.3,
                    "topK": 1,
                    "topP": 1,
                    "maxOutputTokens": 800
                }
            }
            
            print("🤖 Enviando seleção para Gemini API...")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code != 200:
                raise Exception(f"Erro na API: {response.status_code}")
            
            result = response.json()
            ai_response = result['candidates'][0]['content']['parts'][0]['text']
            
            # Limpar e parsear JSON
            clean_response = ai_response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]
            
            clean_response = clean_response.replace("'", '"')
            selection = json.loads(clean_response)
            
            print(f"✅ Seleção IA concluída!")
            print(f"   Agentes selecionados: {len(selection.get('selected_agents', []))}")
            print(f"   Agentes pulados: {len(selection.get('skipped_agents', []))}")
            print(f"   Otimização: {selection.get('optimization_summary', 'N/A')}")
            
            return selection
            
        except Exception as e:
            print(f"❌ Erro na seleção: {e}")
            # Fallback: usar todos os agentes
            return {
                'selected_agents': ['RICO', 'DAVID', 'SAIMON', 'CLOE', 'SHEYLA'],
                'workflow_sequence': [
                    {'agent': 'RICO', 'reason': 'fallback - todos agentes', 'cost_impact': 'low'},
                    {'agent': 'DAVID', 'reason': 'fallback - todos agentes', 'cost_impact': 'medium'},
                    {'agent': 'SAIMON', 'reason': 'fallback - todos agentes', 'cost_impact': 'high'},
                    {'agent': 'CLOE', 'reason': 'fallback - todos agentes', 'cost_impact': 'medium'},
                    {'agent': 'SHEYLA', 'reason': 'fallback - todos agentes', 'cost_impact': 'medium'}
                ],
                'skipped_agents': [],
                'selection_method': 'fallback_all',
                'error': str(e)
            }
    
    def analyze_user_instruction(self, user_instruction: str) -> Dict[str, Any]:
        """Analisa e interpreta a instrução do usuário usando IA"""
        print(f"\n🎯 {self.name}: Analisando instrução do usuário com IA...")
        print(f"💬 Instrução: '{user_instruction}'")
        
        # Análise básica da instrução
        instruction_analysis = {
            'original_instruction': user_instruction,
            'content_type': 'unknown',
            'duration_target': None,
            'focus_keywords': [],
            'platform_format': 'youtube',
            'priority_elements': []
        }
        
        # Usar IA para análise inteligente da instrução
        ai_analysis = self._analyze_with_ai(user_instruction)
        
        # Integrar análise da IA
        instruction_analysis.update(ai_analysis)
        
        # Detectar duração específica (mantém lógica manual para números)
        lower_instruction = user_instruction.lower()
        if 'segundos' in lower_instruction:
            words = lower_instruction.split()
            for i, word in enumerate(words):
                if word == 'segundos' and i > 0:
                    try:
                        duration = int(words[i-1])
                        instruction_analysis['duration_target'] = duration
                    except ValueError:
                        pass
        
        print(f"📊 Análise IA concluída:")
        print(f"   Tipo: {instruction_analysis['content_type']}")
        print(f"   Duração alvo: {instruction_analysis['duration_target']}s")
        print(f"   Palavras-chave: {instruction_analysis['focus_keywords']}")
        print(f"   Elementos prioritários: {instruction_analysis['priority_elements']}")
        
        return instruction_analysis
    
    def _analyze_with_ai(self, user_instruction: str) -> Dict[str, Any]:
        """Usa IA REAL (Gemini API) para analisar instrução do usuário"""
        
        analysis_prompt = f"""Analise esta instrução de edição de vídeo e extraia informações estruturadas:

INSTRUÇÃO: "{user_instruction}"

Retorne APENAS um JSON válido com esta estrutura:
{{
    "content_type": "short|highlights|compilation|tutorial|unknown",
    "duration_target": número_em_segundos_ou_null,
    "focus_keywords": ["palavra1", "palavra2", "palavra3"],
    "priority_elements": ["epic_moments", "fast_paced", "precision_shots", "team_plays", "comebacks"],
    "video_style": "dynamic|calm|epic|funny|educational",
    "target_audience": "gamer|general|kids|adults"
}}

REGRAS:
- focus_keywords: extraia palavras-chave relevantes do conteúdo que o usuário quer destacar
- Se mencionar "short" ou "shorts" = content_type: "short" e duration_target: 60
- Se mencionar "highlight" ou "melhores momentos" = content_type: "highlights"
- priority_elements: baseie-se no que o usuário quer destacar (bonito=epic_moments, rápido=fast_paced, etc)
- video_style: inferir do tom da instrução
- target_audience: inferir do contexto

Seja inteligente e contextual. Retorne APENAS o JSON, sem explicações."""
        
        try:
            # Usar Gemini API (gratuita)
            gemini_api_key = os.getenv('GEMINI_API_KEY')
            
            if not gemini_api_key:
                raise Exception("❌ GEMINI_API_KEY obrigatória! Configure a API key.")
            
            # Chamada para Gemini API (modelo atualizado)
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_api_key}"
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": analysis_prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "topK": 1,
                    "topP": 1,
                    "maxOutputTokens": 500
                }
            }
            
            print("🤖 Enviando para Gemini API...")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['candidates'][0]['content']['parts'][0]['text']
                
                print(f"✅ Resposta da IA recebida: {ai_response[:100]}...")
                
                # Extrair JSON da resposta
                try:
                    # Limpar resposta e extrair JSON
                    clean_response = ai_response.strip()
                    if clean_response.startswith('```json'):
                        clean_response = clean_response[7:]
                    if clean_response.endswith('```'):
                        clean_response = clean_response[:-3]
                    
                    # Corrigir aspas simples para duplas
                    clean_response = clean_response.replace("'", '"')
                    
                    ai_analysis = json.loads(clean_response)
                    
                    print("🎯 Análise IA bem-sucedida!")
                    return ai_analysis
                    
                except json.JSONDecodeError as e:
                    raise Exception(f"❌ IA retornou JSON inválido: {e}\nResposta: {ai_response}")
            else:
                raise Exception(f"Erro na API Gemini: {response.status_code} - {response.text}")
                
        except Exception as e:
            raise Exception(f"❌ Falha na análise IA: {e}")
    
    
    def create_processing_strategy(self, manifest: Dict[str, Any], instruction_analysis: Dict[str, Any], agent_selection: Dict[str, Any] = None) -> Dict[str, Any]:
        """Cria estratégia de processamento 100% gerada pela IA"""
        print(f"\n🎯 {self.name}: Criando estratégia com IA...")
        
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not gemini_api_key:
            raise Exception("❌ GEMINI_API_KEY obrigatória! Configure a API key.")
        
        strategy_prompt = f"""Você é um COORDINATOR experiente de edição de vídeo para YouTube. Crie uma estratégia COMPLETA de processamento baseada nos dados abaixo:

ANÁLISE DA INSTRUÇÃO:
{json.dumps(instruction_analysis, indent=2, ensure_ascii=False)}

MANIFESTO DOS CHUNKS:
- Total de chunks: {manifest['total_chunks']}
- Chunks disponíveis: {[chunk['filename'] for chunk in manifest['chunks']]}

AGENTES DISPONÍVEIS:
- DAVID: Especialista em limpeza de áudio (remove pausas, gagueiras, vícios)
- SAIMON: Especialista em seleção de conteúdo (identifica melhores momentos)  
- CLOE: Especialista em edição dinâmica (efeitos, música, cortes)
- SHEYLA: Especialista em controle de qualidade (avalia resultado final)

Retorne APENAS um JSON válido com esta estrutura:
{{
    "target_content_type": "{instruction_analysis['content_type']}",
    "target_duration": {instruction_analysis['duration_target']},
    "total_chunks": {manifest['total_chunks']},
    "processing_stages": ["DAVID_AUDIO_CLEANING", "SAIMON_...", "CLOE_...", "SHEYLA_QUALITY_CHECK"],
    "agent_instructions": {{
        "DAVID": {{
            "focus": "instrução específica baseada no tipo de conteúdo",
            "preserve_action_audio": true/false,
            "intensity_level": "low|medium|high",
            "chunks_to_process": {[chunk['filename'] for chunk in manifest['chunks']]}
        }},
        "SAIMON": {{
            "selection_criteria": {instruction_analysis['focus_keywords']},
            "target_duration": {instruction_analysis['duration_target']},
            "priority_elements": {instruction_analysis['priority_elements']},
            "content_type": "{instruction_analysis['content_type']}",
            "selection_strategy": "descrição de como selecionar baseado na instrução"
        }},
        "CLOE": {{
            "editing_style": "{instruction_analysis['content_type']}",
            "target_duration": {instruction_analysis['duration_target']},
            "video_style": "{instruction_analysis.get('video_style', 'dynamic')}",
            "add_music": true/false,
            "add_effects": true/false,
            "pacing": "fast|medium|slow",
            "transitions": "cuts|fades|dynamic"
        }},
        "SHEYLA": {{
            "quality_criteria": "{instruction_analysis['content_type']}",
            "target_metrics": "youtube_optimization",
            "target_audience": "{instruction_analysis.get('target_audience', 'gamer')}",
            "user_instruction": "{instruction_analysis['original_instruction']}",
            "success_criteria": "critérios específicos de aprovação"
        }}
    }}
}}

REGRAS OBRIGATÓRIAS:
1. Adapte as instruções ao tipo de conteúdo ({instruction_analysis['content_type']})
2. Use as palavras-chave: {instruction_analysis['focus_keywords']}
3. Priorize elementos: {instruction_analysis['priority_elements']}
4. Se for SHORT: foco em ritmo rápido, cortes dinâmicos
5. Se for HIGHLIGHTS: foco em momentos épicos, boa qualidade
6. Se for COMPILATION: foco em variedade e fluidez
7. DAVID sempre vem primeiro, SHEYLA sempre por último
8. Seja específico e detalhado nas instruções
9. IMPORTANTE: Use APENAS aspas duplas (") em todo o JSON, nunca aspas simples (')

Retorne APENAS o JSON válido, sem explicações, sem texto extra."""

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_api_key}"
            
            headers = {'Content-Type': 'application/json'}
            
            payload = {
                "contents": [{
                    "parts": [{"text": strategy_prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.2,
                    "topK": 1,
                    "topP": 1,
                    "maxOutputTokens": 1500
                }
            }
            
            print("🤖 Enviando estratégia para Gemini API...")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code != 200:
                raise Exception(f"Erro na API Gemini: {response.status_code} - {response.text}")
            
            result = response.json()
            ai_response = result['candidates'][0]['content']['parts'][0]['text']
            
            print(f"✅ Estratégia IA recebida: {ai_response[:100]}...")
            
            # Limpar e parsear JSON
            clean_response = ai_response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]
            
            # Corrigir aspas simples para duplas (Python list -> JSON)
            clean_response = clean_response.replace("'", '"')
            
            strategy = json.loads(clean_response)
            
            print(f"🎯 Estratégia IA criada com sucesso!")
            print(f"   Estágios: {len(strategy['processing_stages'])}")
            print(f"   Agentes: {len(strategy['agent_instructions'])}")
            
            return strategy
            
        except json.JSONDecodeError as e:
            raise Exception(f"❌ IA retornou JSON inválido: {e}\nResposta: {ai_response}")
        except Exception as e:
            raise Exception(f"❌ Falha na criação da estratégia: {e}")
    
    def create_workflow_plan(self, agent_selection: Dict[str, Any], instruction_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria plano de workflow com tracking de etapas baseado nos agentes selecionados.
        """
        print(f"\n📋 {self.name}: Criando plano de workflow otimizado...")
        
        workflow_plan = {
            'workflow_id': f"workflow_{int(time.time())}",
            'created_at': time.time(),
            'coordinator': self.name,
            'user_instruction': instruction_analysis['original_instruction'],
            'content_type': instruction_analysis['content_type'],
            'target_duration': instruction_analysis['duration_target'],
            'selected_agents': agent_selection['selected_agents'],
            'skipped_agents': [agent['agent'] for agent in agent_selection.get('skipped_agents', [])],
            'optimization_summary': agent_selection.get('optimization_summary', ''),
            'estimated_cost': agent_selection.get('estimated_cost_category', 'medium'),
            'workflow_steps': [],
            'step_tracking': {}
        }
        
        # Criar etapas baseadas nos agentes selecionados
        step_number = 1
        for workflow_item in agent_selection.get('workflow_sequence', []):
            agent_name = workflow_item['agent']
            
            step = {
                'step_number': step_number,
                'agent': agent_name,
                'description': workflow_item.get('reason', f'Processamento por {agent_name}'),
                'cost_impact': workflow_item.get('cost_impact', 'medium'),
                'status': 'PENDING',
                'required': not workflow_item.get('skippable', False),
                'dependencies': [] if step_number == 1 else [step_number - 1],
                'estimated_duration': self._estimate_step_duration(agent_name),
                'created_at': time.time()
            }
            
            workflow_plan['workflow_steps'].append(step)
            workflow_plan['step_tracking'][agent_name] = {
                'step_number': step_number,
                'status': 'PENDING',
                'started_at': None,
                'completed_at': None,
                'feedback_received': False,
                'evaluation_score': None
            }
            
            step_number += 1
        
        print(f"✅ Workflow criado com {len(workflow_plan['workflow_steps'])} etapas")
        print(f"   Agentes: {', '.join(workflow_plan['selected_agents'])}")
        print(f"   Economia: {workflow_plan['optimization_summary']}")
        
        return workflow_plan
    
    def _estimate_step_duration(self, agent_name: str) -> int:
        """Estima duração em segundos para cada agente"""
        durations = {
            'RICO': 30,     # Chunking é rápido
            'DAVID': 120,   # Audio processing com IA
            'SAIMON': 180,  # Video analysis é mais lenta
            'CLOE': 150,    # Video enhancement
            'SHEYLA': 90    # Quality evaluation
        }
        return durations.get(agent_name, 60)
    
    def update_workflow_step(self, agent_name: str, status: str, feedback_data: Dict[str, Any] = None) -> bool:
        """
        Atualiza status de uma etapa do workflow baseado no feedback do agente.
        """
        workflow_file = self.coordinator_dir / 'workflow_plan.json'
        
        if not workflow_file.exists():
            print(f"⚠️ Workflow plan não encontrado: {workflow_file}")
            return False
        
        try:
            with open(workflow_file, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
            
            if agent_name not in workflow['step_tracking']:
                print(f"⚠️ Agente {agent_name} não encontrado no workflow")
                return False
            
            # Atualizar status da etapa
            step_info = workflow['step_tracking'][agent_name]
            old_status = step_info['status']
            step_info['status'] = status
            
            if status == 'IN_PROGRESS' and old_status == 'PENDING':
                step_info['started_at'] = time.time()
            elif status in ['COMPLETED', 'FAILED']:
                step_info['completed_at'] = time.time()
                if feedback_data:
                    step_info['feedback_received'] = True
                    step_info['evaluation_score'] = feedback_data.get('overall_score')
            
            # Atualizar step na lista também
            for step in workflow['workflow_steps']:
                if step['agent'] == agent_name:
                    step['status'] = status
                    break
            
            # Verificar se pode avançar próxima etapa
            self._check_next_steps(workflow)
            
            # Salvar workflow atualizado
            with open(workflow_file, 'w', encoding='utf-8') as f:
                json.dump(workflow, f, indent=2, ensure_ascii=False)
            
            print(f"📊 Workflow atualizado: {agent_name} → {status}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao atualizar workflow: {e}")
            return False
    
    def _check_next_steps(self, workflow: Dict[str, Any]) -> None:
        """Verifica se próximas etapas podem ser iniciadas"""
        for step in workflow['workflow_steps']:
            if step['status'] == 'PENDING':
                # Verificar dependências
                dependencies_met = True
                for dep_step_num in step.get('dependencies', []):
                    dep_step = next((s for s in workflow['workflow_steps'] if s['step_number'] == dep_step_num), None)
                    if not dep_step or dep_step['status'] != 'COMPLETED':
                        dependencies_met = False
                        break
                
                if dependencies_met:
                    print(f"✅ Próxima etapa disponível: {step['agent']}")
                break
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Retorna status atual do workflow"""
        workflow_file = self.coordinator_dir / 'workflow_plan.json'
        
        if not workflow_file.exists():
            return {'status': 'NO_WORKFLOW', 'message': 'Nenhum workflow ativo'}
        
        try:
            with open(workflow_file, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
            
            total_steps = len(workflow['workflow_steps'])
            completed_steps = len([s for s in workflow['workflow_steps'] if s['status'] == 'COMPLETED'])
            failed_steps = len([s for s in workflow['workflow_steps'] if s['status'] == 'FAILED'])
            
            return {
                'workflow_id': workflow['workflow_id'],
                'total_steps': total_steps,
                'completed_steps': completed_steps,
                'failed_steps': failed_steps,
                'progress_percentage': (completed_steps / total_steps * 100) if total_steps > 0 else 0,
                'current_status': 'COMPLETED' if completed_steps == total_steps else 'IN_PROGRESS',
                'step_tracking': workflow['step_tracking'],
                'optimization_summary': workflow.get('optimization_summary', '')
            }
            
        except Exception as e:
            return {'status': 'ERROR', 'error': str(e)}
    
    def save_processing_plan(self, strategy: Dict[str, Any]) -> str:
        """Salva plano de processamento para os agentes"""
        plan_file = self.coordinator_dir / 'processing_plan.json'
        
        processing_plan = {
            'coordinator': self.name,
            'created_at': time.time(),
            'strategy': strategy,
            'status': 'READY_FOR_PROCESSING',
            'current_stage': 0,
            'system_context': self.system_prompt
        }
        
        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(processing_plan, f, indent=2, ensure_ascii=False)
        
        print(f"📋 Plano salvo: {plan_file}")
        return str(plan_file)
    
    def coordinate_processing(self, user_instruction: str) -> bool:
        """
        Método principal - coordena todo o processamento com seleção inteligente de agentes.
        """
        print(f"\n{'='*60}")
        print(f"🎬 {self.name}: INICIANDO COORDENAÇÃO INTELIGENTE")
        print(f"{'='*60}")
        
        # 1. Analisar conteúdo disponível
        content_analysis = self.analyze_content_requirements(user_instruction)
        
        # 2. Selecionar agentes necessários com IA
        agent_selection = self.select_required_agents(user_instruction, content_analysis)
        
        # 3. Analisar instrução do usuário
        instruction_analysis = self.analyze_user_instruction(user_instruction)
        
        # 4. Criar workflow plan otimizado
        workflow_plan = self.create_workflow_plan(agent_selection, instruction_analysis)
        
        # 5. Salvar workflow plan
        workflow_file = self.save_workflow_plan(workflow_plan)
        
        # 6. Se agentes selecionados precisam de estratégia detalhada, criar
        if 'DAVID' in agent_selection['selected_agents'] or 'SAIMON' in agent_selection['selected_agents']:
            # Carregar manifesto se necessário
            manifest = self.load_chunks_manifest()
            if manifest:
                strategy = self.create_processing_strategy(manifest, instruction_analysis, agent_selection)
                plan_file = self.save_processing_plan(strategy)
            else:
                print("⚠️ Manifesto não encontrado - alguns agentes podem precisar dele")
        
        print(f"\n🎉 {self.name}: COORDENAÇÃO INTELIGENTE CONCLUÍDA!")
        print(f"📋 Workflow otimizado: {workflow_file}")
        print(f"🎯 Agentes selecionados: {', '.join(agent_selection['selected_agents'])}")
        print(f"💰 Otimização: {agent_selection.get('optimization_summary', 'N/A')}")
        print(f"🚀 Próxima etapa: {workflow_plan['workflow_steps'][0]['agent'] if workflow_plan['workflow_steps'] else 'Nenhuma'}")
        
        return True
    
    def save_workflow_plan(self, workflow_plan: Dict[str, Any]) -> str:
        """Salva plano de workflow otimizado"""
        workflow_file = self.coordinator_dir / 'workflow_plan.json'
        
        with open(workflow_file, 'w', encoding='utf-8') as f:
            json.dump(workflow_plan, f, indent=2, ensure_ascii=False)
        
        print(f"📋 Workflow salvo: {workflow_file}")
        return str(workflow_file)
    
    def receive_agent_feedback(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Recebe e carrega feedback de um agente específico.
        
        Args:
            agent_name: Nome do agente (DAVID, SAIMON, CLOE, SHEYLA)
            
        Returns:
            Feedback do agente ou None se não encontrado
        """
        agent_dir = self.processing_dir / agent_name.lower()
        feedback_file = agent_dir / f"{agent_name.lower()}_feedback.json"
        
        if not feedback_file.exists():
            print(f"⚠️ Feedback do {agent_name} não encontrado: {feedback_file}")
            return None
        
        try:
            with open(feedback_file, 'r', encoding='utf-8') as f:
                feedback = json.load(f)
            
            print(f"📨 Feedback recebido do {agent_name}")
            print(f"   Status: {'✅ Sucesso' if feedback['execution_summary']['success'] else '❌ Falha'}")
            print(f"   Decisões: {feedback['execution_summary']['total_decisions']}")
            print(f"   Problemas: {feedback['execution_summary']['problems_count']}")
            
            return feedback
            
        except Exception as e:
            print(f"❌ Erro ao carregar feedback do {agent_name}: {e}")
            return None
    
    def evaluate_agent_work(self, agent_feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Avalia o trabalho de um agente usando IA (Claude 3.5 Haiku).
        
        Args:
            agent_feedback: Feedback completo do agente
            
        Returns:
            Avaliação estruturada do trabalho do agente
        """
        agent_name = agent_feedback['agent']
        print(f"\n🔍 {self.name}: Avaliando trabalho do {agent_name} com IA...")
        
        # Usar Gemini API (econômica conforme análise de APIs)
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not gemini_api_key:
            raise Exception("❌ GEMINI_API_KEY obrigatória para avaliação!")
        
        evaluation_prompt = f"""Você é um COORDINATOR experiente de edição de vídeo para YouTube. Avalie o trabalho do agente {agent_name} baseado no feedback recebido.

FEEDBACK COMPLETO DO AGENTE:
{json.dumps(agent_feedback, indent=2, ensure_ascii=False)}

CRITÉRIOS DE AVALIAÇÃO:
1. QUALIDADE DAS DECISÕES:
   - As decisões foram apropriadas para o contexto?
   - O reasoning foi consistente e lógico?
   - O nível de confiança foi adequado?

2. EXECUÇÃO TÉCNICA:
   - O agente completou suas tarefas conforme esperado?
   - Problemas foram identificados e reportados corretamente?
   - O tempo de processamento foi razoável?

3. COLABORAÇÃO NO PIPELINE:
   - As recomendações para próximos agentes são úteis?
   - O feedback fornece contexto suficiente?
   - Há informações importantes para o pipeline?

4. CONFORMIDADE COM INSTRUÇÕES:
   - O agente seguiu as instruções do Coordinator?
   - O resultado atende aos objetivos definidos?

Retorne APENAS um JSON válido:
{{
    "agent_evaluated": "{agent_name}",
    "overall_score": 0.85,
    "evaluation_categories": {{
        "decision_quality": {{
            "score": 0.9,
            "reasoning": "decisões bem fundamentadas com alta confiança"
        }},
        "technical_execution": {{
            "score": 0.8,
            "reasoning": "execução correta mas com alguns problemas menores"
        }},
        "pipeline_collaboration": {{
            "score": 0.9,
            "reasoning": "excelente feedback e recomendações"
        }},
        "instruction_compliance": {{
            "score": 0.8,
            "reasoning": "seguiu instruções mas pode melhorar"
        }}
    }},
    "key_strengths": [
        "detecção inteligente de gameplay puro",
        "preservação correta do áudio original"
    ],
    "areas_for_improvement": [
        "otimizar tempo de processamento",
        "melhorar detecção de alucinações"
    ],
    "impact_on_next_agents": {{
        "positive_impacts": [
            "chunks bem categorizados para seleção",
            "áudio limpo disponível quando necessário"
        ],
        "potential_issues": [
            "timing pode precisar ajuste após cortes"
        ]
    }},
    "coordinator_decision": "APPROVE",
    "requires_reprocessing": false,
    "confidence_in_evaluation": 0.9
}}

REGRAS:
- Use apenas aspas duplas no JSON
- Scores de 0.0 a 1.0
- coordinator_decision: APPROVE, REJECT, ou CONDITIONAL_APPROVE
- Seja específico e construtivo"""

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_api_key}"
            
            headers = {'Content-Type': 'application/json'}
            
            payload = {
                "contents": [{"parts": [{"text": evaluation_prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,
                    "topK": 1,
                    "topP": 1,
                    "maxOutputTokens": 1000
                }
            }
            
            print("🤖 Enviando avaliação para Gemini API...")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code != 200:
                raise Exception(f"Erro na API Gemini: {response.status_code} - {response.text}")
            
            result = response.json()
            ai_response = result['candidates'][0]['content']['parts'][0]['text']
            
            # Limpar e parsear JSON
            clean_response = ai_response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]
            
            clean_response = clean_response.replace("'", '"')
            evaluation = json.loads(clean_response)
            
            print(f"✅ Avaliação IA concluída!")
            print(f"   Score geral: {evaluation.get('overall_score', 0):.2f}")
            print(f"   Decisão: {evaluation.get('coordinator_decision', 'N/A')}")
            
            return evaluation
            
        except Exception as e:
            print(f"❌ Erro na avaliação IA: {e}")
            # Fallback para avaliação básica
            return {
                'agent_evaluated': agent_name,
                'overall_score': 0.7,
                'coordinator_decision': 'APPROVE',
                'requires_reprocessing': False,
                'evaluation_method': 'fallback_basic',
                'error': str(e)
            }
    
    def generate_coordinator_report(self, agent_evaluations: List[Dict[str, Any]]) -> str:
        """
        Gera relatório final do Coordinator sobre todo o pipeline.
        
        Args:
            agent_evaluations: Lista de avaliações de todos os agentes
            
        Returns:
            Caminho do arquivo de relatório gerado
        """
        print(f"\n📋 {self.name}: Gerando relatório final do pipeline...")
        
        report_file = self.coordinator_dir / f"coordinator_final_report_{int(time.time())}.json"
        
        # Analisar avaliações
        total_agents = len(agent_evaluations)
        approved_agents = len([e for e in agent_evaluations if e.get('coordinator_decision') == 'APPROVE'])
        average_score = sum(e.get('overall_score', 0) for e in agent_evaluations) / total_agents if total_agents > 0 else 0
        
        needs_reprocessing = [e for e in agent_evaluations if e.get('requires_reprocessing', False)]
        
        # Criar relatório consolidado
        final_report = {
            'coordinator': self.name,
            'report_timestamp': time.time(),
            'pipeline_summary': {
                'total_agents_evaluated': total_agents,
                'agents_approved': approved_agents,
                'average_pipeline_score': average_score,
                'pipeline_status': 'COMPLETED' if approved_agents == total_agents else 'NEEDS_ATTENTION',
                'requires_reprocessing': len(needs_reprocessing) > 0
            },
            'agent_evaluations': agent_evaluations,
            'pipeline_analysis': {
                'strengths': [],
                'weaknesses': [],
                'recommendations': []
            },
            'next_steps': []
        }
        
        # Consolidar insights de todos os agentes
        all_strengths = []
        all_improvements = []
        
        for evaluation in agent_evaluations:
            all_strengths.extend(evaluation.get('key_strengths', []))
            all_improvements.extend(evaluation.get('areas_for_improvement', []))
        
        final_report['pipeline_analysis']['strengths'] = list(set(all_strengths))
        final_report['pipeline_analysis']['weaknesses'] = list(set(all_improvements))
        
        # Definir próximos passos
        if needs_reprocessing:
            final_report['next_steps'].append("Reproccessar agentes que falharam")
        
        if average_score < 0.8:
            final_report['next_steps'].append("Revisar e otimizar pipeline")
        
        if approved_agents == total_agents:
            final_report['next_steps'].append("Pipeline pronto para produção")
        
        # Salvar relatório
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Relatório final gerado: {report_file}")
        print(f"   Status do pipeline: {final_report['pipeline_summary']['pipeline_status']}")
        print(f"   Score médio: {average_score:.2f}")
        print(f"   Agentes aprovados: {approved_agents}/{total_agents}")
        
        return str(report_file)
    
    def evaluate_complete_pipeline(self, agents_to_evaluate: List[str] = None) -> bool:
        """
        Avalia o pipeline completo recebendo feedback de todos os agentes.
        
        Args:
            agents_to_evaluate: Lista de agentes para avaliar (padrão: ['DAVID'])
            
        Returns:
            True se avaliação foi bem-sucedida
        """
        if agents_to_evaluate is None:
            agents_to_evaluate = ['DAVID']  # Expandir conforme implementamos outros agentes
        
        print(f"\n{'='*60}")
        print(f"🔍 {self.name}: AVALIANDO PIPELINE COMPLETO")
        print(f"{'='*60}")
        
        agent_evaluations = []
        
        for agent_name in agents_to_evaluate:
            print(f"\n--- Avaliando {agent_name} ---")
            
            # Receber feedback do agente
            feedback = self.receive_agent_feedback(agent_name)
            if not feedback:
                print(f"⚠️ Pulando {agent_name} - feedback não encontrado")
                continue
            
            # Avaliar trabalho do agente
            evaluation = self.evaluate_agent_work(feedback)
            evaluation['agent_name'] = agent_name
            agent_evaluations.append(evaluation)
        
        # Gerar relatório final
        if agent_evaluations:
            report_file = self.generate_coordinator_report(agent_evaluations)
            
            print(f"\n🎉 {self.name}: AVALIAÇÃO DE PIPELINE CONCLUÍDA!")
            print(f"📋 Relatório final: {report_file}")
            
            return True
        else:
            print(f"\n❌ {self.name}: Nenhum agente foi avaliado")
            return False

def main():
    """Função principal do Coordinator"""
    coordinator = Coordinator()
    
    print("\n🎬 COORDINATOR - OPÇÕES DISPONÍVEIS:")
    print("1. Criar plano inteligente de processamento (com seleção de agentes)")
    print("2. Avaliar pipeline após execução dos agentes")
    print("3. Ver status do workflow atual")
    
    choice = input("\nEscolha uma opção (1, 2 ou 3): ").strip()
    
    if choice == "1":
        # Criar plano de processamento
        user_instruction = input("\n💬 Digite sua instrução (ex: 'crie um video de até 30 segundos para o short do youtube com os tiros mais bonitos dessa partida'): ")
        
        if not user_instruction.strip():
            user_instruction = "crie um video de até 30 segundos para o short do youtube com os tiros mais bonitos dessa partida"
            print(f"📝 Usando instrução padrão: {user_instruction}")
        
        success = coordinator.coordinate_processing(user_instruction)
        
        if success:
            print(f"\n✅ Coordenação bem-sucedida!")
            print(f"📁 Verifique processing/coordinator/processing_plan.json")
            print(f"👥 Próximo passo: Executar agentes na sequência definida")
        else:
            print(f"\n❌ Falha na coordenação")
    
    elif choice == "2":
        # Avaliar pipeline
        success = coordinator.evaluate_complete_pipeline()
        
        if success:
            print(f"\n✅ Avaliação de pipeline concluída!")
            print(f"📁 Verifique processing/coordinator/ para relatórios")
        else:
            print(f"\n❌ Falha na avaliação do pipeline")
    
    elif choice == "3":
        # Ver status do workflow
        status = coordinator.get_workflow_status()
        
        if status['status'] == 'NO_WORKFLOW':
            print(f"\n📋 {status['message']}")
        elif status['status'] == 'ERROR':
            print(f"\n❌ Erro: {status['error']}")
        else:
            print(f"\n📊 STATUS DO WORKFLOW:")
            print(f"   ID: {status['workflow_id']}")
            print(f"   Progresso: {status['completed_steps']}/{status['total_steps']} ({status['progress_percentage']:.1f}%)")
            print(f"   Status: {status['current_status']}")
            print(f"   Otimização: {status['optimization_summary']}")
            
            print(f"\n📋 ETAPAS:")
            for agent, info in status['step_tracking'].items():
                status_icon = {"PENDING": "⏳", "IN_PROGRESS": "🔄", "COMPLETED": "✅", "FAILED": "❌"}.get(info['status'], "❓")
                print(f"   {status_icon} {agent}: {info['status']}")
    
    else:
        print("❌ Opção inválida! Use 1, 2 ou 3")

if __name__ == "__main__":
    main()