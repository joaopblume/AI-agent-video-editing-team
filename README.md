# Video Edit Team - Sistema de Edição Automática com IA

## Visão Geral

O Video Edit Team é um sistema revolucionário de edição de vídeos 100% automatizado, utilizando inteligência artificial. O projeto implementa uma arquitetura de "funcionários virtuais" especializados, cada um responsável por uma etapa específica do processo de edição, todos coordenados por um agente central.

## Conceito de "Funcionários" e Coordenação

### Arquitetura de Agentes Especializados

O sistema funciona como uma equipe de edição profissional, onde cada "funcionário" (agente IA) tem uma especialidade:

- **Funcionário de Áudio** - Remove gagueiras, palavras de preenchimento e pausas desnecessárias
- **Funcionário de Transcrição** - Converte fala em texto para análise semântica
- **Funcionário de Visão** - Analisa o conteúdo visual e identifica momentos-chave
- **Funcionário de Edição** - Aplica efeitos e ajustes dinâmicos de câmera
- **Funcionário de Avaliação** - Controle de qualidade e aprovação final
- **Coordenador Geral** - Gerencia o pipeline entre todos os funcionários

### Fluxo de Trabalho Coordenado

O **Coordenador** supervisiona todo o processo, garantindo que:
- Cada funcionário receba as informações necessárias
- O trabalho flua de forma sequencial e eficiente
- Problemas sejam identificados e corrigidos automaticamente
- A qualidade final atenda aos padrões estabelecidos

## Fluxo Ideal do Projeto

### 1. **Entrada de Vídeo**
- Vídeos brutos são colocados na pasta `raw/`
- Sistema detecta automaticamente novos arquivos

### 2. **Processamento Coordenado**
```
Vídeo Bruto → Funcionário de Áudio → Funcionário de Transcrição → 
Funcionário de Visão → Funcionário de Edição → Funcionário de Avaliação → 
Vídeo Final Editado
```

### 3. **Controle de Qualidade**
- Avaliação automática da qualidade
- Loop de refinamento se necessário
- Aprovação final automatizada

### 4. **Saída Final**
- Vídeo editado disponível em `processed/`
- Logs detalhados do processo em `logs/`

## Objetivo Principal

**Editar vídeos com 100% de automação usando IA**, eliminando:
- Intervenção manual no processo de edição
- Necessidade de conhecimento técnico em edição
- Tempo gasto em tarefas repetitivas
- Inconsistências na qualidade final

## Tecnologias Utilizadas

- **Python 3.11+** - Linguagem principal
- **Ollama + llama3.2:3b** - LLM local para coordenação dos agentes
- **Whisper** - Transcrição de fala para texto
- **FFmpeg** - Processamento de vídeo/áudio
- **OpenCV** - Tarefas de visão computacional
- **Docker + Docker Compose** - Containerização e orquestração
- **ROCm** - Aceleração GPU AMD

## Como Usar


### Processamento de Vídeos
```bash
# 1. Adicione seus vídeos à pasta de entrada
cp seu_video.mp4 raw/

# 2. Inicie o processamento automatizado
docker-compose up main-processor

# 3. Aguarde o processo e colete o resultado
ls processed/
```

## Estrutura do Projeto


## Requisitos do Sistema
