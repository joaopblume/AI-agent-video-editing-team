<p align="center">
  <a href="" rel="noopener">
 <img width=200px height=200px src="https://i.imgur.com/6wj0hh6.jpg" alt="Video Edit Team Logo"></a>
</p>

<h3 align="center">Video Edit Team - Agentes Especializados</h3>

<div align="center">

[![Status](https://img.shields.io/badge/status-active-success.svg)]()
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![AI](https://img.shields.io/badge/AI-powered-green.svg)]()
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](/LICENSE)

</div>

---

<p align="center"> Agentes especializados em IA para edição automática de vídeos - Sistema de "funcionários virtuais" coordenados.
    <br> 
</p>

## 📝 Table of Contents

- [About](#about)
- [Getting Started](#getting_started)
- [Deployment](#deployment)
- [Usage](#usage)
- [Built Using](#built_using)
- [TODO](../TODO.md)
- [Contributing](../CONTRIBUTING.md)
- [Authors](#authors)
- [Acknowledgments](#acknowledgement)

## 🧐 Sobre os Agentes <a name = "about"></a>

O sistema Video Edit Team implementa uma arquitetura inovadora de "funcionários virtuais" - agentes especializados em IA que trabalham em conjunto para automatizar completamente o processo de edição de vídeos. Cada agente possui uma especialidade específica e é coordenado por um agente central que gerencia todo o pipeline de processamento.

Cada "funcionário" opera de forma autônoma em sua área de expertise, comunicando-se através de protocolos padronizados e garantindo que o vídeo final seja editado com qualidade profissional sem intervenção humana.

## 🏁 Iniciando com os Agentes <a name = "getting_started"></a>

Os agentes são automaticamente inicializados quando o sistema principal é executado. Cada agente roda em seu próprio container Docker e se comunica através de filas Redis.

### Pré-requisitos

Sistema base já configurado conforme README principal:

```bash
# WSL2 Ubuntu 22.04
# Docker e Docker Compose
# Ollama com llama3.2:3b
# Python 3.11+ com dependências instaladas
```

### Arquitetura dos Agentes

Cada agente segue uma estrutura padronizada:

```python
class BaseAgent:
    def __init__(self):
        self.setup_communication()
        self.load_models()
    
    def process(self, input_data):
        # Lógica específica do agente
        return processed_data
    
    def communicate_with_coordinator(self):
        # Protocolo de comunicação
        pass
```

Os agentes são inicializados automaticamente via:

```bash
docker-compose up main-processor
```

## 🔧 Testando os Agentes <a name = "tests"></a>

Cada agente possui testes unitários e de integração específicos.

### Testes de Funcionalidade Individual

Testa a capacidade de cada agente processar sua especialidade:

```bash
# Teste do Agente de Áudio
python -m pytest tests/test_audio_agent.py

# Teste do Agente de Visão
python -m pytest tests/test_vision_agent.py

# Teste completo de todos os agentes
python local/test_system.py
```

### Testes de Comunicação Entre Agentes

Verifica o protocolo de comunicação e coordenação:

```bash
# Teste de integração completa
python -m pytest tests/test_agent_coordination.py
```

## 🎈 Como os Agentes Funcionam <a name="usage"></a>

### Fluxo de Trabalho dos Agentes

1. **Coordenador** recebe vídeo bruto e inicia o pipeline
2. **Agente de Áudio** remove ruídos, gagueiras e pausas
3. **Agente de Transcrição** converte áudio em texto
4. **Agente de Visão** analisa conteúdo visual e identifica highlights
5. **Agente de Edição** aplica efeitos e transições
6. **Agente de Avaliação** valida qualidade final

### Comunicação Entre Agentes

Os agentes se comunicam via mensagens Redis seguindo este protocolo:

```json
{
  "agent_id": "audio_agent",
  "task_id": "uuid-123",
  "status": "completed",
  "data": {
    "input_path": "/temp/input.mp4",
    "output_path": "/temp/audio_cleaned.mp4",
    "metadata": {"removed_stutters": 15, "silence_removed": "30s"}
  }
}
```

## 🚀 Estrutura dos Agentes <a name = "deployment"></a>

### Organização dos Agentes

```
agents/
├── coordinator/          # Agente coordenador principal
│   ├── coordinator.py
│   └── pipeline_manager.py
├── audio_agent/          # Especialista em processamento de áudio
│   ├── audio_processor.py
│   └── speech_cleaner.py
├── transcription_agent/  # Converte fala em texto
│   ├── whisper_handler.py
│   └── text_analyzer.py
├── vision_agent/         # Análise de conteúdo visual
│   ├── frame_analyzer.py
│   └── highlight_detector.py
├── editing_agent/        # Aplicação de efeitos
│   ├── effect_applier.py
│   └── transition_manager.py
├── evaluation_agent/     # Controle de qualidade
│   ├── quality_checker.py
│   └── approval_system.py
└── shared/              # Recursos compartilhados
    ├── communication.py
    └── utils.py
```

### Deployment em Produção

Cada agente roda em container separado para escalabilidade:

```yaml
# docker-compose.yml (extract)
services:
  coordinator:
    build: ./agents/coordinator
  audio-agent:
    build: ./agents/audio_agent
    depends_on: [coordinator]
```

## ⛏️ Tecnologias dos Agentes <a name = "built_using"></a>

- [Python 3.11+](https://www.python.org/) - Linguagem principal dos agentes
- [Ollama + llama3.2:3b](https://ollama.ai/) - LLM para tomada de decisão dos agentes
- [Whisper](https://openai.com/research/whisper) - Transcrição de áudio pelo Agente de Transcrição
- [OpenCV](https://opencv.org/) - Processamento visual pelo Agente de Visão
- [FFmpeg](https://ffmpeg.org/) - Manipulação de vídeo/áudio pelos agentes
- [Redis](https://redis.io/) - Sistema de comunicação entre agentes
- [Docker](https://www.docker.com/) - Containerização de cada agente

## 👥 Especialidades dos Agentes <a name = "authors"></a>

### Agentes Principais

- **Coordenador** - Gerencia pipeline e coordena todos os funcionários
- **Funcionário de Áudio** - Remove gagueiras, ruídos e pausas desnecessárias  
- **Funcionário de Transcrição** - Converte áudio em texto para análise semântica
- **Funcionário de Visão** - Identifica momentos importantes no conteúdo visual
- **Funcionário de Edição** - Aplica efeitos dinâmicos e transições
- **Funcionário de Avaliação** - Controle de qualidade e aprovação final

### Comunicação e Protocolos

Todos os agentes seguem protocolos padronizados de comunicação via Redis, garantindo sincronização perfeita no pipeline de processamento.

## 🎉 Objetivo dos Agentes <a name = "acknowledgement"></a>

- **Automação Completa** - Eliminar intervenção humana no processo de edição
- **Especialização** - Cada agente domina perfeitamente sua área específica
- **Coordenação Inteligente** - Pipeline gerenciado por IA para máxima eficiência
- **Qualidade Profissional** - Resultado final com padrão profissional de edição
