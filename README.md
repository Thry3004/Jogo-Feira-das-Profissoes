# Jogo de Nave com Controle de Inclinação por IA

Este projeto é um jogo arcade vertical onde o jogador controla uma nave espacial desviando de asteroides. O diferencial é o sistema de controle, que utiliza visão computacional (OpenCV e MediaPipe) para detectar a inclinação dos pulsos do jogador. A nave se move lateralmente com velocidade proporcional ao ângulo de inclinação do corpo.

## Tecnologias Envolvidas

*   **Python**: Linguagem de programação principal.
*   **Pygame**: Biblioteca para o desenvolvimento do jogo.
*   **OpenCV**: Biblioteca para visão computacional.
*   **MediaPipe**: Framework para detecção de pose e reconhecimento de gestos.

## Como Usar

1.  **Pré-requisitos**: Certifique-se de ter Python instalado em sua máquina.
2.  **Instalação das dependências**: Instale as bibliotecas necessárias:
    ```bash
    pip install pygame opencv-python mediapipe
    ```
3.  **Executar o jogo**: Rode o arquivo `main.py` para iniciar o jogo:
    ```bash
    python main.py
    ```
4.  **Controles**: Posicione-se em frente à câmera com os braços abertos na altura dos ombros. Incline o corpo para a esquerda ou direita para mover a nave. A velocidade de movimento é proporcional à inclinação dos seus pulsos.
