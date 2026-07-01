# 🚀 Nave por Inclinação — Jogo com Controle por Visão Computacional

Um jogo arcade estilo *Space Invaders* vertical, em Python, onde você controla a nave
**inclinando o corpo na frente da webcam** — sem teclado, sem controle, sem toque. A pose
é detectada em tempo real por visão computacional, tornando o jogo ideal para exposições e
feiras: interativo, chamativo e sem periféricos.

> Feito para a **Feira das Profissões**: o jogador controla a nave com o corpo enquanto o
> público acompanha por uma tela réplica no segundo monitor.

---

## 🎯 Como funciona o controle

Você fica de frente para a câmera com os **braços abertos** (na altura dos ombros), como as
asas de um avião. O sistema mede o **ângulo da linha entre os seus cotovelos**:

- Inclinou para a **direita** → a nave vai para a **direita**.
- Inclinou para a **esquerda** → a nave vai para a **esquerda**.
- **Braços alinhados** (retos) → a nave **para**.

A velocidade é proporcional à inclinação, e o controle foi ajustado para **parar e inverter
na hora**, sem deslizar. O teclado (setas ou `A`/`D`) funciona como alternativa.

---

## ✨ Funcionalidades

- **Controle por visão computacional** — MediaPipe Pose detecta os cotovelos e converte a
  inclinação do corpo em movimento, com filtro de suavização para um controle estável.
- **Jogabilidade arcade** — ondas de inimigos que aceleram com o tempo e um **chefe final**
  ("Dado Corrompido") com tiros direcionados e ataque de laser.
- **Tiro e recarga automáticos** — a nave dispara sozinha (pente de 6 tiros) e recarrega
  ao esvaziar; foque em desviar e mirar com o corpo.
- **Ranking local** — top 10 por pontuação e tempo, salvo em `data/ranking.json`.
- **Modo espectador** — uma **janela réplica** espelha o jogo em tempo real para o público
  acompanhar num segundo monitor.
- **Janela de feedback da câmera** — mostra o vídeo com o esqueleto rastreado (ótimo para
  demonstrar a tecnologia), com tamanho ajustável.
- **Seleção de monitor** — escolha em qual tela o jogo roda (1 ou 2).
- **Multiplataforma** — roda em **Windows, Linux e macOS** (backend de câmera e modo de
  tela cheia adaptados a cada sistema).

---

## 🛠️ Tecnologias

| Tecnologia | Uso |
| --- | --- |
| **Python** | Linguagem principal |
| **Pygame** | Renderização 2D, entrada e loop do jogo |
| **OpenCV** | Acesso à webcam e exibição das janelas de feedback/réplica |
| **MediaPipe** | Detecção de pose corporal (cotovelos) |
| **NumPy** | Suporte a processamento de imagem |

---

## 📋 Requisitos

- **Python 3.10, 3.11 ou 3.12** — as versões **3.13/3.14 não são suportadas** pelo
  `mediapipe 0.10.14` (o jogo quebra em `import mediapipe`).
- Uma **webcam** funcional.
- Espaço em frente à câmera para abrir os braços.

---

## ⚙️ Instalação

Crie um ambiente virtual com Python 3.11 e instale as dependências:

**Windows** (PowerShell ou CMD):

```powershell
py -3.11 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**Linux / macOS**:

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

> **VSCode:** após criar o `venv`, selecione o interpretador dele em
> `Ctrl+Shift+P` → **"Python: Select Interpreter"** → escolha o `venv` (Python 3.11).

---

## ▶️ Como jogar

Com o `venv` ativado:

```bash
python main.py
```

1. **Digite seu nome** na tela inicial (`BACKSPACE` apaga) e pressione `ENTER`.
2. Aguarde a **contagem regressiva** (3, 2, 1, GO!).
3. **Posicione-se** de frente para a câmera, com os **braços abertos** na altura dos ombros
   (cotovelos visíveis). Um aviso na tela indica se a câmera não está te enxergando.
4. **Incline o corpo** para mover a nave e desvie dos tiros. A nave atira sozinha.
5. Elimine as ondas de inimigos e derrote o **chefe final** para vencer.

### Objetivo e pontuação

| Ação | Pontos |
| --- | --- |
| Destruir um inimigo | +100 |
| Acertar o chefe | +5 por acerto |
| Derrotar o chefe (vitória) | +1700 |

Sua pontuação e tempo entram no **ranking** (top 10). Ao vencer ou perder, `ENTER` volta
à tela inicial (digitar nome → contagem → jogar) para uma nova partida.

---

## ⌨️ Atalhos

| Tecla | Ação |
| --- | --- |
| Inclinar o corpo / `←` `→` / `A` `D` | Mover a nave |
| `F1` / `F2` | Escolher o monitor do jogo (1 / 2) — requer 2 monitores |
| `F3` | Liga/desliga a janela de **feedback da câmera** (esqueleto) |
| `F4` | Liga/desliga a **janela réplica** (para espectadores) |
| `F5` / `F6` | Diminuir / aumentar a janela de feedback |
| `F11` | Alternar tela cheia |
| `ENTER` | Confirmar nome / voltar à tela inicial (após vitória ou derrota) |
| `BACKSPACE` | Apagar caractere ao digitar o nome |
| `ESC` | Sair do jogo |

---

## 🖥️ Configuração para feira (dois monitores)

Setup recomendado para exposição:

1. **Monitor do jogador** — o jogo em tela cheia. Use `F1`/`F2` para escolher qual monitor.
2. **Monitor do público** — arraste para lá:
   - a **janela réplica** (`Jogo (replica) - Espectadores`), que espelha a partida;
   - a **janela de feedback** (`Feedback MediaPipe`), que mostra o corpo rastreado.

Ambas as janelas são **redimensionáveis** (arraste as bordas). A réplica atualiza a ~30 FPS
para não pesar no jogo (que roda a 60 FPS). No topo do `main.py` há constantes para ajustar
o padrão (`MONITOR_INICIAL`, `REPLICA_ATIVA`, `REPLICA_ALTURA`, `FEEDBACK_LARGURA`).

---

## 🎚️ Ajuste fino do controle

Se o controle estiver sensível demais, ou lento, ajuste estas constantes:

| Constante | Arquivo | Padrão | Efeito |
| --- | --- | --- | --- |
| `ZONA_MORTA` | `comp_vision.py` | `3.0` | Inclinação mínima (graus) para a nave reagir |
| `ANGULO_MAX` | `comp_vision.py` | `30.0` | Inclinação (graus) que corresponde à velocidade máxima |
| `FILTRO_ALPHA` | `comp_vision.py` | `0.4` | Suavização do movimento (maior = responsivo, menor = suave) |
| `resposta` | `main.py` (`Player.update`) | `5.0` | Rapidez com que a nave alcança a velocidade-alvo (maior = mais seco) |

Ex.: para exigir menos inclinação, diminua `ANGULO_MAX`; para um movimento mais suave,
reduza `resposta`.

---

## 💻 Compatibilidade

O jogo detecta o sistema operacional e se adapta automaticamente:

| | Windows | Linux | macOS |
| --- | --- | --- | --- |
| Backend de câmera | DirectShow | V4L2 | AVFoundation |
| Tela cheia | Borderless (não minimiza ao clicar nas outras janelas) | Exclusiva | Exclusiva |
| DPI | Ajuste automático em telas com escala ≠ 100% | — | — |

---

## 📁 Estrutura do projeto

```
Jogo-Feira-das-Profissoes/
├── main.py            # Loop do jogo, entidades, estados, HUD, colisões, janelas
├── comp_vision.py     # Webcam + MediaPipe (thread) → ângulo de inclinação
├── teste_comp.py      # Script isolado para testar/calibrar a webcam
├── requirements.txt   # Dependências (versões fixadas)
├── assets/            # Sprites (nave, inimigos, chefe, balas, HUD, efeitos) e sons
└── data/ranking.json  # Ranking local (gerado automaticamente)
```

Para testar apenas a visão computacional (sem o jogo), rode `python teste_comp.py` e
pressione `q` para sair.

---

## 🧯 Solução de problemas

| Sintoma | Causa provável / Solução |
| --- | --- |
| **Câmera preta** | Verifique a **tampa de privacidade** da webcam; reconecte o cabo USB; teste em outro app. |
| **"CAMERA NAO DETECTADA"** na tela | Outra janela/execução está usando a webcam. Feche a instância anterior e rode de novo. |
| **A nave não se move** | Fique de **braços abertos** com os cotovelos visíveis; o aviso "Abra os bracos" indica que a pose se perdeu. |
| **`ModuleNotFoundError: mediapipe`** | Python errado. Use a `venv` com **3.10–3.12** (nunca 3.13/3.14). |
| **"Run Python File" do VSCode não faz nada** | Selecione o interpretador do `venv` (Python 3.11). |
| **(Windows) câmera lenta** | No terminal, veja a linha `Camera OK: ... [DSHOW]`. Se aparecer `[MSMF]`, o backend caiu no fallback. |

---

## 🔮 Desenvolvimento futuro

- **Integrar áudio** — os efeitos e a trilha já estão em `assets/sounds/`, faltando ligá-los ao código.
- Novos tipos de inimigos com padrões de ataque variados.
- Power-ups para o jogador.
- Calibração automática da visão para diferentes ambientes e iluminações.

---

## 📄 Licença

Projeto sob a licença MIT.
