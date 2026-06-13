import cv2
import mediapipe as mp
import math


class VisionController:

    #função para inicializar a câmera e o modelo de detecção de pose do MediaPipe
    def __init__(self):
        self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)

        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.mp_draw = mp.solutions.drawing_utils


    #função para capturar o frame da câmera, processar a pose e calcular o ângulo de inclinação com base na posição dos pulsos
    # retorna o multiplicador e a imagem
    #com a imagem n precisa fazer nd, ela é só para mostrar o que a câmera está capturando, o multiplicador é o que realmente importa para controlar a velocidade do carrinho
    def get_tilt_angle(self):

        sucesso, frame = self.cap.read()
        if not sucesso:
            return 0.0, None

        frame = cv2.flip(frame, 1)
        
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resultados = self.pose.process(frame_rgb)

        multiplicador_velocidade = 0.0

        if resultados.pose_landmarks:
            self.mp_draw.draw_landmarks(
                frame, 
                resultados.pose_landmarks, 
                self.mp_pose.POSE_CONNECTIONS
            )

            landmarks = resultados.pose_landmarks.landmark
            
            ombro_esq = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
            ombro_dir = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]

            if ombro_esq.visibility > 0.5 and ombro_dir.visibility > 0.5:
                
                dx = abs(ombro_dir.x - ombro_esq.x)
                if dx == 0:
                    dx = 0.00001
                
                dy = ombro_esq.y - ombro_dir.y 
                
                angulo_radianos = math.atan2(dy, dx)
                angulo_graus = math.degrees(angulo_radianos)
                
                ZONA_MORTA = 4.0  
                ANGULO_MAX = 30.0  
                
                if abs(angulo_graus) < ZONA_MORTA:
                    multiplicador_velocidade = 0.0
                else:
                    angulo_limitado = max(-ANGULO_MAX, min(ANGULO_MAX, angulo_graus))
                    
                    if angulo_limitado > 0:
                        multiplicador_velocidade = (angulo_limitado - ZONA_MORTA) / (ANGULO_MAX - ZONA_MORTA)
                    else:
                        multiplicador_velocidade = (angulo_limitado + ZONA_MORTA) / (ANGULO_MAX - ZONA_MORTA)

        return multiplicador_velocidade, frame

    # destrutor
    def close(self):
        self.cap.release()
        cv2.destroyAllWindows()



