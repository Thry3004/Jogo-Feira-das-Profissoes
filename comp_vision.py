import cv2
import mediapipe as mp
import math
import sys
import threading
import time


class VisionController:
    # --- Calibração ---
    ZONA_MORTA = 5.0
    ANGULO_MAX = 45.0
    # Filtro exponencial do ângulo: alto = responsivo, baixo = suave.
    FILTRO_ALPHA = 0.6

    def __init__(self, debug_mode=False):
        # Backend de camera por sistema operacional. cv2.CAP_V4L2 e' exclusivo do
        # Linux; no Windows usamos DirectShow (abre rapido e aceita MJPG/resolucao)
        # e no macOS o AVFoundation. Se o backend preferido falhar, cai no padrao
        # do OpenCV (que escolhe automaticamente).
        if sys.platform.startswith("win"):
            backend = cv2.CAP_DSHOW
        elif sys.platform == "darwin":
            backend = cv2.CAP_AVFOUNDATION
        else:
            backend = cv2.CAP_V4L2
        self.cap = cv2.VideoCapture(0, backend)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)

        # Falha visivel: se a camera nao abrir (webcam ocupada por outro programa ou
        # por uma execucao anterior do jogo), avisa no terminal em vez de girar em silencio.
        self.camera_ok = self.cap.isOpened()
        if not self.camera_ok:
            print(
                "[VisionController] ERRO: nao foi possivel abrir a webcam (camera indice 0).\n"
                "  Causa provavel: outro programa (ou uma execucao anterior do jogo) "
                "ainda esta usando a camera.\n"
                "  Solucao: feche a outra janela/processo e rode novamente."
            )

        # ⚡ OT1: resolução reduzida (~75% menos pixels) → MediaPipe muito mais rápido.
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        # ⚡ OT-B: pedir 60fps. Sem isto, a maioria das webcams fica em 30fps
        # (piso de 33ms por frame). Em 640×360, 60fps costuma ser suportado.
        self.cap.set(cv2.CAP_PROP_FPS, 60)
        self.fps_real = self.cap.get(cv2.CAP_PROP_FPS)
        if self.camera_ok:
            print(
                "[VisionController] Camera OK: "
                f"{int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x"
                f"{int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))} @ {self.fps_real:.0f}fps"
            )

        # ⚡ OT2/OT3: modelo leve + sem suavização (o jitter é tratado por filtro
        # exponencial próprio, mais barato e sem o delay de frame do MediaPipe).
        # ⚡ OT-H: min_tracking_confidence menor mantém o tracking ativo por mais
        # tempo, evitando picos de re-detecção em movimentos rápidos de inclinação.
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=0,
            smooth_landmarks=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.3,
        )
        self.mp_draw = mp.solutions.drawing_utils

        # ⚡ OT4: processamento em thread separada (não bloqueia o loop do jogo).
        self.debug_mode = debug_mode
        self._running = True
        # ⚡ OT-D: sem fila. _last_angle/_last_frame guardam SEMPRE o valor mais
        # recente. A fila anterior devolvia o frame mais VELHO (1 frame de atraso).
        # Atribuição de float/referência é atômica sob o GIL → leitor único seguro.
        self._last_angle = 0.0
        self._last_frame = None
        self._pose_detectada = False  # exposto para feedback na HUD do jogo

        # So inicia a thread de captura se a camera realmente abriu.
        self._processing_thread = None
        if self.camera_ok:
            self._processing_thread = threading.Thread(target=self._process_loop, daemon=True)
            self._processing_thread.start()

    def _process_loop(self):
        """Thread separada: captura e processa a câmera continuamente."""
        while self._running:
            sucesso, frame = self.cap.read()
            if not sucesso:
                time.sleep(0.001)
                continue

            # ⚡ OT-E: NÃO espelhamos para a detecção. O ângulo usa dy (eixo
            # vertical, invariante a flip horizontal) e abs(dx), então o resultado
            # é idêntico com ou sem espelho. Espelhamos apenas o frame de debug.
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # ⚡ OT-C: array não-gravável → MediaPipe processa por referência (sem cópia).
            frame_rgb.flags.writeable = False
            resultados = self.pose.process(frame_rgb)

            multiplicador_alvo = 0.0
            pose_ok = False
            frame_debug = None

            if resultados.pose_landmarks:
                landmarks = resultados.pose_landmarks.landmark
                cotovelo_esq = landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW]
                cotovelo_dir = landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW]

                if cotovelo_esq.visibility > 0.5 and cotovelo_dir.visibility > 0.5:
                    pose_ok = True
                    dx = abs(cotovelo_dir.x - cotovelo_esq.x)
                    if dx == 0:
                        dx = 0.00001
                    dy = cotovelo_esq.y - cotovelo_dir.y
                    angulo_graus = math.degrees(math.atan2(dy, dx))

                    if abs(angulo_graus) >= self.ZONA_MORTA:
                        angulo_limitado = max(-self.ANGULO_MAX, min(self.ANGULO_MAX, angulo_graus))
                        if angulo_limitado > 0:
                            multiplicador_alvo = (angulo_limitado - self.ZONA_MORTA) / (self.ANGULO_MAX - self.ZONA_MORTA)
                        else:
                            multiplicador_alvo = (angulo_limitado + self.ZONA_MORTA) / (self.ANGULO_MAX - self.ZONA_MORTA)

                if self.debug_mode:
                    frame_debug = cv2.flip(frame, 1)
                    self.mp_draw.draw_landmarks(
                        frame_debug,
                        resultados.pose_landmarks,
                        self.mp_pose.POSE_CONNECTIONS,
                    )
            elif self.debug_mode:
                frame_debug = cv2.flip(frame, 1)

            # ⚡ OT-I: filtro exponencial — remove o jitter de ter desligado o
            # smooth do MediaPipe, sem reintroduzir atraso de frame.
            self._last_angle = (
                self.FILTRO_ALPHA * multiplicador_alvo
                + (1.0 - self.FILTRO_ALPHA) * self._last_angle
            )
            self._pose_detectada = pose_ok
            self._last_frame = frame_debug

    def get_tilt_angle(self):
        """Chamado pela thread principal do jogo. Sempre devolve o valor mais recente."""
        return self._last_angle, self._last_frame

    def pose_detectada(self):
        """True se ambos os cotovelos estão visíveis (para feedback na tela)."""
        return self._pose_detectada

    def close(self):
        self._running = False
        if self._processing_thread:
            self._processing_thread.join(timeout=1)
        self.cap.release()
        cv2.destroyAllWindows()
