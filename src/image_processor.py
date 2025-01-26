import math

import cv2 as cv
import numpy as np

from .config import (
    BACKGROUND_COLOR, BACKGROUND_DARK_COLOR,
    MESH_COLOR, MESH_LIGHT_COLOR, MESH_DARK_COLOR,
    LEFT_IRIS, RIGHT_IRIS,
    L_H_LEFT, L_H_RIGHT,
    R_H_LEFT, R_H_RIGHT,
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

    def update_colors(self, color_name, hex_color):
        """Update color values"""
        rgb_color = self.hex_to_rgb(hex_color)
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
    def create_gradient_background(height, width, base_color, brightness_increase=40):
        """Create a radial gradient background with lighter center.

        Args:
            height (int): Frame height
            width (int): Frame width
            base_color (tuple): Base BGR color for the background
            brightness_increase (int): How much brighter the center should be

        Returns:
            numpy.ndarray: Frame with radial gradient
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
        gradient_mask = dist_from_center / max_dist

        # Create lighter color for center
        lighter_color = np.minimum(np.array(base_color) + brightness_increase, 255)

        # Create gradient frame
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        for c in range(3):  # For each color channel
            frame[:, :, c] = (gradient_mask * base_color[c] +
                            (1 - gradient_mask) * lighter_color[c])

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
        # Draw mesh
        mesh_rgb = self.hex_to_rgb(self.mesh_color)
        mesh_color = self.rgb_to_bgr(mesh_rgb)
        for point in mesh_points:
            cv.circle(frame, tuple(point), 1, mesh_color, -1)

        # Draw eyes
        # Convert colors to BGR
        mesh_light_rgb = self.hex_to_rgb(self.mesh_light_color)
        iris_color = self.rgb_to_bgr(mesh_light_rgb)
        # eye_inner_corner_color = iris_color
        # eye_outer_corner_color = iris_color

        cv.circle(frame, center_left, int(l_radius), iris_color, 2, cv.LINE_AA)
        cv.circle(frame, center_right, int(r_radius), iris_color, 2, cv.LINE_AA)

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
        self._draw_mesh(frame, mesh_points, center_left, center_right, l_radius, r_radius)

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
