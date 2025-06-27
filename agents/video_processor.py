#!/usr/bin/env python3
"""
Video Processor - Entry point para o sistema de edição de vídeo com IA
Monitora pasta raw/ e inicia processamento com Agente Rico
"""

import os
import json
import time
from pathlib import Path
import subprocess
from typing import List, Dict, Any

class VideoMetadata:
    """Classe para extrair e organizar metadados do vídeo"""
    
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.metadata = self._extract_metadata()
    
    def _extract_metadata(self) -> Dict[str, Any]:
        """Extrai metadados usando FFprobe"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', self.video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
            
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            print(f"Erro ao extrair metadados: {e}")
            return {}
    
    def get_duration(self) -> float:
        """Retorna duração do vídeo em segundos"""
        try:
            return float(self.metadata['format']['duration'])
        except (KeyError, ValueError):
            return 0.0
    
    def get_video_info(self) -> Dict[str, Any]:
        """Retorna informações do stream de vídeo"""
        try:
            for stream in self.metadata['streams']:
                if stream['codec_type'] == 'video':
                    return {
                        'width': stream.get('width', 0),
                        'height': stream.get('height', 0),
                        'fps': eval(stream.get('r_frame_rate', '0/1')),
                        'codec': stream.get('codec_name', 'unknown')
                    }
        except:
            pass
        return {}
    
    def to_agent_format(self) -> Dict[str, Any]:
        """Converte metadados para formato que o Agente Rico pode entender"""
        return {
            'file_path': self.video_path,
            'file_name': os.path.basename(self.video_path),
            'duration_seconds': self.get_duration(),
            'video_info': self.get_video_info(),
            'file_size_mb': os.path.getsize(self.video_path) / (1024 * 1024),
            'task': 'CREATE_CHUNKS',
            'instructions': {
                'chunk_duration': 60,  # 60 segundos por chunk
                'output_directory': 'chunks',
                'preserve_quality': True,
                'overlap_seconds': 2  # 2 segundos de overlap entre chunks
            }
        }

class VideoProcessor:
    """Classe principal para processar vídeos da pasta raw/"""
    
    def __init__(self):
        self.raw_dir = Path('raw')
        self.processed_dir = Path('processed') 
        self.chunks_dir = Path('chunks')
        self.supported_formats = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
        
        # Criar diretórios se não existirem
        self.chunks_dir.mkdir(exist_ok=True)
    
    def find_videos_in_raw(self) -> List[Path]:
        """Busca vídeos na pasta raw/"""
        videos = []
        
        if not self.raw_dir.exists():
            print("❌ Pasta raw/ não encontrada")
            return videos
            
        for file_path in self.raw_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                videos.append(file_path)
                
        return videos
    
    def prepare_for_agent_rico(self, video_path: Path) -> Dict[str, Any]:
        """Prepara dados do vídeo para o Agente Rico"""
        print(f"📹 Analisando vídeo: {video_path.name}")
        
        # Extrair metadados
        metadata_extractor = VideoMetadata(str(video_path))
        agent_data = metadata_extractor.to_agent_format()
        
        # Informações adicionais para o Agente Rico
        agent_data.update({
            'agent_name': 'RICO',
            'agent_task': 'VIDEO_CHUNKING',
            'timestamp': time.time(),
            'processing_status': 'READY_FOR_CHUNKING'
        })
        
        return agent_data
    
    def save_agent_instructions(self, video_data: Dict[str, Any]) -> str:
        """Salva instruções para o Agente Rico em formato JSON"""
        instructions_file = self.chunks_dir / f"{Path(video_data['file_name']).stem}_instructions.json"
        
        with open(instructions_file, 'w', encoding='utf-8') as f:
            json.dump(video_data, f, indent=2, ensure_ascii=False)
        
        print(f"📝 Instruções salvas: {instructions_file}")
        return str(instructions_file)
    
    def process_videos(self):
        """Processa todos os vídeos encontrados na pasta raw/"""
        videos = self.find_videos_in_raw()
        
        if not videos:
            print("📁 Nenhum vídeo encontrado na pasta raw/")
            return
        
        print(f"🎬 Encontrados {len(videos)} vídeo(s) para processamento:")
        
        for video_path in videos:
            try:
                print(f"\n{'='*50}")
                print(f"🎯 Processando: {video_path.name}")
                print(f"{'='*50}")
                
                # Preparar dados para Agente Rico
                agent_data = self.prepare_for_agent_rico(video_path)
                
                # Exibir informações do vídeo
                self._display_video_info(agent_data)
                
                # Salvar instruções para o Agente Rico
                instructions_file = self.save_agent_instructions(agent_data)
                
                print(f"✅ Vídeo preparado para Agente Rico")
                print(f"📋 Próximo passo: Agente Rico deve processar {instructions_file}")
                
            except Exception as e:
                print(f"❌ Erro ao processar {video_path.name}: {e}")
    
    def _display_video_info(self, video_data: Dict[str, Any]):
        """Exibe informações do vídeo de forma formatada"""
        print(f"📊 INFORMAÇÕES DO VÍDEO:")
        print(f"   Arquivo: {video_data['file_name']}")
        print(f"   Duração: {video_data['duration_seconds']:.1f} segundos")
        print(f"   Tamanho: {video_data['file_size_mb']:.1f} MB")
        
        video_info = video_data.get('video_info', {})
        if video_info:
            print(f"   Resolução: {video_info.get('width', 0)}x{video_info.get('height', 0)}")
            print(f"   FPS: {video_info.get('fps', 0):.1f}")
            print(f"   Codec: {video_info.get('codec', 'unknown')}")
        
        instructions = video_data.get('instructions', {})
        print(f"\n🎯 INSTRUÇÕES PARA AGENTE RICO:")
        print(f"   Duração por chunk: {instructions.get('chunk_duration', 60)} segundos")
        print(f"   Pasta de saída: {instructions.get('output_directory', 'chunks')}/")
        print(f"   Overlap entre chunks: {instructions.get('overlap_seconds', 2)} segundos")
        print(f"   Preservar qualidade: {instructions.get('preserve_quality', True)}")

def main():
    """Função principal"""
    print("🎬 SISTEMA DE EDIÇÃO DE VÍDEO COM IA")
    print("=" * 50)
    print("Monitorando pasta raw/ para novos vídeos...")
    
    processor = VideoProcessor()
    processor.process_videos()
    
    print(f"\n{'=' * 50}")
    print("✨ Processamento inicial concluído!")
    print("📁 Verifique a pasta chunks/ para as instruções do Agente Rico")

if __name__ == "__main__":
    main()