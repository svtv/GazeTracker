import cv2 as cv
import math
import numpy as np

from config import *

class ImageProcessor:
    """Image processing and enhancement class"""

    @staticmethod
    def hex_to_rgb(hex_color):
        """Convert hex color to RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
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

    @staticmethod
    def estimate_head_pose(landmarks, image_size):
        """
        Estimate the head pose using facial landmarks.
        
        Args:
            landmarks: Facial landmarks detected by MediaPipe.
            image_size: Size of the input image (height, width).
        
        Returns:
            pitch, yaw, roll: Head pose angles in degrees.
        """
        img_h, img_w = image_size

        # 3D model points
        model_points = np.array([
            (0.0, 0.0, 0.0),            # Nose tip
            (-225.0, 170.0, -135.0),    # Left eye left corner
            (-150.0, -150.0, -125.0),   # Left Mouth corner
            (0.0, 0.0, 0.0),            # Center of the face
            (225.0, 170.0, -135.0),     # Right eye right corner
            (150.0, -150.0, -125.0)     # Right mouth corner
        ])

        # Camera internals
        focal_length = img_w
        center = (img_w/2, img_h/2)
        camera_matrix = np.array(
            [[focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1]], dtype="double"
        )

        # Assuming no lens distortion
        dist_coeffs = np.zeros((4, 1))

        # 2D points
        image_points = np.array([
            landmarks[_indices_pose[0]],    # Nose tip
            landmarks[_indices_pose[1]],    # Left eye left corner
            landmarks[_indices_pose[2]],    # Left Mouth corner
            landmarks[_indices_pose[3]],    # Center of the face
            landmarks[_indices_pose[4]],    # Right eye right corner
            landmarks[_indices_pose[5]],    # Right mouth corner
        ], dtype="double")

        # Solve PnP
        success, rotation_vector, translation_vector = cv.solvePnP(
            model_points, image_points, camera_matrix, dist_coeffs)

        # Convert rotation vector to rotation matrix and decompose
        rotation_matrix, _ = cv.Rodrigues(rotation_vector)
        pose_matrix = cv.hconcat((rotation_matrix, translation_vector))
        _, _, _, _, _, _, euler_angles = cv.decomposeProjectionMatrix(pose_matrix)
        
        pitch, yaw, roll = [float(angle) for angle in euler_angles]
        
        return pitch, yaw, roll

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

    @staticmethod
    def process_face_mesh(app, frame, mesh_results):
        """Process face mesh detection results and draw on frame
        
        Args:
            app: Application instance
            frame: Input frame
            mesh_results: Face mesh detection results
            
        Returns:
            dict: Processing results containing frame and detection flags
        """
        # Get frame dimensions
        img_h, img_w = frame.shape[:2]
        normalized_eye_distance = 0
        mesh_points = None
        screen_text = "No face detected"
        screen_text_color = ImageProcessor.rgb_to_bgr(YELLOW_COLOR)
                
        # If show_camera is off, create a gradient background
        if not app.show_camera.get():
            background_rgb = BACKGROUND_COLOR
            if not mesh_results.multi_face_landmarks:
                background_rgb = BACKGROUND_DARK_COLOR

            background_bgr = ImageProcessor.rgb_to_bgr(background_rgb)

            frame = ImageProcessor.create_gradient_background(
                height=frame.shape[0], 
                width=frame.shape[1], 
                base_color=background_bgr
            )
        
        if mesh_results.multi_face_landmarks:
                
            face_landmarks = mesh_results.multi_face_landmarks[0]
            
            # Convert landmarks to numpy array
            mesh_points = np.array([
                [int(point.x * img_w), int(point.y * img_h)]
                for point in face_landmarks.landmark
            ])
            
            # Only center mesh points when show_camera is False
            if not app.show_camera.get():
                window_center_x = img_w // 2
                window_center_y = img_h // 2
                mesh_center_x = np.mean(mesh_points[:, 0])
                mesh_center_y = np.mean(mesh_points[:, 1])
                offset_x = int(window_center_x - mesh_center_x)
                offset_y = int(window_center_y - mesh_center_y)
                mesh_points[:, 0] += offset_x
                mesh_points[:, 1] += offset_y

            # Process eyes
            (l_cx, l_cy), l_radius = cv.minEnclosingCircle(mesh_points[LEFT_EYE_IRIS])
            (r_cx, r_cy), r_radius = cv.minEnclosingCircle(mesh_points[RIGHT_EYE_IRIS])
            center_left = np.array([l_cx, l_cy], dtype=np.int32)
            center_right = np.array([r_cx, r_cy], dtype=np.int32)

            # Check for strabismus
            eye_distance = math.hypot(l_cx - r_cx, l_cy - r_cy)
            face_width = abs(mesh_points[234][0] - mesh_points[454][0])
            normalized_eye_distance = eye_distance / face_width if face_width > 0 else 0

            # Visualization

            # Draw mesh
            mesh_color = ImageProcessor.rgb_to_bgr(MESH_COLOR)
            for point in mesh_points:
                cv.circle(frame, tuple(point), 1, mesh_color, -1)

            # Draw eyes
            iris_color = ImageProcessor.rgb_to_bgr(MESH_LIGHT_COLOR)
            eye_inner_corner_color = ImageProcessor.rgb_to_bgr(MESH_LIGHT_COLOR)
            eye_outer_corner_color = ImageProcessor.rgb_to_bgr(MESH_LIGHT_COLOR)
            
            cv.circle(frame, center_left, int(l_radius), iris_color, 2, cv.LINE_AA)
            cv.circle(frame, center_right, int(r_radius), iris_color, 2, cv.LINE_AA)
            cv.circle(frame, mesh_points[LEFT_EYE_INNER_CORNER][0], 3, eye_inner_corner_color, -1, cv.LINE_AA)
            cv.circle(frame, mesh_points[LEFT_EYE_OUTER_CORNER][0], 3, eye_outer_corner_color, -1, cv.LINE_AA)
            cv.circle(frame, mesh_points[RIGHT_EYE_INNER_CORNER][0], 3, eye_inner_corner_color, -1, cv.LINE_AA)
            cv.circle(frame, mesh_points[RIGHT_EYE_OUTER_CORNER][0], 3, eye_outer_corner_color, -1, cv.LINE_AA)

            screen_text = app.format_eye_distance(normalized_eye_distance)
            screen_text_color = ImageProcessor.rgb_to_bgr(MESH_DARK_COLOR)

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
            'normalized_eye_distance': normalized_eye_distance,
            'mesh_points': mesh_points,
        }
