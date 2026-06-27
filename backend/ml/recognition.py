import onnxruntime as ort
import cv2
import numpy as np

from core.config import MODEL_RECOGNITION_PATH, MODEL_ALIGNMENT_PATH, REFERENCE_LANDMARKS
from core.decorators import safe_execute


class RecognitionModel:
    """Класс-обёртка для распознавания лиц с fallback-выравниванием."""
   
    def __init__(self):
        self.rec_session = ort.InferenceSession(
            MODEL_RECOGNITION_PATH,
            providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
        )
        self.rec_input_name = self.rec_session.get_inputs()[0].name

        self.alig_session = ort.InferenceSession(
            MODEL_ALIGNMENT_PATH,
            providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
        )
        self.alig_input_name = self.alig_session.get_inputs()[0].name
        self.use_alignment = True

    def _decode_scrfd_landmarks(self, outputs: list, input_shape: tuple) -> np.ndarray:
        """Декодирование координат точек лица из вывода SCRFD."""
        scores_list, kpss_list = [], []
       
        for idx, stride in enumerate([8, 16, 32]):
            scores, kpss = outputs[idx][0], outputs[idx + 6][0]
            h, w = input_shape[0] // stride, input_shape[1] // stride
            y, x = np.mgrid[0:h, 0:w]
           
            anchors = np.repeat((np.stack([x, y], axis=-1).astype(np.float32) * stride).reshape(-1, 2), 2, axis=0)
            scores_list.append(scores)
            kpss_list.append(kpss.reshape(-1, 5, 2) * stride + anchors[:, None, :])
           
        all_scores, all_kpss = np.vstack(scores_list), np.vstack(kpss_list)
        best_idx = np.argmax(all_scores)
       
        return all_kpss[best_idx] if all_scores[best_idx][0] >= 0.3 else None

    @safe_execute(default_return=np.zeros(512, dtype=np.float32))
    def preprocess_face(self, face: np.ndarray) -> np.ndarray:
        """Выравнивание лица и извлечение векторного эмбеддинга."""
        face_rgb = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
        aligned_face = None
       
        h_orig, w_orig = face_rgb.shape[:2]
        blob = (cv2.resize(face_rgb, (640, 640)).astype(np.float32) - 127.5) / 128.0
       
        outputs = self.alig_session.run(None, {self.alig_input_name: np.transpose(blob, (2, 0, 1))[None, ...]})
        landmarks_det = self._decode_scrfd_landmarks(outputs, (640, 640))
       
        if landmarks_det is not None:
            landmarks = landmarks_det * np.array([w_orig / 640.0, h_orig / 640.0])
            tform, _ = cv2.estimateAffinePartial2D(landmarks, REFERENCE_LANDMARKS, method=cv2.LMEDS)
            if tform is not None:
                aligned_face = cv2.warpAffine(face_rgb, tform, (112, 112), borderValue=0.0)

        if aligned_face is None:
            aligned_face = cv2.resize(face_rgb, (112, 112))

        input_tensor = (np.transpose(aligned_face.astype(np.float32), (2, 0, 1)) - 127.5) / 128.0
        vec = self.rec_session.run(None, {self.rec_input_name: input_tensor[None, ...]})[0][0]
       
        return vec / np.linalg.norm(vec)