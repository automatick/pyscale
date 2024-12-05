import cv2 as cv
import matplotlib.pyplot as plt
import tqdm

video = cv.VideoCapture('name.mp4')

frame_count = int(video.get(cv.CAP_PROP_FRAME_COUNT))
fps = video.get(cv.CAP_PROP_FPS)
frame_width = int(video.get(cv.CAP_PROP_FRAME_WIDTH))
frame_height = int(video.get(cv.CAP_PROP_FRAME_HEIGHT))

output_path = 'output.mp4'

fourcc = cv.VideoWriter_fourcc(*'mp4v')
out = cv.VideoWriter(output_path, fourcc, fps, (frame_width * 2, frame_height * 2))

progress_bar = tqdm.tqdm(total=frame_count)

while True:
    ret, frame = video.read()
    if not ret:
        break

    progress_bar.update(1)

    frame = cv.medianBlur(frame, 5)

    frame = cv.resize(frame, (frame_width * 2, frame_height * 2), interpolation=cv.INTER_LANCZOS4)

    out.write(frame)

    if cv.waitKey(1) & 0xFF == ord('q'):
        break

video.release()
out.release()

cv.destroyAllWindows()

progress_bar.close()
