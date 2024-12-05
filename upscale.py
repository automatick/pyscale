import cv2 as cv
import matplotlib.pyplot as plt
import tqdm
import sys

if len(sys.argv) < 2:
    print("Provide video name as argument in command line!")
    sys.exit(1)

video = cv.VideoCapture(sys.argv[1])
frame_count = int(video.get(cv.CAP_PROP_FRAME_COUNT))
fps = video.get(cv.CAP_PROP_FPS)
frame_width = int(video.get(cv.CAP_PROP_FRAME_WIDTH))
frame_height = int(video.get(cv.CAP_PROP_FRAME_HEIGHT))

output_path = 'output.mp4'
fourcc = cv.VideoWriter_fourcc(*'mp4v')
out = cv.VideoWriter(output_path, fourcc, fps, (frame_width * 2, frame_height * 2))
progress_bar = tqdm.tqdm(total=frame_count)

plt.ion()
fig, ax = plt.subplots()

while True:
    ret, frame = video.read()
    if not ret:
        break
    progress_bar.update(1)
    frame = cv.resize(frame, (frame_width * 2, frame_height * 2), interpolation=cv.INTER_LANCZOS4)
    frame = cv.bilateralFilter(frame, 6, 75, 75)
    frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    
    ax.imshow(frame_rgb)
    ax.axis('off')
    plt.draw()
    plt.pause(1)
    
    key = cv.waitKey(0) & 0xFF  
    if key == ord('n'):
        continue
    elif key == ord('q'):
        break

    out.write(frame)

video.release()
out.release()
cv.destroyAllWindows()
progress_bar.close()
plt.ioff()
plt.show()
