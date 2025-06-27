#!/usr/bin/env python3
"""
Agent David - Especialista em limpeza de áudio
Remove pausas, gagueiras, vícios de linguagem e melhora qualidade do áudio
"""

import os
import json
import subprocess
import time
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
from base_agent import BaseAgent, DecisionTypes, AgentStatus

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

class AgentDavid(BaseAgent):
    """
    Agent David - Especialista em Audio Cleaning
    
    MISSÃO: Limpar e otimizar áudio dos chunks para criar conteúdo dinâmico
    Remove pausas desnecessárias, gagueiras, vícios de linguagem ("hmm", "ahh", "tipo")
    """
    
    def __init__(self):
        super().__init__("DAVID", "AUDIO_CLEANING_SPECIALIST")
        
        # Configurações específicas do David
        self.temp_dir = self.agent_dir / 'temp_audio'
        self.temp_dir.mkdir(exist_ok=True)
        
        # Configurações de limpeza de áudio
        self.silence_threshold = -40  # dB para detectar silêncio
        self.min_silence_duration = 0.5  # segundos mínimos para considerar pausa
        self.filler_words = ['hmm', 'ahh', 'uhh', 'tipo', 'né', 'então', 'assim']
        
        print(f"🔧 Configurações de áudio:")
        print(f"   Threshold silêncio: {self.silence_threshold} dB")
        print(f"   Duração mín. pausa: {self.min_silence_duration}s")
        print(f"   Palavras-filtro: {len(self.filler_words)} configuradas")
    
    def execute(self) -> bool:
        """
        OBRIGATÓRIO: Método principal de execução do Agent David.
        Implementa o pipeline completo de limpeza de áudio com IA.
        """
        print(f"\n{'='*60}")
        print(f"🎵🤖 {self.name}: INICIANDO LIMPEZA DE ÁUDIO COM IA")
        print(f"{'='*60}")
        
        # Verificar API key
        if not os.getenv('GEMINI_API_KEY'):
            self.log_processing_step("API_CHECK", AgentStatus.ERROR, "GEMINI_API_KEY não encontrada")
            return False
        
        # Carregar plano do Coordinator
        processing_plan = self.load_processing_plan()
        if not processing_plan:
            return False
        
        self.log_processing_step("PLAN_LOADED", AgentStatus.SUCCESS, 
                               f"Tipo: {processing_plan['strategy']['target_content_type']}")
        
        # Processar chunks com IA
        results = self.process_chunks_with_ai(processing_plan)
        
        # Salvar resultados consolidados
        results_file = self.save_results(results)
        
        # Gerar feedback para o Coordinator
        self._generate_david_feedback(results, processing_plan)
        
        return results['status'] == 'COMPLETED'
    
    def load_processing_plan(self) -> Optional[Dict[str, Any]]:
        """Carrega plano de processamento criado pelo Coordinator"""
        print(f"\n📋 {self.name}: Carregando plano de processamento...")
        
        plan_file = self.coordinator_dir / 'processing_plan.json'
        
        if not plan_file.exists():
            print(f"❌ Plano não encontrado: {plan_file}")
            return None
        
        try:
            with open(plan_file, 'r', encoding='utf-8') as f:
                plan = json.load(f)
            
            # Verificar se é tarefa para David
            david_instructions = plan['strategy']['agent_instructions'].get('DAVID')
            if not david_instructions:
                print(f"❌ Nenhuma instrução para {self.name} no plano")
                return None
            
            print(f"✅ Plano carregado com instruções para {self.name}")
            return plan
            
        except Exception as e:
            print(f"❌ Erro ao carregar plano: {e}")
            return None
    
    def analyze_chunk_with_ai(self, chunk_path: str, instructions: Dict[str, Any]) -> Dict[str, Any]:
        """Usa IA para analisar chunk e criar estratégia de limpeza personalizada"""
        print(f"🧠 {self.name}: Analisando chunk com IA - {Path(chunk_path).name}")
        
        try:
            # Primeiro, extrair informações técnicas básicas
            technical_analysis = self._get_technical_analysis(chunk_path)
            
            # Usar IA para criar estratégia baseada nas instruções
            ai_strategy = self._create_cleaning_strategy_with_ai(chunk_path, technical_analysis, instructions)
            
            return {
                'chunk_path': chunk_path,
                'technical_analysis': technical_analysis,
                'ai_strategy': ai_strategy,
                'needs_cleaning': ai_strategy.get('requires_processing', True)
            }
            
        except Exception as e:
            print(f"   ❌ Erro na análise IA: {e}")
            return {'chunk_path': chunk_path, 'needs_cleaning': False, 'error': str(e)}
    
    def _get_technical_analysis(self, chunk_path: str) -> Dict[str, Any]:
        """Extrai informações técnicas E transcrição do chunk"""
        try:
            # Informações de áudio com ffprobe
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_streams', '-show_format', chunk_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            media_info = json.loads(result.stdout)
            
            # Detectar silêncios (mantém por compatibilidade)
            silence_cmd = [
                'ffmpeg', '-i', chunk_path, '-af', 
                f'silencedetect=noise={self.silence_threshold}dB:d={self.min_silence_duration}',
                '-f', 'null', '-'
            ]
            
            silence_result = subprocess.run(silence_cmd, capture_output=True, text=True)
            silence_periods = self._parse_silence_detection(silence_result.stderr)
            
            # Analisar volume médio
            volume_cmd = [
                'ffmpeg', '-i', chunk_path, '-af', 'volumedetect',
                '-f', 'null', '-'
            ]
            
            volume_result = subprocess.run(volume_cmd, capture_output=True, text=True)
            volume_info = self._parse_volume_analysis(volume_result.stderr)
            
            # NOVA: Extrair transcrição do áudio
            print(f"   🎤 Transcrevendo áudio para detectar vícios...")
            transcription = self._transcribe_audio_whisper_api(chunk_path)
            
            return {
                'duration': float(media_info.get('format', {}).get('duration', 0)),
                'silence_periods': silence_periods,
                'total_silence_duration': sum(p['duration'] for p in silence_periods),
                'silence_count': len(silence_periods),
                'volume_info': volume_info,
                'audio_streams': len([s for s in media_info.get('streams', []) if s.get('codec_type') == 'audio']),
                'transcription': transcription  # NOVO!
            }
            
        except Exception as e:
            print(f"   ⚠️ Erro análise técnica: {e}")
            return {'duration': 0, 'silence_periods': [], 'transcription': {'text': '', 'segments': []}, 'error': str(e)}
    
    def _transcribe_audio_whisper_api(self, chunk_path: str) -> Dict[str, Any]:
        """Transcreve áudio usando OpenAI Whisper API para detectar vícios"""
        try:
            # Extrair áudio do vídeo primeiro
            audio_path = self.temp_dir / f"{Path(chunk_path).stem}_audio.wav"
            
            cmd = [
                'ffmpeg', '-i', chunk_path,
                '-vn', '-acodec', 'pcm_s16le',
                '-ar', '16000', '-ac', '1',
                '-y', str(audio_path)
            ]
            
            subprocess.run(cmd, capture_output=True, check=True)
            
            if not audio_path.exists():
                return {'text': '', 'segments': []}
            
            # Usar Whisper API da OpenAI
            try:
                import openai
            except ImportError:
                print(f"   ⚠️ openai library não instalada: pip install openai")
                return {'text': '', 'segments': []}
            
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if not openai_api_key:
                print(f"   ⚠️ OPENAI_API_KEY não encontrada, pulando transcrição")
                return {'text': '', 'segments': []}
            
            # Configurar cliente OpenAI
            client = openai.OpenAI(api_key=openai_api_key)
            
            # Chamar API Whisper com configurações otimizadas
            with open(audio_path, 'rb') as audio_file:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"],
                    language="pt",  # Forçar português para reduzir alucinações
                    prompt="Gameplay de videogame. Pode conter falas do jogador ou sons do jogo. Se não há fala humana clara, retorne texto vazio.",  # Prompt genérico
                    temperature=0.0  # Temperatura zero para reduzir criatividade/alucinação
                )
            
            # Limpar arquivo temporário
            audio_path.unlink()
            
            print(f"   ✅ Transcrição: '{response.text[:50]}...'")
            
            # Converter segments para formato JSON serializável e analisar qualidade
            segments_data = []
            high_confidence_segments = 0
            total_speech_duration = 0.0
            
            if hasattr(response, 'segments') and response.segments:
                for segment in response.segments:
                    no_speech_prob = getattr(segment, 'no_speech_prob', 1.0)
                    avg_logprob = getattr(segment, 'avg_logprob', -10.0)
                    segment_text = getattr(segment, 'text', '').strip()
                    
                    segment_dict = {
                        'id': getattr(segment, 'id', 0),
                        'start': getattr(segment, 'start', 0.0),
                        'end': getattr(segment, 'end', 0.0),
                        'text': segment_text,
                        'tokens': getattr(segment, 'tokens', []),
                        'temperature': getattr(segment, 'temperature', 0.0),
                        'avg_logprob': avg_logprob,
                        'compression_ratio': getattr(segment, 'compression_ratio', 0.0),
                        'no_speech_prob': no_speech_prob
                    }
                    segments_data.append(segment_dict)
                    
                    # Analisar qualidade da transcrição
                    if no_speech_prob < 0.6 and avg_logprob > -3.0 and len(segment_text) > 3:
                        high_confidence_segments += 1
                        total_speech_duration += segment_dict['end'] - segment_dict['start']
            
            # Filtrar texto se qualidade for baixa (possível alucinação)
            filtered_text = response.text
            is_likely_hallucination = False
            
            # Critérios para detectar alucinação:
            # 1. Muitos segmentos com alta probabilidade de não-fala
            # 2. Texto muito longo vs duração real de fala
            # 3. Palavras estranhas ou texto multilíngue suspeito
            if len(segments_data) > 0:
                avg_no_speech_prob = sum(s['no_speech_prob'] for s in segments_data) / len(segments_data)
                
                suspicious_patterns = [
                    'thanks for watching', 'subscribe', 'like and subscribe',
                    'youtube', 'channel', 'click here', 'description below',
                    'video tutorial', 'follow me on', 'plug-in', 'software',
                    'alpha', 'beta', 'version', 'update available'
                ]
                
                has_suspicious_content = any(pattern.lower() in filtered_text.lower() for pattern in suspicious_patterns)
                
                if (avg_no_speech_prob > 0.7 or 
                    high_confidence_segments == 0 or 
                    has_suspicious_content or
                    len(filtered_text) > total_speech_duration * 20):  # Mais de 20 chars por segundo é suspeito
                    
                    is_likely_hallucination = True
                    filtered_text = ""  # Limpar texto suspeito
                    print(f"   ⚠️ Possível alucinação detectada - limpando transcrição")
                    print(f"   📊 Avg no_speech_prob: {avg_no_speech_prob:.2f}, Segmentos confiáveis: {high_confidence_segments}")
            
            return {
                'text': filtered_text,
                'segments': segments_data,
                'language': getattr(response, 'language', 'pt'),
                'quality_analysis': {
                    'high_confidence_segments': high_confidence_segments,
                    'total_segments': len(segments_data),
                    'total_speech_duration': total_speech_duration,
                    'is_likely_hallucination': is_likely_hallucination,
                    'avg_no_speech_prob': avg_no_speech_prob if segments_data else 1.0
                }
            }
            
        except Exception as e:
            print(f"   ⚠️ Erro na transcrição: {e}")
            return {'text': '', 'segments': []}
    
    def _parse_volume_analysis(self, ffmpeg_output: str) -> Dict[str, float]:
        """Parseia análise de volume do FFmpeg"""
        volume_info = {}
        for line in ffmpeg_output.split('\n'):
            if 'mean_volume:' in line:
                try:
                    volume_info['mean_volume'] = float(line.split('mean_volume: ')[1].split(' dB')[0])
                except:
                    pass
            elif 'max_volume:' in line:
                try:
                    volume_info['max_volume'] = float(line.split('max_volume: ')[1].split(' dB')[0])
                except:
                    pass
        return volume_info
    
    def _create_cleaning_strategy_with_ai(self, chunk_path: str, technical_analysis: Dict[str, Any], instructions: Dict[str, Any]) -> Dict[str, Any]:
        """Usa IA para criar estratégia de limpeza baseada nas instruções específicas"""
        
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not gemini_api_key:
            raise Exception("❌ GEMINI_API_KEY obrigatória!")
        
        # Extrair dados de transcrição
        transcription = technical_analysis.get('transcription', {})
        transcript_text = transcription.get('text', '')
        quality_analysis = transcription.get('quality_analysis', {})
        
        ai_prompt = f"""Você é DAVID, especialista em limpeza de áudio/vídeo para gaming/esports.

INSTRUÇÃO ESPECÍFICA DO COORDINATOR:
{json.dumps(instructions, indent=2, ensure_ascii=False)}

ANÁLISE TÉCNICA DO CHUNK "{Path(chunk_path).name}":
- Duração: {technical_analysis.get('duration', 0):.1f} segundos
- Períodos de silêncio: {technical_analysis.get('silence_count', 0)}
- Duração total silêncio: {technical_analysis.get('total_silence_duration', 0):.1f}s
- Volume médio: {technical_analysis.get('volume_info', {}).get('mean_volume', 'N/A')} dB
- Volume máximo: {technical_analysis.get('volume_info', {}).get('max_volume', 'N/A')} dB

ANÁLISE DE TRANSCRIÇÃO:
- Texto transcrito: "{transcript_text}"
- Segmentos de alta confiança: {quality_analysis.get('high_confidence_segments', 0)}/{quality_analysis.get('total_segments', 0)}
- Duração real de fala: {quality_analysis.get('total_speech_duration', 0):.1f}s
- Probabilidade média de não-fala: {quality_analysis.get('avg_no_speech_prob', 1.0):.2f}
- Possível alucinação detectada: {quality_analysis.get('is_likely_hallucination', False)}

ANÁLISE INTELIGENTE DO CONTEÚDO:
Use as métricas de qualidade da transcrição para determinar o TIPO DE ÁUDIO:

CRITÉRIOS PARA GAMEPLAY SÓ COM JOGO:
- Transcrição vazia OU possível alucinação detectada = TRUE
- Segmentos de alta confiança = 0 ou muito poucos
- Probabilidade média de não-fala > 0.6
- Texto suspeito (frases estranhas, multilíngue, técnicas)
- Duração real de fala < 10% da duração total do chunk
- Sons típicos: Windows, cliques, música do jogo, vozes de NPCs

CRITÉRIOS PARA GAMEPLAY COM NARRAÇÃO:
- Segmentos de alta confiança > 30% dos segmentos totais
- Probabilidade média de não-fala < 0.5
- Duração real de fala > 20% da duração total
- Texto contém comentários pessoais: "nossa", "cara", "mano"
- Reações ao gameplay: "que tiro", "olha isso"

CRITÉRIOS PARA CONVERSA/CHAT:
- Duração real de fala > 50% da duração total
- Múltiplas vozes detectadas
- Conversas contínuas entre pessoas

REGRAS DE DECISÃO BASEADAS NAS MÉTRICAS:

1. SE possível_alucinação = TRUE → TIPO = "gameplay_only"
2. SE segmentos_alta_confiança = 0 → TIPO = "gameplay_only"  
3. SE prob_média_não_fala > 0.7 → TIPO = "gameplay_only"
4. SE duração_real_fala < 5 segundos → TIPO = "gameplay_only"
5. SE texto_vazio OU texto_suspeito → TIPO = "gameplay_only"

IMPORTANTE: Seja CONSERVADOR. Na dúvida, classifique como "gameplay_only" para preservar a experiência.

Com base nesta análise BASEADA EM DADOS, crie uma estratégia PRECISA.

Retorne APENAS um JSON válido sem comentários ou texto extra. Use strings curtas e simples:
{{
    "requires_processing": false,
    "audio_type": "gameplay_only",
    "strategy_explanation": "Gameplay puro detectado. Preservar audio original.",
    "detected_issues": {{
        "silence_periods": {technical_analysis.get('silence_count', 0)},
        "filler_words": [],
        "stutters": [],
        "hesitations": [],
        "game_audio_detected": true
    }},
    "processing_strategy": {{
        "preserve_game_audio": true,
        "cut_silence": false,
        "remove_filler_words": false,
        "fix_stutters": false,
        "audio_enhancement": true
    }},
    "audio_filters": [
        "highpass=f=80",
        "lowpass=f=15000"
    ],
    "silence_removal": {{
        "enabled": false,
        "threshold_db": -40,
        "min_duration": 0.5,
        "aggressiveness": "low"
    }},
    "volume_adjustment": {{
        "enabled": true,
        "normalize": true,
        "target_loudness": -23
    }},
    "preserve_action_audio": true,
    "intensity_level": "medium",
    "expected_improvement": "Melhoria na qualidade do audio do jogo"
}}

REGRAS OBRIGATÓRIAS:
0. Use APENAS caracteres ASCII simples no JSON. Evite acentos, aspas curvas, reticências especiais
1. Siga exatamente a instrução: "{instructions.get('focus', '')}"
2. Preserve_action_audio: {instructions.get('preserve_action_audio', True)}
3. Intensity_level: {instructions.get('intensity_level', 'medium')}

DETECÇÃO DE TIPO DE ÁUDIO:
4. Se transcrição for vazia ou só conter falas do jogo → audio_type: "gameplay_only"
5. Se detectar jogador falando sobre gameplay → audio_type: "gameplay_with_narration"  
6. Se detectar múltiplas pessoas conversando → audio_type: "conversation"

REGRAS POR TIPO:
7. GAMEPLAY_ONLY: requires_processing = false (preserve tudo)
8. GAMEPLAY_WITH_NARRATION: processar apenas vícios do jogador
9. CONVERSATION: cuidado com cortes que quebrem diálogo

PRIORIDADES:
10. NUNCA corte falas importantes do jogo (callouts, comunicação de equipe)
11. PRESERVE sons de ambiente, música, efeitos sonoros
12. ANALISE CONTEXTO: "Fire in the hole" é do jogo, "nossa que tiro" é do jogador
13. Se em dúvida sobre quem está falando → NÃO CORTE

Seja CONSERVADOR - melhor preservar demais que cortar demais."""

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_api_key}"
            
            headers = {'Content-Type': 'application/json'}
            
            payload = {
                "contents": [{"parts": [{"text": ai_prompt}]}],
                "generationConfig": {
                    "temperature": 0.3,
                    "topK": 1,
                    "topP": 1,
                    "maxOutputTokens": 800
                }
            }
            
            print(f"🤖 Enviando análise para IA...")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code != 200:
                raise Exception(f"Erro API: {response.status_code}")
            
            result = response.json()
            ai_response = result['candidates'][0]['content']['parts'][0]['text']
            
            # Parsear JSON com tratamento robusto
            clean_response = ai_response.strip()
            
            # Remover markdown code blocks
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]
            elif clean_response.startswith('```'):
                clean_response = clean_response[3:]
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]
            
            # Limpar texto antes e depois do JSON
            clean_response = clean_response.strip()
            
            # Encontrar o JSON no texto
            start_idx = clean_response.find('{')
            end_idx = clean_response.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                clean_response = clean_response[start_idx:end_idx + 1]
            
            # Corrigir aspas simples para duplas (mas não dentro de strings)
            # Usar regex mais cuidadoso ou método manual
            clean_response = clean_response.replace("'", '"')
            
            # Corrigir caracteres problemáticos que podem aparecer
            clean_response = clean_response.replace('…', '...')
            clean_response = clean_response.replace('"', '"').replace('"', '"')
            clean_response = clean_response.replace(''', "'").replace(''', "'")
            
            # Debug: mostrar o JSON que estamos tentando parsear
            print(f"   🔧 JSON para parsear: {clean_response[:200]}...")
            
            try:
                strategy = json.loads(clean_response)
            except json.JSONDecodeError as parse_error:
                print(f"   ❌ JSON inválido: {parse_error}")
                print(f"   📝 Linha problemática: {clean_response.split(chr(10))[parse_error.lineno-1] if hasattr(parse_error, 'lineno') else 'N/A'}")
                print(f"   📄 Resposta completa limpa:\n{clean_response}")
                
                # Tentar fallback: remover caracteres não-ASCII
                try:
                    clean_ascii = clean_response.encode('ascii', 'ignore').decode('ascii')
                    strategy = json.loads(clean_ascii)
                    print(f"   ✅ Fallback ASCII funcionou!")
                except:
                    raise Exception(f"IA retornou JSON inválido mesmo com fallback: {parse_error}")
            
            print(f"✅ Estratégia IA criada: {strategy.get('strategy_explanation', '')[:50]}...")
            
            # Salvar análise da IA em arquivo JSON
            self._save_ai_analysis(chunk_path, technical_analysis, instructions, strategy)
            
            return strategy
            
        except Exception as e:
            print(f"❌ Erro na estratégia IA: {e}")
            # Fallback para estratégia básica
            return {
                'requires_processing': True,
                'strategy_explanation': 'Estratégia básica por falha da IA',
                'audio_filters': ['highpass=f=80', 'lowpass=f=15000', 'dynaudnorm'],
                'silence_removal': {'enabled': True, 'threshold_db': -40, 'min_duration': 0.5},
                'volume_adjustment': {'enabled': True, 'normalize': True},
                'preserve_action_audio': instructions.get('preserve_action_audio', True),
                'intensity_level': instructions.get('intensity_level', 'medium')
            }
    
    def _save_ai_analysis(self, chunk_path: str, technical_analysis: Dict[str, Any], instructions: Dict[str, Any], ai_strategy: Dict[str, Any]) -> str:
        """Salva análise completa da IA em arquivo JSON"""
        try:
            chunk_name = Path(chunk_path).stem
            analysis_file = self.david_dir / f"david_analysis_{chunk_name}.json"
            
            complete_analysis = {
                'agent': self.name,
                'chunk_file': Path(chunk_path).name,
                'analysis_timestamp': time.time(),
                'coordinator_instructions': instructions,
                'technical_analysis': {
                    'duration': technical_analysis.get('duration', 0),
                    'silence_periods_count': technical_analysis.get('silence_count', 0),
                    'total_silence_duration': technical_analysis.get('total_silence_duration', 0),
                    'volume_info': technical_analysis.get('volume_info', {}),
                    'transcription': technical_analysis.get('transcription', {})
                },
                'ai_strategy': ai_strategy,
                'processing_decision': {
                    'requires_processing': ai_strategy.get('requires_processing', False),
                    'audio_type_detected': ai_strategy.get('audio_type', 'unknown'),
                    'reasoning': ai_strategy.get('strategy_explanation', ''),
                    'detected_issues': ai_strategy.get('detected_issues', {}),
                    'processing_strategy': ai_strategy.get('processing_strategy', {})
                }
            }
            
            with open(analysis_file, 'w', encoding='utf-8') as f:
                json.dump(complete_analysis, f, indent=2, ensure_ascii=False)
            
            print(f"   💾 Análise IA salva: {analysis_file.name}")
            return str(analysis_file)
            
        except Exception as e:
            print(f"   ⚠️ Erro ao salvar análise: {e}")
            return ""
    
    def _save_chunk_processing_result(self, chunk_filename: str, chunk_result: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Salva resultado detalhado do processamento de cada chunk"""
        try:
            chunk_name = Path(chunk_filename).stem
            result_file = self.david_dir / f"david_processing_{chunk_name}.json"
            
            processing_result = {
                'agent': self.name,
                'chunk_file': chunk_filename,
                'processing_timestamp': time.time(),
                'processing_result': chunk_result,
                'detailed_analysis': {
                    'technical_analysis': analysis.get('technical_analysis', {}),
                    'ai_strategy': analysis.get('ai_strategy', {}),
                    'processing_decision': {
                        'needs_cleaning': analysis.get('needs_cleaning', False),
                        'audio_type_detected': analysis.get('ai_strategy', {}).get('audio_type', 'unknown'),
                        'strategy_explanation': analysis.get('ai_strategy', {}).get('strategy_explanation', ''),
                        'detected_issues': analysis.get('ai_strategy', {}).get('detected_issues', {}),
                        'processing_strategy': analysis.get('ai_strategy', {}).get('processing_strategy', {}),
                        'expected_improvement': analysis.get('ai_strategy', {}).get('expected_improvement', '')
                    }
                },
                'performance_metrics': {
                    'time_saved': chunk_result.get('time_saved', 0),
                    'processing_successful': chunk_result.get('status') == 'AI_PROCESSED',
                    'audio_filters_applied': len(analysis.get('ai_strategy', {}).get('audio_filters', [])),
                    'issues_detected': len(analysis.get('ai_strategy', {}).get('detected_issues', {}).get('filler_words', [])) + len(analysis.get('ai_strategy', {}).get('detected_issues', {}).get('stutters', []))
                },
                'transcription_data': analysis.get('technical_analysis', {}).get('transcription', {}),
                'coordinator_context': analysis.get('coordinator_instructions', {})
            }
            
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(processing_result, f, indent=2, ensure_ascii=False)
            
            print(f"   📊 Resultado do processamento salvo: {result_file.name}")
            return str(result_file)
            
        except Exception as e:
            print(f"   ⚠️ Erro ao salvar resultado do processamento: {e}")
            return ""
    
    def _parse_silence_detection(self, ffmpeg_output: str) -> List[Dict[str, float]]:
        """Parseia output do silencedetect do FFmpeg"""
        silence_periods = []
        lines = ffmpeg_output.split('\n')
        
        current_silence = {}
        
        for line in lines:
            if 'silence_start:' in line:
                try:
                    start_time = float(line.split('silence_start: ')[1].split()[0])
                    current_silence = {'start': start_time}
                except (IndexError, ValueError):
                    continue
                    
            elif 'silence_end:' in line and current_silence:
                try:
                    end_time = float(line.split('silence_end: ')[1].split()[0])
                    duration = float(line.split('silence_duration: ')[1].split()[0])
                    
                    current_silence.update({
                        'end': end_time,
                        'duration': duration
                    })
                    
                    silence_periods.append(current_silence)
                    current_silence = {}
                    
                except (IndexError, ValueError):
                    continue
        
        return silence_periods
    
    def create_ai_audio_filter(self, ai_strategy: Dict[str, Any]) -> str:
        """Cria filtro FFmpeg baseado na estratégia da IA"""
        filters = []
        
        # Usar filtros específicos da IA
        ai_filters = ai_strategy.get('audio_filters', [])
        filters.extend(ai_filters)
        
        # Configurar remoção de silêncio baseada na IA
        silence_config = ai_strategy.get('silence_removal', {})
        if silence_config.get('enabled', False):
            threshold_db = silence_config.get('threshold_db', -40)
            min_duration = silence_config.get('min_duration', 0.5)
            aggressiveness = silence_config.get('aggressiveness', 'medium')
            
            # Ajustar parâmetros baseado na agressividade
            if aggressiveness == 'high':
                threshold_db = max(threshold_db, -35)  # Mais sensível
                min_duration = max(min_duration * 0.7, 0.3)  # Cortes menores
            elif aggressiveness == 'low':
                threshold_db = min(threshold_db, -45)  # Menos sensível  
                min_duration = min_duration * 1.3  # Cortes maiores
            
            # IMPORTANTE: silenceremove remove áudio E vídeo juntos
            # Remove início silencioso e múltiplos segmentos de silêncio
            silence_filter = f'silenceremove=start_periods=1:start_silence={min_duration}:start_threshold={threshold_db}dB:stop_periods=-1:stop_silence={min_duration}:stop_threshold={threshold_db}dB'
            filters.append(silence_filter)
        
        # Configurar ajuste de volume baseado na IA
        volume_config = ai_strategy.get('volume_adjustment', {})
        if volume_config.get('enabled', False):
            if volume_config.get('normalize', False):
                target_loudness = volume_config.get('target_loudness', -23)
                filters.append(f'loudnorm=I={target_loudness}:LRA=11:TP=-1.5')
            else:
                filters.append('dynaudnorm=p=0.9:s=1')
        
        # Se não há filtros, usar básico
        if not filters:
            filters = ['highpass=f=80', 'lowpass=f=15000', 'dynaudnorm']
        
        print(f"🎛️ Filtros IA aplicados: {len(filters)} filtros")
        return ','.join(filters)
    
    def clean_audio_chunk_with_ai(self, chunk_path: str, analysis: Dict[str, Any]) -> Optional[str]:
        """Limpa áudio E corta vídeo usando estratégia criada pela IA"""
        print(f"🧹 {self.name}: Processando chunk com estratégia IA - {Path(chunk_path).name}")
        
        ai_strategy = analysis.get('ai_strategy', {})
        technical_analysis = analysis.get('technical_analysis', {})
        
        if not analysis.get('needs_cleaning') or not ai_strategy.get('requires_processing', True):
            audio_type = ai_strategy.get('audio_type', 'unknown')
            print(f"   ✅ IA determinou: chunk não precisa de processamento")
            print(f"   🎮 Tipo de áudio: {audio_type}")
            print(f"   💡 Motivo: {ai_strategy.get('strategy_explanation', 'N/A')}")
            
            # Se for gameplay_only, garantir que não processamos
            if audio_type == 'gameplay_only':
                print(f"   🎯 Gameplay puro detectado - preservando experiência completa do jogo")
            
            return chunk_path
        
        # Criar nome do arquivo limpo
        chunk_file = Path(chunk_path)
        cleaned_filename = f"{chunk_file.stem}_cleaned_ai{chunk_file.suffix}"
        cleaned_path = self.temp_dir / cleaned_filename
        
        try:
            audio_type = ai_strategy.get('audio_type', 'unknown')
            processing_strategy = ai_strategy.get('processing_strategy', {})
            
            print(f"   🎯 Estratégia: {ai_strategy.get('strategy_explanation', '')[:80]}...")
            print(f"   🎮 Tipo de áudio: {audio_type}")
            print(f"   🎛️ Intensidade: {ai_strategy.get('intensity_level', 'medium')}")
            print(f"   🎵 Preservar áudio do jogo: {processing_strategy.get('preserve_game_audio', True)}")
            
            # Verificar se precisa cortar partes silenciosas
            silence_periods = technical_analysis.get('silence_periods', [])
            
            # Lógica baseada no tipo de áudio
            if audio_type == 'gameplay_only':
                print(f"   🎮 Gameplay puro - aplicando apenas melhorias básicas de áudio")
                return self._apply_audio_filters_only(chunk_path, ai_strategy, cleaned_path)
            
            elif processing_strategy.get('cut_silence') and len(silence_periods) > 0:
                print(f"   ✂️ Cortando {len(silence_periods)} períodos de silêncio do vídeo...")
                return self._cut_silence_from_video(chunk_path, silence_periods, ai_strategy, cleaned_path)
            
            else:
                print(f"   🎚️ Aplicando filtros de áudio sem cortes...")
                return self._apply_audio_filters_only(chunk_path, ai_strategy, cleaned_path)
                
        except Exception as e:
            print(f"   ❌ Erro no processamento: {e}")
            return None
    
    def _cut_silence_from_video(self, chunk_path: str, silence_periods: List[Dict], ai_strategy: Dict, output_path: Path) -> Optional[str]:
        """Corta partes silenciosas do vídeo (áudio + vídeo)"""
        try:
            # Criar segmentos sem silêncio
            segments_file = self.temp_dir / f"segments_{Path(chunk_path).stem}.txt"
            
            # Gerar lista de segmentos a manter
            duration = self._get_video_duration(chunk_path)
            segments = self._generate_segments_without_silence(duration, silence_periods, ai_strategy)
            
            if len(segments) == 0:
                print(f"   ⚠️ Nenhum segmento válido encontrado")
                return chunk_path
            
            # Criar segmentos individuais primeiro
            segment_files = []
            print(f"   📐 Criando {len(segments)} segmentos...")
            
            for i, (start, end) in enumerate(segments):
                segment_file = self.temp_dir / f"segment_{i}_{Path(chunk_path).stem}.mp4"
                print(f"   🔧 Segmento {i+1}/{len(segments)}: {start:.1f}s → {end:.1f}s")
                
                # Extrair cada segmento
                cmd = [
                    'ffmpeg', '-i', chunk_path,
                    '-ss', str(start),
                    '-t', str(end - start),
                    '-c:v', 'libx264', '-c:a', 'aac',
                    '-b:a', '128k', '-crf', '23',
                    '-avoid_negative_ts', 'make_zero',
                    '-y', str(segment_file)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0 and segment_file.exists():
                    segment_files.append(str(segment_file))
                    print(f"     ✅ Segmento criado: {segment_file.name}")
                else:
                    print(f"     ❌ Erro ao criar segmento: {result.stderr}")
            
            if not segment_files:
                print(f"   ❌ Nenhum segmento criado")
                return None
            
            # Criar arquivo de lista para concatenação (usar caminhos absolutos)
            with open(segments_file, 'w') as f:
                for segment_file in segment_files:
                    abs_path = Path(segment_file).resolve()
                    f.write(f"file '{abs_path}'\n")
            
            # Debug: mostrar conteúdo do arquivo
            print(f"   📄 Arquivo de lista criado: {segments_file}")
            with open(segments_file, 'r') as f:
                content = f.read()
                print(f"   📝 Conteúdo:\n{content}")
            
            # Verificar se todos os arquivos existem
            for segment_file in segment_files:
                if not Path(segment_file).exists():
                    print(f"   ⚠️ Arquivo não existe: {segment_file}")
                else:
                    print(f"   ✅ Arquivo existe: {Path(segment_file).name}")
            
            # Usar FFmpeg para concatenar segmentos
            cmd = [
                'ffmpeg', '-f', 'concat', '-safe', '0',
                '-i', str(segments_file),
                '-c', 'copy',  # Copy streams para evitar re-encoding
                '-y', str(output_path)
            ]
            
            print(f"   🔧 Concatenando {len(segment_files)} segmentos...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"   ❌ Erro na concatenação: {result.stderr}")
                # Tentar método alternativo com re-encoding
                cmd_alt = [
                    'ffmpeg', '-f', 'concat', '-safe', '0',
                    '-i', str(segments_file),
                    '-c:v', 'libx264', '-c:a', 'aac',
                    '-b:a', '128k', '-crf', '23',
                    '-y', str(output_path)
                ]
                print(f"   🔄 Tentando concatenação com re-encoding...")
                result = subprocess.run(cmd_alt, capture_output=True, text=True)
            
            # Limpar arquivos temporários
            segments_file.unlink()
            for segment_file in segment_files:
                Path(segment_file).unlink(missing_ok=True)
            
            if output_path.exists() and result.returncode == 0:
                original_duration = self._get_video_duration(chunk_path)
                new_duration = self._get_video_duration(str(output_path))
                time_saved = original_duration - new_duration
                
                print(f"   ✅ Corte concluído!")
                print(f"   📊 Tempo removido: {time_saved:.1f}s ({time_saved/original_duration*100:.1f}%)")
                print(f"   🎬 Nova duração: {new_duration:.1f}s")
                
                return str(output_path)
            else:
                print(f"   ❌ Falha na concatenação: {result.stderr}")
                return None
                
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Erro FFmpeg no corte: {e}")
            return None
    
    def _apply_audio_filters_only(self, chunk_path: str, ai_strategy: Dict, output_path: Path) -> Optional[str]:
        """Aplica apenas filtros de áudio sem cortar vídeo"""
        try:
            audio_filter = self.create_ai_audio_filter(ai_strategy)
            
            cmd = [
                'ffmpeg', '-i', chunk_path,
                '-af', audio_filter,
                '-c:v', 'copy',  # Manter vídeo original
                '-c:a', 'aac',   # Re-encode áudio
                '-b:a', '128k',  # Bitrate áudio
                '-y', str(output_path)
            ]
            
            print(f"   🔧 Aplicando {len(audio_filter.split(','))} filtros de áudio...")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if output_path.exists():
                print(f"   ✅ Filtros aplicados com sucesso!")
                return str(output_path)
            else:
                return None
                
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Erro FFmpeg nos filtros: {e}")
            return None
    
    def _generate_segments_without_silence(self, duration: float, silence_periods: List[Dict], ai_strategy: Dict) -> List[tuple]:
        """Gera lista de segmentos de vídeo removendo silêncios"""
        segments = []
        current_time = 0.0
        
        # Configurações baseadas na estratégia IA
        silence_config = ai_strategy.get('silence_removal', {})
        min_segment_duration = 1.0  # Mínimo 1 segundo por segmento
        
        for silence in silence_periods:
            silence_start = silence['start']
            silence_end = silence['end']
            
            # Adicionar segmento antes do silêncio
            if silence_start > current_time:
                segment_duration = silence_start - current_time
                if segment_duration >= min_segment_duration:
                    segments.append((current_time, silence_start))
            
            # Pular o silêncio
            current_time = silence_end
        
        # Adicionar segmento final após último silêncio
        if current_time < duration:
            segment_duration = duration - current_time
            if segment_duration >= min_segment_duration:
                segments.append((current_time, duration))
        
        print(f"   📐 Segmentos gerados: {len(segments)} de {duration:.1f}s total")
        return segments
    
    def _get_video_duration(self, video_path: str) -> float:
        """Obtém duração do vídeo em segundos"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            info = json.loads(result.stdout)
            
            return float(info['format']['duration'])
            
        except Exception:
            return 0.0
    
    def process_chunks_with_ai(self, processing_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Processa chunks usando IA para estratégias personalizadas"""
        print(f"\n🤖 {self.name}: Iniciando processamento com IA...")
        
        david_instructions = processing_plan['strategy']['agent_instructions']['DAVID']
        chunks_to_process = david_instructions['chunks_to_process']
        
        results = {
            'agent': self.name,
            'processed_chunks': [],
            'ai_strategies_used': [],
            'total_time_saved': 0.0,
            'processing_time': time.time(),
            'status': 'IN_PROGRESS',
            'coordinator_instructions': david_instructions
        }
        
        print(f"📋 Instruções do Coordinator:")
        print(f"   🎯 Foco: {david_instructions.get('focus', 'N/A')}")
        print(f"   🎵 Preservar áudio de ação: {david_instructions.get('preserve_action_audio', True)}")
        print(f"   🎛️ Intensidade: {david_instructions.get('intensity_level', 'medium')}")
        print(f"📊 Chunks para processar: {len(chunks_to_process)}")
        
        for i, chunk_filename in enumerate(chunks_to_process, 1):
            chunk_path = self.chunks_dir / chunk_filename
            
            if not chunk_path.exists():
                print(f"⚠️ Chunk {i}/{len(chunks_to_process)}: {chunk_filename} não encontrado")
                continue
            
            print(f"\n{'='*60}")
            print(f"🎬 Processando chunk {i}/{len(chunks_to_process)}: {chunk_filename}")
            print(f"{'='*60}")
            
            try:
                # Analisar chunk com IA
                analysis = self.analyze_chunk_with_ai(str(chunk_path), david_instructions)
                
                # Limpar áudio com estratégia IA
                cleaned_path = self.clean_audio_chunk_with_ai(str(chunk_path), analysis)
                
                if cleaned_path:
                    ai_strategy = analysis.get('ai_strategy', {})
                    technical_analysis = analysis.get('technical_analysis', {})
                    
                    # Calcular tempo salvo corretamente baseado no processamento
                    requires_processing = ai_strategy.get('requires_processing', True)
                    actual_time_saved = 0.0
                    
                    if requires_processing and cleaned_path != str(chunk_path):
                        # Só conta tempo salvo se realmente processou e gerou arquivo diferente
                        actual_time_saved = technical_analysis.get('total_silence_duration', 0)
                    
                    chunk_result = {
                        'original_chunk': chunk_filename,
                        'cleaned_chunk': Path(cleaned_path).name,
                        'time_saved': actual_time_saved,
                        'ai_strategy_used': ai_strategy.get('strategy_explanation', ''),
                        'audio_type_detected': ai_strategy.get('audio_type', 'unknown'),
                        'requires_processing': requires_processing,
                        'expected_improvement': ai_strategy.get('expected_improvement', ''),
                        'processing_strategy': ai_strategy.get('processing_strategy', {}),
                        'detected_issues': ai_strategy.get('detected_issues', {}),
                        'status': 'AI_PROCESSED' if requires_processing else 'PRESERVED'
                    }
                    
                    results['processed_chunks'].append(chunk_result)
                    results['total_time_saved'] += chunk_result['time_saved']
                    
                    # Armazenar estratégia única para relatório
                    strategy_summary = {
                        'chunk': chunk_filename,
                        'audio_type': ai_strategy.get('audio_type', 'unknown'),
                        'strategy': ai_strategy.get('strategy_explanation', ''),
                        'filters_used': len(ai_strategy.get('audio_filters', [])),
                        'intensity': ai_strategy.get('intensity_level', 'medium'),
                        'issues_found': len(ai_strategy.get('detected_issues', {}).get('filler_words', [])) + len(ai_strategy.get('detected_issues', {}).get('stutters', []))
                    }
                    results['ai_strategies_used'].append(strategy_summary)
                    
                    # Salvar resultado individual do chunk
                    self._save_chunk_processing_result(chunk_filename, chunk_result, analysis)
                    
                else:
                    chunk_result = {
                        'original_chunk': chunk_filename,
                        'status': 'FAILED',
                        'error': 'Processamento IA falhou'
                    }
                    results['processed_chunks'].append(chunk_result)
                    
            except Exception as e:
                print(f"❌ Erro no processamento do chunk {chunk_filename}: {e}")
                chunk_result = {
                    'original_chunk': chunk_filename,
                    'status': 'ERROR',
                    'error': str(e)
                }
                results['processed_chunks'].append(chunk_result)
        
        results['processing_time'] = time.time() - results['processing_time']
        results['status'] = 'COMPLETED'
        
        # Relatório final
        successful_chunks = [c for c in results['processed_chunks'] if c['status'] in ['AI_PROCESSED', 'PRESERVED']]
        preserved_chunks = [c for c in results['processed_chunks'] if c['status'] == 'PRESERVED']
        processed_chunks = [c for c in results['processed_chunks'] if c['status'] == 'AI_PROCESSED']
        
        print(f"\n🎉 {self.name}: PROCESSAMENTO IA CONCLUÍDO!")
        print(f"📊 Chunks analisados com sucesso: {len(successful_chunks)}/{len(chunks_to_process)}")
        print(f"🎬 Chunks processados (limpeza): {len(processed_chunks)}")
        print(f"🎮 Chunks preservados (gameplay puro): {len(preserved_chunks)}")
        print(f"⏱️  Tempo total economizado: {results['total_time_saved']:.1f}s")
        print(f"🕐 Tempo de processamento: {results['processing_time']:.1f}s")
        print(f"🤖 Estratégias IA únicas: {len(set(s['strategy'] for s in results['ai_strategies_used']))}")
        
        return results
    
    def save_results(self, results: Dict[str, Any]) -> str:
        """Salva resultados do processamento"""
        results_file = self.david_dir / f'{self.name.lower()}_results.json'
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Resultados salvos: {results_file}")
        return str(results_file)
    
    def execute_ai_audio_cleaning(self) -> bool:
        """Método principal - executa limpeza de áudio usando IA"""
        print(f"\n{'='*60}")
        print(f"🎵🤖 {self.name}: INICIANDO LIMPEZA DE ÁUDIO COM IA")
        print(f"{'='*60}")
        
        # Verificar API key
        if not os.getenv('GEMINI_API_KEY'):
            print("❌ GEMINI_API_KEY não encontrada! Configure a API key.")
            return False
        
        # Carregar plano do Coordinator
        processing_plan = self.load_processing_plan()
        if not processing_plan:
            return False
        
        print(f"📋 Plano carregado do Coordinator")
        print(f"🎯 Tipo de conteúdo: {processing_plan['strategy']['target_content_type']}")
        print(f"⏱️ Duração alvo: {processing_plan['strategy']['target_duration']}s")
        
        # Processar chunks com IA
        results = self.process_chunks_with_ai(processing_plan)
        
        # Salvar resultados
        results_file = self.save_results(results)
        
        # Relatório final detalhado
        total_chunks = len(results['processed_chunks'])
        successful_chunks = [c for c in results['processed_chunks'] if c['status'] in ['AI_PROCESSED', 'PRESERVED']]
        preserved_chunks = [c for c in results['processed_chunks'] if c['status'] == 'PRESERVED']
        processed_chunks = [c for c in results['processed_chunks'] if c['status'] == 'AI_PROCESSED']
        
        print(f"\n🎉 {self.name}: LIMPEZA DE ÁUDIO IA CONCLUÍDA!")
        print(f"📋 Resultados detalhados: {results_file}")
        print(f"📊 Taxa de sucesso: {len(successful_chunks)}/{total_chunks} chunks analisados")
        print(f"🎬 Processados: {len(processed_chunks)} | 🎮 Preservados: {len(preserved_chunks)}")
        print(f"🤖 IA aplicou {len(results['ai_strategies_used'])} estratégias personalizadas")
        print(f"👥 Próximo agente: SAIMON (seleção de conteúdo)")
        
        return True
    
    def _generate_david_feedback(self, results: Dict[str, Any], processing_plan: Dict[str, Any]) -> str:
        """Gera feedback específico do David para o Coordinator"""
        
        decisions_made = []
        problems_found = []
        recommendations = []
        
        # Analisar resultados e criar decisões estruturadas
        for chunk_result in results.get('processed_chunks', []):
            decision = self.create_decision_record(
                decision_type=DecisionTypes.AUDIO_PROCESSING,
                decision=f"audio_type: {chunk_result.get('audio_type_detected', 'unknown')}",
                reasoning=chunk_result.get('ai_strategy_used', 'No strategy applied'),
                confidence=0.9 if chunk_result.get('status') == 'PRESERVED' else 0.8,
                data_used={
                    'chunk': chunk_result.get('original_chunk'),
                    'requires_processing': chunk_result.get('requires_processing', False),
                    'time_saved': chunk_result.get('time_saved', 0),
                    'processing_strategy': chunk_result.get('processing_strategy', {})
                }
            )
            decisions_made.append(decision)
        
        # Identificar problemas
        failed_chunks = [c for c in results.get('processed_chunks', []) if c.get('status') in ['FAILED', 'ERROR']]
        if failed_chunks:
            problems_found.extend([f"Falha no processamento: {c['original_chunk']}" for c in failed_chunks])
        
        # Recomendações para próximos agentes
        preserved_count = len([c for c in results.get('processed_chunks', []) if c.get('status') == 'PRESERVED'])
        processed_count = len([c for c in results.get('processed_chunks', []) if c.get('status') == 'AI_PROCESSED'])
        
        if preserved_count > 0:
            recommendations.append(f"Saimon: {preserved_count} chunks preservados contêm gameplay puro - foque em momentos visuais épicos")
        
        if processed_count > 0:
            recommendations.append(f"Saimon: {processed_count} chunks processados têm áudio limpo - podem conter narração importante")
        
        if results.get('total_time_saved', 0) > 0:
            recommendations.append(f"Cloe: {results['total_time_saved']:.1f}s economizados - ajustar timing para manter sincronismo")
        
        # Métricas de performance
        metrics = {
            'chunks_analyzed': len(results.get('processed_chunks', [])),
            'chunks_preserved': preserved_count,
            'chunks_processed': processed_count,
            'total_time_saved': results.get('total_time_saved', 0),
            'processing_time': results.get('processing_time', 0),
            'ai_strategies_used': len(results.get('ai_strategies_used', [])),
            'average_confidence': sum(d['confidence'] for d in decisions_made) / len(decisions_made) if decisions_made else 0
        }
        
        # Determinar sucesso geral
        success = (results.get('status') == 'COMPLETED' and 
                  len(failed_chunks) == 0 and 
                  len(decisions_made) > 0)
        
        return self.generate_feedback(
            success=success,
            decisions_made=decisions_made,
            problems_found=problems_found,
            recommendations=recommendations,
            metrics=metrics
        )

def main():
    """Função principal do Agent David"""
    david = AgentDavid()
    
    success = david.execute()
    
    if success:
        print(f"\n✅ Agent David IA concluído com sucesso!")
        print(f"📁 Verifique temp_audio/ para chunks processados")
        print(f"📋 Verifique chunks/david_results.json para estratégias IA")
    else:
        print(f"\n❌ Falha no processamento do Agent David")

if __name__ == "__main__":
    main()