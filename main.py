import numpy as np
import cv2 as cv
from collections import Counter
import os

def get_dominant_color(image, mask):
    """Extract the dominant color from a masked region"""
    # Apply mask to get only the circular region
    masked_region = cv.bitwise_and(image, image, mask=mask)
    
    # Get non-zero pixels (inside the circle)
    pixels = masked_region[mask > 0]
    
    if len(pixels) == 0:
        return None
    
    # Convert to HSV for better color detection
    pixels_hsv = cv.cvtColor(pixels.reshape(-1, 1, 3), cv.COLOR_BGR2HSV)
    
    # Get the median HSV values
    h_median = np.median(pixels_hsv[:, 0, 0])
    s_median = np.median(pixels_hsv[:, 0, 1])
    v_median = np.median(pixels_hsv[:, 0, 2])
    
    return classify_rubiks_color(h_median, s_median, v_median)

def classify_rubiks_color(h, s, v):
    print("h: ", h)
    """Classify HSV values into Rubik's cube colors"""
    # Adjust these ranges based on your lighting conditions
    if v < 50:  # Very dark
        return "Black"
    elif s < 50:  # Low saturation
        if v > 200:
            return "White"
        else:
            return "Gray"
    elif 160 <= h and h <= 180:  # Red range (narrowed)
        return "Red"
    elif 0 <= h and h <= 8:  # Orange range (widened)
        return "Orange"
    elif 20 <= h and h <= 35:  # Yellow range (adjusted to avoid overlap)
        return "Yellow"
    elif 35 <= h and h <= 85:  # Green range
        return "Green"
    elif 85 <= h and h <= 130:  # Blue range
        return "Blue"
    else:
        return "Purple"

cap = cv.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
    exit()

# Define circle positions for 3x3 grid
circle_positions = [
    (150, 150), (250, 150), (350, 150),
    (150, 250), (250, 250), (350, 250),
    (150, 350), (250, 350), (350, 350)
]

nbr_faces_captured = 0
while True:
    ret, frame = cap.read()
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break
    
    # Draw rectangle around detection area
    cv.rectangle(frame, (100, 100), (400, 400), (255, 0, 255), 3)
    
    # Detect colors in each position
    detected_colors = []
    
    for i, (x, y) in enumerate(circle_positions):
        # Create individual mask for each circle
        individual_mask = np.zeros(frame.shape[:2], dtype="uint8")
        cv.circle(individual_mask, (x, y), 50, 255, -1)
        
        # Detect color in this region
        color = get_dominant_color(frame, individual_mask)
        detected_colors.append(color)
        
        # Draw circle and label
        cv.circle(frame, (x, y), 50, (0, 255, 0), 2)
        if color:
            cv.putText(frame, color, (x-30, y-60), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    
    # Print the 3x3 grid of colors
    if all(color is not None for color in detected_colors):
        grid = np.array(detected_colors).reshape(3, 3)
        print("Detected Rubik's cube face:")
        for row in grid:
            print(" ".join(f"{color:>6}" for color in row))
        print("-" * 30)

    cv.putText(frame, "Press SPACE to take a look.", 
               (50, 50), cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv.imshow('frame', frame)
    
    key = cv.waitKey(1)  # Une seule fois
    if key == ord('q'):
        if nbr_faces_captured != 6:
            if os.path.exists("detected_colors.txt"): os.remove("detected_colors.txt")
            print("Incomplete capture. Exiting and deleting detected_colors.txt")
        break
    elif key == ord(' '):  # Utiliser elif au lieu de if
        print("Pausing for user to see detected colors. Press ENTER to continue.")
        # Create a copy of the frame to display the message
        frame_with_text = frame.copy()
        cv.putText(frame_with_text, "Press ENTER to go to the next face.", 
                   (50, 50), cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv.imshow('frame', frame_with_text)
        
        # Wait for Enter key (key code 13)
        while True:
            key = cv.waitKey(0)
            if key == 13 or key == ord('\r'):  # Enter key
                # save the color in a file
                with open("detected_colors.txt", "a") as f:
                    f.write(f"{detected_colors[4]} face: {detected_colors}\n")
                nbr_faces_captured += 1
                if nbr_faces_captured == 6:
                    print("Captured all 6 faces. Exiting.")
                    cap.release()
                    cv.destroyAllWindows()
                    exit()
                break
            elif key == ord(' '):
                # If space is pressed again, just continue
                break
            elif key == ord('q'):
                cap.release()
                cv.destroyAllWindows()
                if nbr_faces_captured != 6:
                    if os.path.exists("detected_colors.txt"): os.remove("detected_colors.txt")
                    print("Incomplete capture. Exiting and deleting detected_colors.txt")
                exit()

cap.release()
cv.destroyAllWindows()