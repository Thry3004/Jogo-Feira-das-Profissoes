# Jogo de Nave com Controle de Inclinação por Visão Computacional

Este projeto é um jogo arcade vertical desenvolvido em Python, onde o jogador controla uma nave espacial em um ambiente dinâmico, desviando de projéteis inimigos e enfrentando chefes. O principal diferencial é o sistema de controle inovador, que utiliza visão computacional para detectar a inclinação do corpo do jogador, proporcionando uma experiência de jogo imersiva e sem a necessidade de periféricos adicionais.

## Funcionalidades

*   **Controle por Visão Computacional**: Utilize a câmera do seu computador para controlar a nave. Incline seu corpo para a esquerda ou direita para mover a nave na tela, com a velocidade de movimento sendo proporcional ao ângulo de inclinação detectado pelos pulsos.
*   **Jogabilidade Arcade Clássica**: Desvie de ondas de inimigos, elimine-os e enfrente um chefe final desafiador.
*   **Sistema de Pontuação e Ranking**: Compita com outros jogadores e salve sua pontuação e tempo em um ranking local.
*   **Gráficos e Efeitos Visuais**: Sprites personalizados e efeitos visuais como explosões e lasers para uma experiência de jogo mais rica.
*   **Tela de Título e Game Over**: Interfaces claras para o início e fim do jogo, incluindo a entrada de nome do jogador e a exibição do ranking.
*   **Modo Tela Cheia**: Alterne entre o modo de janela e tela cheia para otimizar sua experiência visual.

## Tecnologias Envolvidas

*   **Python**: Linguagem de programação principal.
*   **Pygame**: Biblioteca para o desenvolvimento de jogos 2D em Python, utilizada para gráficos, áudio e interação.
*   **OpenCV (Open Source Computer Vision Library)**: Biblioteca para visão computacional, utilizada para acessar a câmera e processar as imagens.
*   **MediaPipe**: Framework do Google para construção de soluções de aprendizado de máquina, utilizado especificamente para detecção de pose corporal e reconhecimento de gestos (detecção dos pulsos e cotovelos).

## Como Jogar

### Pré-requisitos

Certifique-se de ter o [Python 3](https://www.python.org/downloads/) instalado em sua máquina.

### Instalação das Dependências

Abra o terminal na pasta raiz do projeto e instale as bibliotecas necessárias usando `pip`:

```bash
pip install -r requirements.txt
```

Ou instale manualmente:

```bash
pip install pygame opencv-python mediapipe
```

### Executar o Jogo

Após instalar as dependências, execute o arquivo `main.py`:

```bash
python main.py
```

### Controles

1.  **Posicionamento**: Posicione-se em frente à câmera com seus braços abertos na altura dos ombros. Certifique-se de que seus pulsos e cotovelos estejam visíveis para a câmera.
2.  **Movimento da Nave**: Incline seu corpo para a **esquerda** ou para a **direita** para mover a nave horizontalmente na tela. A velocidade de movimento da nave é diretamente proporcional ao ângulo de inclinação dos seus pulsos.
3.  **Tiro**: A nave atira automaticamente.
4.  **Recarregar**: A nave recarrega automaticamente após disparar todos os tiros.
5.  **Tela Cheia**: Pressione `F11` para alternar entre o modo de janela e tela cheia.
6.  **Sair do Jogo**: Pressione `ESC` a qualquer momento para sair do jogo.

## Estrutura do Projeto

*   `main.py`: Contém a lógica principal do jogo, classes de entidades (Jogador, Inimigo, Bala, Chefe, etc.), gerenciamento de estados, renderização e detecção de colisões.
*   `comp_vision.py`: Implementa a lógica de visão computacional utilizando OpenCV e MediaPipe para detectar e interpretar a pose do jogador, retornando o ângulo de inclinação.
*   `assets/`: Pasta contendo todos os recursos visuais do jogo (sprites de nave, inimigos, chefe, balas, HUD e efeitos).
*   `data/ranking.json`: Arquivo onde as pontuações do ranking são salvas e carregadas.

## Desenvolvimento Futuro

*   Implementar diferentes tipos de inimigos com padrões de ataque variados.
*   Adicionar power-ups para o jogador.
*   Integrar áudio e música para uma experiência mais imersiva.
*   Melhorar a calibração da visão computacional para diferentes ambientes e iluminações.
