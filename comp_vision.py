import cv2
import mediapipe as mp
import math


class VisionController:

    #função para inicializar a câmera e o modelo de detecção de pose do MediaPipe
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.7, 
            min_tracking_confidence=0.7
        )
        
        self.cap = cv2.VideoCapture(0)

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
            self.mp_drawing.draw_landmarks(
                frame, 
                resultados.pose_landmarks, 
                self.mp_pose.POSE_CONNECTIONS
            )

            landmarks = resultados.pose_landmarks.landmark
            
            pulso_esq = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST]
            pulso_dir = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST]

            if pulso_esq.visibility > 0.5 and pulso_dir.visibility > 0.5:
                
                dx = pulso_dir.x - pulso_esq.x
                dy = pulso_dir.y - pulso_esq.y
                
                angulo_radianos = math.atan2(dy, dx)
                angulo_graus = math.degrees(angulo_radianos)
                angulo_max = 45.0
                
                angulo_limitado = max(-angulo_max, min(angulo_max, angulo_graus))
                
                multiplicador_velocidade = angulo_limitado / angulo_max

        return multiplicador_velocidade, frame

    # destrutor
    def close(self):
        self.cap.release()
        cv2.destroyAllWindows()



