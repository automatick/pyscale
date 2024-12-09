# Video Frame Upscaler and Processor

This **Python** script allows you to process a video by applying filters to each frame and displaying the frames one by one for manual viewing. It also saves the processed video to an output file.
Requirements

Before running the script, ensure that you have the following libraries installed:

    opencv-python (cv2)
    matplotlib
    tqdm

You can install them using pip:
``` bash
pip install -r requirements.txt
```
How to Run:
```py
python upscale.py sample.mp4
```

Make sure the video file you want to process is available.
Run the script from the command line and provide the video file path as an argument.

# Example:

#*Before image:*

![image](https://github.com/user-attachments/assets/d7c41072-cee0-4dcc-afae-18879282eaa1)


#*After image:*

![image](https://github.com/user-attachments/assets/c3ee72d6-5ad6-4eae-9954-63324fb009cc)



Where video_name.mp4 is the name of the video you want to process.
How it Works:
    Loading the Video: The script uses OpenCV to load the video specified as a command-line argument.
    Frame Processing: Each frame of the video is:
        Resized to double the original dimensions.
        Processed with a bilateral filter to reduce noise while preserving edges.
    Displaying Frames: The frames are displayed using matplotlib in an interactive mode. After each frame is displayed:
        It waits for the user to press n to move to the next frame.
        It waits for the user to press q to quit the script.
    Saving Processed Video: After processing each frame, the frame is written to an output video file (output.mp4).
    Progress Bar: A progress bar is displayed in the terminal showing the processing progress.
