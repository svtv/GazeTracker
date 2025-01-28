import math

import cv2 as cv
import numpy as np

from .config import (
    BACKGROUND_COLOR, BACKGROUND_DARK_COLOR,
    MESH_COLOR, MESH_LIGHT_COLOR, MESH_DARK_COLOR,
    LEFT_IRIS, RIGHT_IRIS,
    L_H_LEFT, L_H_RIGHT,
    R_H_LEFT, R_H_RIGHT,
    SHOW_DISTANCE,
    EYES_DISPLAY_SCALE,
    EYES_VERTICAL_OFFSET,
    EYE_STYLE,
    IRIS_DETAIL_LEVEL,
    IRIS_OUTER_COLOR,
    IRIS_INNER_COLOR,
    IRIS_HIGHLIGHT_COLOR,
    IRIS_HIGHLIGHT_SIZE,
    IRIS_HIGHLIGHT_OFFSET,
    EYEBROW_THICKNESS,
    EYEBROW_SMOOTHING,
    LINE_THICKNESS,
    LINE_SMOOTHING,
)

class ImageProcessor:
    """Image processing and enhancement class"""

    def __init__(self, app, modules):
        self.app = app
        self.modules = modules

        self.background_dark_color = BACKGROUND_DARK_COLOR
        self.mesh_dark_color = MESH_DARK_COLOR
        self.mesh_color = MESH_COLOR
        self.mesh_light_color = MESH_LIGHT_COLOR
        self.background_color = BACKGROUND_COLOR
        self.brightness_increase = 40

        # Настройки отображения
        self.show_distance = SHOW_DISTANCE
        self.eyes_display_scale = EYES_DISPLAY_SCALE
        self.eyes_vertical_offset = EYES_VERTICAL_OFFSET
        self.eye_style = EYE_STYLE

        # Настройки детализации глаз
        self.iris_detail_level = IRIS_DETAIL_LEVEL
        self.iris_outer_color = IRIS_OUTER_COLOR
        self.iris_inner_color = IRIS_INNER_COLOR
        self.iris_highlight_color = IRIS_HIGHLIGHT_COLOR
        self.iris_highlight_size = IRIS_HIGHLIGHT_SIZE
        self.iris_highlight_offset = IRIS_HIGHLIGHT_OFFSET
        self.eyebrow_thickness = EYEBROW_THICKNESS
        self.eyebrow_smoothing = EYEBROW_SMOOTHING
        self.line_thickness = LINE_THICKNESS
        self.line_smoothing = LINE_SMOOTHING

        # Предварительно вычисляем цвета для _draw_mesh
        self._mesh_color_bgr = self.rgb_to_bgr(self.hex_to_rgb(self.mesh_color))
        self._iris_color_bgr = self.rgb_to_bgr(self.hex_to_rgb(self.mesh_light_color))
        self._background_color_bgr = self.rgb_to_bgr(self.hex_to_rgb(self.background_color))

        # Предварительно определяем индексы точек
        self._left_eye_details = np.array([33, 246, 161, 160, 159, 158, 157, 173, 133, 155, 154, 153, 145, 144, 163, 7])
        self._right_eye_details = np.array([362, 398, 384, 385, 386, 387, 388, 466, 263, 249, 390, 373, 374, 380, 381, 382])
        self._left_eyebrow = np.array([70, 63, 105, 66, 107, 55, 65, 52, 53])
        self._right_eyebrow = np.array([300, 293, 334, 296, 336, 285, 295, 282, 283])

        # Создаем заранее массивы для линий
        self._left_eye_lines = np.column_stack((self._left_eye_details, np.roll(self._left_eye_details, -1)))
        self._right_eye_lines = np.column_stack((self._right_eye_details, np.roll(self._right_eye_details, -1)))
        self._left_eyebrow_lines = np.column_stack((self._left_eyebrow[:-1], self._left_eyebrow[1:]))
        self._right_eyebrow_lines = np.column_stack((self._right_eyebrow[:-1], self._right_eyebrow[1:]))

    def _update_colors(self):
        """Обновляем цвета в зависимости от текущей темы"""
        # Обновляем предварительно вычисленные цвета
        self._mesh_color_bgr = self.rgb_to_bgr(self.hex_to_rgb(self.mesh_color))
        self._iris_color_bgr = self.rgb_to_bgr(self.hex_to_rgb(self.mesh_light_color))
        self._background_color_bgr = self.rgb_to_bgr(self.hex_to_rgb(self.background_color))

    def update_colors(self, color_name, hex_color):
        """Update color values"""
        # rgb_color = self.hex_to_rgb(hex_color)
        # bgr_color = self.rgb_to_bgr(rgb_color)

        if color_name == "Background Dark":
            self.background_dark_color = hex_color
        elif color_name == "Mesh Dark":
            self.mesh_dark_color = hex_color
        elif color_name == "Mesh":
            self.mesh_color = hex_color
        elif color_name == "Mesh Light":
            self.mesh_light_color = hex_color
        elif color_name == "Background":
            self.background_color = hex_color

    def update_brightness(self, value):
        """Update brightness increase value"""
        self.brightness_increase = int(value)

    @staticmethod
    def hex_to_rgb(hex_color):
        """Convert hex color to RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    @staticmethod
    def rgb_to_hex(rgb_color):
        """Convert RGB color to HEX"""
        if isinstance(rgb_color, str) and rgb_color.startswith('#'):
            return rgb_color
        return f'#{rgb_color[0]:02x}{rgb_color[1]:02x}{rgb_color[2]:02x}'

    @staticmethod
    def rgb_to_bgr(rgb_color):
        """Convert RGB color to BGR"""
        return rgb_color[2], rgb_color[1], rgb_color[0]

    @staticmethod
    def _create_tech_grid(height, width, base_color):
        """Создает технологичную сетку с ячейками разного размера.

        Args:
            height (int): Высота изображения
            width (int): Ширина изображения
            base_color (tuple): Базовый цвет в формате BGR
            alpha (float): Прозрачность сетки (0-1)

        Returns:
            numpy.ndarray: Изображение с сеткой
        """
        grid = np.zeros((height, width, 3), dtype=np.uint8)

        # Создаем сетку разных размеров
        cell_sizes = [64, 32, 16]  # Размеры ячеек
        colors = []

        # Создаем цвета для разных уровней сетки
        for i, size in enumerate(cell_sizes):
            # Делаем каждый следующий уровень сетки немного темнее
            factor = 1.0 - (i * 0.2)
            color = tuple(int(c * factor) for c in base_color)
            colors.append(color)

        # Рисуем сетки разных размеров
        for size, color in zip(cell_sizes, colors):
            # Вертикальные линии
            for x in range(0, width, size):
                thickness = 1 if size < 64 else 2
                cv.line(grid, (x, 0), (x, height), color, thickness)

            # Горизонтальные линии
            for y in range(0, height, size):
                thickness = 1 if size < 64 else 2
                cv.line(grid, (0, y), (width, y), color, thickness)

        return grid

    @staticmethod
    def create_gradient_background(height, width, base_color, brightness_increase=40):
        """Create a radial gradient background with lighter center and tech grid.

        Args:
            height (int): Frame height
            width (int): Frame width
            base_color (tuple): Base BGR color for the background
            brightness_increase (int): How much brighter the center should be

        Returns:
            numpy.ndarray: Frame with radial gradient and tech grid
        """
        # Create coordinates grid
        Y, X = np.ogrid[:height, :width]
        # Calculate center point
        center_y, center_x = height // 2, width // 2

        # Create radial gradient mask
        # Calculate distance from center for each pixel
        dist_from_center = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
        # Normalize distances to [0, 1] range
        max_dist = np.sqrt(center_x**2 + center_y**2)
        norm_dist = dist_from_center / max_dist

        # Create gradient effect
        gradient = 1 - norm_dist
        # Apply brightness increase
        gradient = gradient * brightness_increase

        # Create output frame
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        # Apply base color
        frame[:, :] = base_color

        # Apply brightness increase
        for i in range(3):
            frame[:, :, i] = np.clip(frame[:, :, i] + gradient, 0, 255)

        # Создаем и накладываем технологичную сетку
        grid = ImageProcessor._create_tech_grid(height, width, base_color)

        # Смешиваем сетку с фоном
        frame = cv.addWeighted(frame, 1, grid, 0.15, 0)

        return frame

    @staticmethod
    def enhance_image(frame):
        """Enhance image quality for better recognition under different lighting conditions"""
        # Apply adaptive histogram equalization
        lab = cv.cvtColor(frame, cv.COLOR_BGR2LAB)
        l, a, b = cv.split(lab)
        clahe = cv.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        limg = cv.merge((cl, a, b))

        # Convert back to BGR
        enhanced = cv.cvtColor(limg, cv.COLOR_LAB2BGR)

        # Apply gamma correction
        gamma = 1.2  # Can be adjusted based on conditions
        enhanced = ImageProcessor.adjust_gamma(enhanced, gamma)

        return enhanced

    @staticmethod
    def adjust_gamma(image, gamma=1.0):
        """Apply gamma correction to image"""
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255
            for i in np.arange(0, 256)]).astype("uint8")
        return cv.LUT(image, table)

    @staticmethod
    def euclidean_distance_3D(points):
        """
        Calculate the Euclidean distance between two points in 3D space.

        Args:
            points: A list of 3D points.

        Returns:
            The Euclidean distance between the two points.
        """
        p1 = points[0]
        p2 = points[1]
        return math.sqrt(
            (p2[0] - p1[0]) * (p2[0] - p1[0])
            + (p2[1] - p1[1]) * (p2[1] - p1[1])
            + (p2[2] - p1[2]) * (p2[2] - p1[2])
        )

    # @staticmethod
    # def estimate_head_pose(landmarks, image_size):
    #     """
    #     Estimate the head pose using facial landmarks.

    #     Args:
    #         landmarks: Facial landmarks detected by MediaPipe.
    #         image_size: Size of the input image (height, width).

    #     Returns:
    #         pitch, yaw, roll: Head pose angles in degrees.
    #     """
    #     img_h, img_w = image_size

    #     # 3D model points
    #     model_points = np.array([
    #         (0.0, 0.0, 0.0),            # Nose tip
    #         (-225.0, 170.0, -135.0),    # Left eye left corner
    #         (-150.0, -150.0, -125.0),   # Left Mouth corner
    #         (0.0, 0.0, 0.0),            # Center of the face
    #         (225.0, 170.0, -135.0),     # Right eye right corner
    #         (150.0, -150.0, -125.0)     # Right mouth corner
    #     ])

    #     # Camera internals
    #     focal_length = img_w
    #     center = (img_w/2, img_h/2)
    #     camera_matrix = np.array(
    #         [[focal_length, 0, center[0]],
    #         [0, focal_length, center[1]],
    #         [0, 0, 1]], dtype="double"
    #     )

    #     # Assuming no lens distortion
    #     dist_coeffs = np.zeros((4, 1))

    #     # 2D points
    #     image_points = np.array([
    #         landmarks[HEAD_INDICES_POSE[0]],    # Nose tip
    #         landmarks[HEAD_INDICES_POSE[1]],    # Left eye left corner
    #         landmarks[HEAD_INDICES_POSE[2]],    # Left Mouth corner
    #         landmarks[HEAD_INDICES_POSE[3]],    # Center of the face
    #         landmarks[HEAD_INDICES_POSE[4]],    # Right eye right corner
    #         landmarks[HEAD_INDICES_POSE[5]],    # Right mouth corner
    #     ], dtype="double")

    #     # Solve PnP
    #     success, rotation_vector, translation_vector = cv.solvePnP(
    #         model_points, image_points, camera_matrix, dist_coeffs)

    #     # Convert rotation vector to rotation matrix and decompose
    #     rotation_matrix, _ = cv.Rodrigues(rotation_vector)
    #     pose_matrix = cv.hconcat((rotation_matrix, translation_vector))
    #     _, _, _, _, _, _, euler_angles = cv.decomposeProjectionMatrix(pose_matrix)

    #     pitch, yaw, roll = [float(angle) for angle in euler_angles]

    #     return pitch, yaw, roll

    @staticmethod
    def normalize_pitch(pitch):
        """
        Normalize the pitch angle to be within the range of [-90, 90].

        Args:
            pitch (float): The raw pitch angle in degrees.

        Returns:
            float: The normalized pitch angle.
        """
        # Normalize to [-180, 180]
        pitch = pitch % 360
        if pitch > 180:
            pitch -= 360

        # Map to [-90, 90]
        if pitch > 90:
            pitch = 180 - pitch
        elif pitch < -90:
            pitch = -180 - pitch

        return pitch

    @staticmethod
    def blinking_ratio(landmarks):
        """
        Calculate the blinking ratio of a person.

        Args:
            landmarks: A facial landmarks in 3D normalized.

        Returns:
            The blinking ratio of the person, between 0 and 1, where 0 is fully open and 1 is fully closed.
        """
        rh_right = landmarks[R_H_RIGHT[0]]
        rh_left = landmarks[R_H_LEFT[0]]
        lh_right = landmarks[L_H_RIGHT[0]]
        lh_left = landmarks[L_H_LEFT[0]]

        # right eye horizontal distance
        rh_distance = ImageProcessor.euclidean_distance_3D([rh_right, rh_left])

        # left eye horizontal distance
        lh_distance = ImageProcessor.euclidean_distance_3D([lh_right, lh_left])

        ratio = (rh_distance + lh_distance) / 2.0
        return ratio

    @staticmethod
    def make_lighter_rgb(rgb_color, factor=0.3):
        """Make RGB color lighter by the specified factor.

        Args:
            rgb_color (tuple): Input RGB color (r, g, b)
            factor (float): Factor to lighten by, between 0 and 1

        Returns:
            tuple: Lightened RGB color
        """
        r, g, b = rgb_color
        # Calculate the amount to increase each channel
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))
        return (r, g, b)

    @staticmethod
    def make_darker_rgb(rgb_color, factor=0.3):
        """Make RGB color darker by the specified factor.

        Args:
            rgb_color (tuple): Input RGB color (r, g, b)
            factor (float): Factor to darken by, between 0 and 1

        Returns:
            tuple: Darkened RGB color
        """
        r, g, b = rgb_color
        # Calculate the amount to decrease each channel
        r = max(0, int(r * (1 - factor)))
        g = max(0, int(g * (1 - factor)))
        b = max(0, int(b * (1 - factor)))
        return (r, g, b)

    def _prepare_frame(self, frame):
        """Prepare frame for face mesh processing"""
        if not self.app.app_state.show_camera.get():
            background_rgb = self.hex_to_rgb(self.background_color)
            background_bgr = self.rgb_to_bgr(background_rgb)

            return self.create_gradient_background(
                height=frame.shape[0],
                width=frame.shape[1],
                base_color=background_bgr,
                brightness_increase=self.brightness_increase
            )
        return frame

    def _process_landmarks(self, face_landmarks, img_w, img_h):
        """Convert landmarks to numpy array and get mesh points"""
        return np.array([
            [int(point.x * img_w), int(point.y * img_h)]
            for point in face_landmarks.landmark
        ])

    def _process_eyes(self, mesh_points):
        """Process eyes and calculate normalized eye distance"""
        # Process eyes
        (l_cx, l_cy), l_radius = cv.minEnclosingCircle(mesh_points[LEFT_IRIS])
        (r_cx, r_cy), r_radius = cv.minEnclosingCircle(mesh_points[RIGHT_IRIS])
        center_left = np.array([l_cx, l_cy], dtype=np.int32)
        center_right = np.array([r_cx, r_cy], dtype=np.int32)

        # Calculate eye distance
        eye_distance = math.hypot(l_cx - r_cx, l_cy - r_cy)
        face_width = abs(mesh_points[234][0] - mesh_points[454][0])
        normalized_eye_distance = eye_distance / face_width if face_width > 0 else 0

        return center_left, center_right, l_radius, r_radius, normalized_eye_distance

    def _center_mesh_points(self, mesh_points, center_left, center_right, img_w, img_h):
        """Center mesh points when show_camera is False"""
        # Calculate offset
        window_center_x = img_w // 2
        window_center_y = img_h // 2
        mesh_center_x = np.mean(mesh_points[:, 0])
        mesh_center_y = np.mean(mesh_points[:, 1])
        offset_x = int(window_center_x - mesh_center_x)
        offset_y = int(window_center_y - mesh_center_y)

        # Apply offset
        mesh_points[:, 0] += offset_x
        mesh_points[:, 1] += offset_y
        center_left[0] += offset_x
        center_left[1] += offset_y
        center_right[0] += offset_x
        center_right[1] += offset_y

        return mesh_points, center_left, center_right

    def _draw_mesh(self, frame, mesh_points, center_left, center_right, l_radius, r_radius):
        """Draw mesh and eyes on frame"""
        if center_left is None or center_right is None:
            return frame

        height, width = frame.shape[:2]
        # display_frame = np.zeros((height, width, 3), dtype=np.uint8)
        # display_frame[:] = self._background_color_bgr

        # Определяем масштаб
        scale = self.eyes_display_scale

        # Инициализируем точки без масштабирования
        centered_points = mesh_points
        centered_center_left = center_left
        centered_center_right = center_right

        if not self.app.app_state.show_camera.get():
            # Находим центр между глазами и целевой центр экрана
            eyes_center = (center_left + center_right) * 0.5

            # Вычисляем целевой центр с учетом вертикального смещения
            vertical_offset = height * self.eyes_vertical_offset
            target_center = np.array([width * 0.5, height * 0.5 + vertical_offset])

            # Сначала применяем масштабирование к точкам относительно центра глаз
            scale_matrix = np.array([[scale, 0], [0, scale]])
            scaled_points = (mesh_points - eyes_center) @ scale_matrix + eyes_center
            scaled_center_left = (center_left - eyes_center) @ scale_matrix + eyes_center
            scaled_center_right = (center_right - eyes_center) @ scale_matrix + eyes_center

            # Затем вычисляем смещение для центрирования масштабированных точек
            scaled_eyes_center = (scaled_center_left + scaled_center_right) * 0.5
            offset = target_center - scaled_eyes_center

            # Применяем смещение к масштабированным точкам
            centered_points = scaled_points + offset
            centered_center_left = scaled_center_left + offset
            centered_center_right = scaled_center_right + offset

        # Рисуем линии глаз (векторизованная операция)
        def draw_lines(lines_indices):
            points = centered_points[lines_indices]
            points = points.reshape(-1, 2, 2).astype(np.int32)
            line_thickness = max(1, int(scale * self.eye_style['MESH_LINE_SCALE']))
            for pt1, pt2 in points:
                cv.line(frame, tuple(pt1), tuple(pt2),
                       self._mesh_color_bgr, line_thickness, cv.LINE_AA)

        draw_lines(self._left_eye_lines)
        draw_lines(self._right_eye_lines)
        draw_lines(self._left_eyebrow_lines)
        draw_lines(self._right_eyebrow_lines)

        # Рисуем точки (векторизованная операция)
        all_points = np.concatenate([
            centered_points[self._left_eye_details],
            centered_points[self._right_eye_details],
            centered_points[self._left_eyebrow],
            centered_points[self._right_eyebrow]
        ]).astype(np.int32)

        point_size = max(1, int(scale * self.eye_style['POINT_SCALE']))
        for point in all_points:
            cv.circle(frame, tuple(point), point_size, self._mesh_color_bgr, -1, cv.LINE_AA)

        # Оптимизированное рисование глаз
        def draw_eye(center, radius):
            center = tuple(map(int, center))

            # Применяем масштаб только если камера выключена
            if not self.app.app_state.show_camera.get():
                scaled_radius = int(radius * scale)
            else:
                scaled_radius = int(radius)

            # Рисуем радужку
            iris_thickness = max(1, int(scaled_radius * self.eye_style['IRIS_THICKNESS']))
            cv.circle(frame, center, scaled_radius, self._iris_color_bgr, iris_thickness, cv.LINE_AA)

            # Рисуем зрачок
            pupil_radius = int(scaled_radius * self.eye_style['PUPIL_SCALE'])
            cv.circle(frame, center, pupil_radius, self._iris_color_bgr, -1, cv.LINE_AA)

            # Добавляем блик
            highlight_size = int(scaled_radius * self.eye_style['HIGHLIGHT_SCALE'])
            highlight_offset = int(scaled_radius * self.eye_style['HIGHLIGHT_OFFSET'])

            # Основной блик
            highlight_pos = (
                center[0] + highlight_offset,
                center[1] - highlight_offset
            )
            cv.circle(frame, highlight_pos, highlight_size, (255, 255, 255), -1, cv.LINE_AA)

            # Дополнительный маленький блик для реалистичности
            small_highlight_pos = (
                center[0] - highlight_offset // 2,
                center[1] + highlight_offset // 2
            )
            cv.circle(frame, small_highlight_pos, highlight_size // 2,
                     (255, 255, 255), -1, cv.LINE_AA)

        # Рисуем оба глаза
        draw_eye(centered_center_left, l_radius)
        draw_eye(centered_center_right, r_radius)

        # Добавляем текст с расстоянием (вычисляем только если нужно)
        if self.show_distance:
            eye_distance = np.linalg.norm(centered_center_right - centered_center_left)
            cv.putText(frame, f"Eye Distance: {eye_distance:.1f}px",
                      (10, height - 20), cv.FONT_HERSHEY_SIMPLEX, 0.7, self._mesh_color_bgr, 1, cv.LINE_AA)

        return frame

    def _draw_text(self, frame, normalized_eye_distance):
        """Draw eye distance text on frame"""
        screen_text = self.app.format_eye_distance(normalized_eye_distance)
        mesh_dark_rgb = self.hex_to_rgb(self.mesh_dark_color)
        screen_text_color = self.rgb_to_bgr(mesh_dark_rgb)

        screen_text_size = cv.getTextSize(
            text=screen_text,
            fontFace=cv.FONT_HERSHEY_SIMPLEX,
            fontScale=0.4,
            thickness=1)[0]

        cv.putText(
            img=frame,
            text=screen_text,
            org=((frame.shape[1] - screen_text_size[0]) // 2, frame.shape[0] - 20),
            fontFace=cv.FONT_HERSHEY_SIMPLEX,
            fontScale=0.4,
            color=screen_text_color,
            thickness=1,
            lineType=cv.LINE_AA)

    def _process_face_mesh_impl(self, frame, mesh_results):
        """Process face mesh detection results and draw on frame"""
        # Get frame dimensions
        img_h, img_w = frame.shape[:2]

        # Prepare frame
        frame = self._prepare_frame(frame)

        # Process landmarks
        face_landmarks = mesh_results.multi_face_landmarks[0]
        mesh_points = self._process_landmarks(face_landmarks, img_w, img_h)

        # Process eyes
        (
            center_left,
            center_right,
            l_radius,
            r_radius,
            normalized_eye_distance
        ) = self._process_eyes(mesh_points)

        # Center mesh points if needed
        if not self.app.app_state.show_camera.get():
            mesh_points, center_left, center_right = (
                self._center_mesh_points(
                    mesh_points,
                    center_left,
                    center_right,
                    img_w,
                    img_h
                )
            )

        # Draw mesh and eyes
        frame = self._draw_mesh(frame, mesh_points, center_left, center_right, l_radius, r_radius)

        # Draw text
        self._draw_text(frame, normalized_eye_distance)

        return {
            'frame': frame,
            'normalized_eye_distance': normalized_eye_distance,
            'mesh_points': mesh_points,
        }

    def _process_face_mesh_noface(self, frame):

        screen_text = "No face detected"
        mesh_dark_rgb = self.hex_to_rgb(self.mesh_dark_color)
        screen_text_color = self.rgb_to_bgr(mesh_dark_rgb)

        # If show_camera is off, create a gradient background
        if not self.app.app_state.show_camera.get():
            background_dark_rgb = self.hex_to_rgb(self.background_dark_color)
            background_dark_bgr = self.rgb_to_bgr(background_dark_rgb)

            frame = self.create_gradient_background(
                height=frame.shape[0],
                width=frame.shape[1],
                base_color=background_dark_bgr,
                brightness_increase=self.brightness_increase
            )

        screen_text_size = cv.getTextSize(
            text=screen_text,
            fontFace=cv.FONT_HERSHEY_SIMPLEX,
            fontScale=0.4,
            thickness=1)[0]

        cv.putText(
            img=frame,
            text=screen_text,
            org=((frame.shape[1] - screen_text_size[0]) // 2, frame.shape[0] - 20),
            fontFace=cv.FONT_HERSHEY_SIMPLEX,
            fontScale=0.4,
            color=screen_text_color,
            thickness=1,
            lineType=cv.LINE_AA)

        return {
            'frame': frame,
            'normalized_eye_distance': 0,
            'mesh_points': None,
        }

    def process_face_mesh(self, frame, mesh_results):
        """Process face mesh detection results and draw on frame

        Args:
            frame: Input frame
            mesh_results: Face mesh detection results

        Returns:
            dict: Processing results containing frame and detection flags
        """
        if mesh_results.multi_face_landmarks:
            return self._process_face_mesh_impl(frame, mesh_results)
        return self._process_face_mesh_noface(frame)
