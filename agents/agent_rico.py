#!/usr/bin/env python3
"""
RICO Agent 
Splits videos into smaller chunks for efficient processing
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any
import time
from base_agent import BaseAgent, DecisionTypes, AgentStatus

class AgenteRico(BaseAgent):

    def __init__(self):
        super().__init__("RICO", "VIDEO_CHUNKING_SPECIALIST")
        
        # Configurações específicas do Rico  
        self.default_chunk_duration = 120  # 2 minutes for chunks
        self.default_overlap = 5  # 5 seconds overlap
    
    def execute(self) -> bool:
        print(f"\n{'='*60}")
        print(f"🎬📊 {self.name}: Initiating chunking video")
        print(f"{'='*60}")
        
        # Carregar plano do Coordinator
        processing_plan = self.load_processing_plan()
        if not processing_plan:
            return False
        
        self.log_processing_step("PLAN_LOADED", AgentStatus.SUCCESS, 
                               f"Tipo: {processing_plan['content_type']}")
        
        # Buscar vídeo para processar
        video_file = self._find_video_to_process()
        if not video_file:
            self.log_processing_step("VIDEO_SEARCH", AgentStatus.ERROR, "Nenhum vídeo encontrado")
            return False
        
        # Processar chunks
        results = self._process_video_chunks(video_file, processing_plan)
        
        # Salvar resultados consolidados
        self.save_results(results)
        
        # Gerar feedback para o Coordinator
        self._generate_rico_feedback(results, processing_plan)
        
        return results['status'] == 'COMPLETED'
    
    def _find_video_to_process(self) -> str:
        """Busca vídeo para processar na pasta raw/"""
        raw_dir = Path('raw')
        if not raw_dir.exists():
            return None
        
        video_files = list(raw_dir.glob('*.mp4'))
        if not video_files:
            return None
        
        # Pegar primeiro vídeo encontrado
        video_file = str(video_files[0])
        print(f"🎥 Vídeo encontrado: {Path(video_file).name}")
        return video_file
    
    def _process_video_chunks(self, video_file: str, processing_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Processa vídeo em chunks conforme plano"""
        print(f"\n🔧 {self.name}: Processando vídeo em chunks...")
        
        decisions = []
        
        # Obter duração do vídeo
        duration = self._get_video_duration(video_file)
        if duration <= 0:
            return {'status': 'FAILED', 'error': 'Não foi possível obter duração do vídeo'}
        
        # Decisão sobre estratégia de chunking
        chunk_decision = self.create_decision_record(
            decision_type=DecisionTypes.CHUNKING_STRATEGY,
            decision=f"chunks de {self.default_chunk_duration}s com overlap de {self.default_overlap}s",
            reasoning=f"Vídeo de {duration:.1f}s requer chunks para processamento eficiente",
            confidence=0.95,
            data_used={'video_duration': duration, 'target_type': processing_plan['content_type']}
        )
        decisions.append(chunk_decision)
        
        # Criar chunks
        chunks_created = self._create_video_chunks(video_file, duration)
        
        # Criar manifesto
        manifest_file = self._create_chunks_manifest(video_file, chunks_created)
        
        results = {
            'status': 'COMPLETED',
            'video_processed': Path(video_file).name,
            'chunks_created': len(chunks_created),
            'manifest_file': manifest_file,
            'decisions': decisions,
            'processing_time': time.time() - self.start_time
        }
        
        return results
    
    def _get_video_duration(self, video_file: str) -> float:
        """Obtém duração do vídeo usando FFprobe"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', video_file
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except Exception as e:
            print(f"❌ Erro ao obter duração: {e}")
            return 0
    
    def _create_video_chunks(self, video_file: str, duration: float) -> List[str]:
        """Cria chunks do vídeo"""
        chunks_created = []
        base_name = Path(video_file).stem
        
        start_time = 0
        chunk_number = 1
        
        while start_time < duration:
            end_time = min(start_time + self.default_chunk_duration, duration)
            chunk_filename = f"{base_name}_chunk_{chunk_number:03d}.mp4"
            chunk_path = self.chunks_dir / chunk_filename
            
            try:
                cmd = [
                    'ffmpeg', '-i', video_file,
                    '-ss', str(start_time),
                    '-t', str(end_time - start_time),
                    '-c', 'copy',
                    '-avoid_negative_ts', 'make_zero',
                    '-y', str(chunk_path)
                ]
                
                subprocess.run(cmd, capture_output=True, text=True, check=True)
                
                if chunk_path.exists():
                    chunks_created.append(str(chunk_path))
                    print(f"   ✅ Chunk criado: {chunk_path.name}")
                
            except subprocess.CalledProcessError as e:
                print(f"   ❌ Erro ao criar chunk {chunk_number}: {e}")
            
            start_time = start_time + self.default_chunk_duration - self.default_overlap
            chunk_number += 1
        
        return chunks_created
    
    def _create_chunks_manifest(self, video_file: str, chunks_list: List[str]) -> str:
        """Cria manifesto dos chunks"""
        manifest = {
            'original_video': Path(video_file).name,
            'total_chunks': len(chunks_list),
            'chunks': [],
            'created_by': self.name,
            'created_at': time.time(),
            'ready_for_coordinator': True
        }
        
        for i, chunk_path in enumerate(chunks_list):
            chunk_file = Path(chunk_path)
            if chunk_file.exists():
                manifest['chunks'].append({
                    'chunk_number': i + 1,
                    'filename': chunk_file.name,
                    'path': str(chunk_path),
                    'size_mb': chunk_file.stat().st_size / (1024 * 1024),
                    'status': 'READY_FOR_PROCESSING'
                })
        
        # Salvar manifesto
        manifest_file = self.chunks_dir / f"{Path(video_file).stem}_manifest.json"
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Manifesto salvo: {manifest_file}")
        return str(manifest_file)
    
    def _generate_rico_feedback(self, results: Dict[str, Any], processing_plan: Dict[str, Any]):
        """Gera feedback do Rico para o Coordinator"""
        success = results['status'] == 'COMPLETED'
        
        recommendations = []
        if success:
            recommendations.append(f"Chunks prontos para processamento: {results['chunks_created']} arquivos")
            recommendations.append("David pode prosseguir com limpeza de áudio")
            recommendations.append("Saimon pode analisar conteúdo dos chunks")
        
        metrics = {
            'chunks_created': results.get('chunks_created', 0),
            'processing_efficiency': 1.0 if success else 0.0,
            'confidence_score': 0.95 if success else 0.3
        }
        
        self.generate_feedback(
            success=success,
            decisions_made=results.get('decisions', []),
            recommendations=recommendations,
            metrics=metrics
        )
    
    def understand_task(self, instructions_file: str) -> Dict[str, Any]:
        """
        Rico COMPREENDE as instruções recebidas
        """
        print(f"\n🧠 {self.name}: Analisando instruções...")
        
        try:
            with open(instructions_file, 'r', encoding='utf-8') as f:
                instructions = json.load(f)
            
            print(f"✅ {self.name}: Instruções compreendidas!")
            print(f"📁 Arquivo: {instructions['file_name']}")
            print(f"⏱️  Duração: {instructions['duration_seconds']:.1f}s")
            print(f"🔄 Tarefa: {instructions['task']}")
            
            return instructions
            
        except Exception as e:
            print(f"❌ {self.name}: Erro ao ler instruções - {e}")
            return {}
    
    def plan_chunking_strategy(self, video_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rico PLANEJA como dividir o vídeo em chunks
        """
        print(f"\n🎯 {self.name}: Planejando estratégia de chunks...")
        
        duration = video_data['duration_seconds']
        chunk_duration = video_data['instructions']['chunk_duration']
        overlap = video_data['instructions']['overlap_seconds']
        
        chunks_plan = []
        start_time = 0
        chunk_number = 1
        
        while start_time < duration:
            end_time = min(start_time + chunk_duration, duration)
            
            chunk_info = {
                'chunk_number': chunk_number,
                'start_time': start_time,
                'end_time': end_time,
                'duration': end_time - start_time,
                'overlap_next': overlap if end_time < duration else 0
            }
            
            chunks_plan.append(chunk_info)
            
            # Próximo chunk com overlap
            start_time = end_time - overlap
            chunk_number += 1
            
            # Evitar chunks muito pequenos no final
            if duration - start_time < chunk_duration * 0.3:
                break
        
        print(f"📊 {self.name}: Planejamento concluído - {len(chunks_plan)} chunks")
        for i, chunk in enumerate(chunks_plan):
            print(f"   Chunk {chunk['chunk_number']}: {chunk['start_time']:.1f}s → {chunk['end_time']:.1f}s")
        
        return chunks_plan
    
    def create_chunks(self, video_data: Dict[str, Any], chunks_plan: List[Dict[str, Any]]) -> List[str]:
        """
        Rico EXECUTA a criação dos chunks
        """
        print(f"\n⚙️ {self.name}: Iniciando criação de chunks...")
        
        input_file = video_data['file_path']
        base_name = Path(video_data['file_name']).stem
        created_chunks = []
        
        for chunk in chunks_plan:
            chunk_filename = f"{base_name}_chunk_{chunk['chunk_number']:03d}.mp4"
            chunk_path = self.chunks_dir / chunk_filename
            
            print(f"🔧 Criando: {chunk_filename}")
            
            try:
                # Comando FFmpeg para extrair chunk
                cmd = [
                    'ffmpeg',
                    '-i', input_file,
                    '-ss', str(chunk['start_time']),
                    '-t', str(chunk['duration']),
                    '-c', 'copy',  # Copy streams sem re-encoding
                    '-avoid_negative_ts', 'make_zero',
                    '-y',  # Overwrite if exists
                    str(chunk_path)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                
                if chunk_path.exists():
                    created_chunks.append(str(chunk_path))
                    print(f"   ✅ Chunk criado: {chunk_path.name}")
                else:
                    print(f"   ❌ Falha ao criar chunk: {chunk_filename}")
                    
            except subprocess.CalledProcessError as e:
                print(f"   ❌ Erro FFmpeg: {e}")
                continue
        
        print(f"\n✨ {self.name}: {len(created_chunks)} chunks criados com sucesso!")
        return created_chunks
    
    def create_chunk_manifest(self, video_data: Dict[str, Any], chunks_list: List[str]) -> str:
        """
        Rico cria um manifesto com informações dos chunks para o Coordinator
        """
        print(f"\n📋 {self.name}: Criando manifesto dos chunks...")
        
        manifest = {
            'original_video': video_data['file_name'],
            'total_chunks': len(chunks_list),
            'chunks': [],
            'created_by': self.name,
            'created_at': time.time(),
            'ready_for_coordinator': True
        }
        
        for i, chunk_path in enumerate(chunks_list):
            chunk_file = Path(chunk_path)
            if chunk_file.exists():
                manifest['chunks'].append({
                    'chunk_number': i + 1,
                    'filename': chunk_file.name,
                    'path': str(chunk_path),
                    'size_mb': chunk_file.stat().st_size / (1024 * 1024),
                    'status': 'READY_FOR_PROCESSING'
                })
        
        # Salvar manifesto
        manifest_file = self.chunks_dir / f"{Path(video_data['file_name']).stem}_manifest.json"
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Manifesto salvo: {manifest_file}")
        return str(manifest_file)
    
    def process_video(self, instructions_file: str) -> bool:
        """
        Método principal do Agente Rico - processa um vídeo completo
        """
        print(f"\n{'='*60}")
        print(f"🎬 {self.name}: INICIANDO PROCESSAMENTO")
        print(f"{'='*60}")
        
        # 1. Compreender tarefa
        video_data = self.understand_task(instructions_file)
        if not video_data:
            return False
        
        # 2. Planejar chunks
        chunks_plan = self.plan_chunking_strategy(video_data)
        if not chunks_plan:
            return False
        
        # 3. Criar chunks
        created_chunks = self.create_chunks(video_data, chunks_plan)
        if not created_chunks:
            return False
        
        # 4. Criar manifesto para Coordinator
        manifest_file = self.create_chunk_manifest(video_data, created_chunks)
        
        print(f"\n🎉 {self.name}: MISSÃO CUMPRIDA!")
        print(f"✅ Chunks criados: {len(created_chunks)}")
        print(f"📋 Manifesto: {manifest_file}")
        print(f"👥 Próximo: Coordinator deve processar o manifesto")
        
        return True

def main():
    """Função principal do Agente Rico"""
    rico = AgenteRico()
    
    # Buscar arquivos de instruções
    chunks_dir = Path('chunks')
    instruction_files = list(chunks_dir.glob('*_instructions.json'))
    
    if not instruction_files:
        print(f"📭 {rico.name}: Nenhuma instrução encontrada em chunks/")
        print("💡 Execute video_processor.py primeiro para gerar instruções")
        return
    
    print(f"📬 {rico.name}: Encontradas {len(instruction_files)} instrução(ões)")
    
    for instruction_file in instruction_files:
        print(f"\n🎯 Processando: {instruction_file.name}")
        success = rico.process_video(str(instruction_file))
        
        if success:
            # Mover arquivo de instrução para indicar que foi processado
            processed_file = instruction_file.with_suffix('.processed')
            instruction_file.rename(processed_file)
            print(f"📁 Instrução marcada como processada: {processed_file.name}")

if __name__ == "__main__":
    main()