# Pink Saur Game (Jumping Sky)

Um jogo de plataforma 2D completo, desenvolvido em Python com a biblioteca Pygame Zero. O objetivo é guiar o personagem Pink Saur através de uma fase cheia de desafios e inimigos para capturar a moeda da vitória no final.

## 🚀 Funcionalidades

* **Personagem Animado:** Animações de personagem para os estados de parado (`idle`), correndo (`run`) e pulando (`jump`).
* **Inimigos com IA:** Inimigos animados com uma IA de patrulha simples, que pausam nas bordas de suas rotas.
* **Física de Plataforma:** Sistema de gravidade e pulo que interage com múltiplas plataformas.
* **Câmera Dinâmica:** Uma câmera suave que segue o movimento do jogador pelo nível.
* **Design de Nível por Tiles:** Fase construída usando um mapa de texto (tile map), com suporte a tilesheets para um visual mais rico e pontas de acabamento para plataformas.
* **Sistema de Jogo Completo:**
    * Menu principal com botões para Iniciar, Ligar/Desligar Som e Sair.
    * Tela de "Game Over" com opções para Reiniciar ou Sair.
    * Tela de "Vitória" com as mesmas opções.
* **Áudio:** Música de fundo, efeitos sonoros para pulo, passos, coleta de item e derrota.
* **Interface Polida:** Uso de fontes personalizadas e feedback sonoro nos botões do menu.
* **Executável Standalone:** O jogo foi empacotado em um arquivo `.exe` usando PyInstaller para ser jogado em computadores Windows sem a necessidade de instalar Python.

## 🎮 Como Jogar

O objetivo é chegar até a moeda dourada no final da fase, pulando entre plataformas e desviando dos inimigos.

### Controles
* **Setas Esquerda / Direita:** Mover o personagem.
* **Barra de Espaço:** Pular.

## ⚙️ Como Executar

Existem duas maneiras de rodar o jogo:

### Opção 1: Pelo Executável (Windows)

1.  Navegue até a pasta `dist`.
2.  Dê um duplo clique no arquivo `game.exe`.

### Opção 2: A Partir do Código Fonte (Para Desenvolvedores)

Se você tem Python instalado, pode rodar o jogo a partir do código fonte.

1.  **Instale o Pygame Zero:**
    ```bash
    pip install pgzero
    ```
2.  **Navegue até a pasta do projeto** pelo terminal.

3.  **Execute o jogo** com o seguinte comando:
    ```bash
    pgzrun game.py
    ```

## 💻 Tecnologias Utilizadas

* **Linguagem:** Python
* **Biblioteca Principal:** Pygame Zero (sobre o Pygame)
* **Empacotamento:** PyInstaller
