# ObstacleAvoidance-mBot
**ETF – Robot Vision Project**

An obstacle avoidance system for the mBot robot using computer vision and homography. The system enables the robot to autonomously detect and avoid obstacles in real-time using color detection (HSV) and feature-based recognition (SIFT).

## Team
- **Ajla Herak** – aherak1@etf.unsa.ba  
- **Adelisa Hasic** – ahasic2@etf.unsa.ba  
Department of Automation and Electronics, Faculty of Electrical Engineering, Sarajevo, Bosnia and Herzegovina

## Overview
- **Robot Platform:** mBot (Arduino-based, Makeblock)  
- **Key Features:**  
  - Real-time obstacle detection and avoidance  
  - Homography for mapping camera feed to real-world coordinates  
  - Color-based decision making (HSV)  
  - SIFT for feature detection in low-detail environments  
  - Mobile app (Flutter) for BLE-based robot control

## Architecture
1. **Data Capture:** iPhone camera mounted on mBot captures frames  
2. **Processing:** Images analyzed with OpenCV (SIFT, HSV, homography)  
3. **Decision Making:** Robot determines movement based on obstacle position and color  
4. **Execution:** Commands sent via Bluetooth to mBot for real-time navigation

## Highlights
- Works under varying lighting conditions  
- Integrates computer vision with BLE-controlled mobile app  
- Tested with different colored obstacles and sequences

## Future Improvements
- Integrate YOLO or depth sensors for enhanced obstacle recognition  
- Add LiDAR/ultrasonic sensors for better distance measurement  
- Optimize image processing and communication latency

**Keywords:** obstacle avoidance, mBot, computer vision, OpenCV, homography, SIFT, HSV, BLE
