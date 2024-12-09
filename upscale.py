
import cv2 as cv
import tqdm
import argparse
import sys
import threading
import queue

def parse_arguments():
    parser = argparse.ArgumentParser(description="Обработка видео с использованием фильтра и ресайза.")
    
    parser.add_argument(
        "video", 
        type=str, 
        help="Путь к входному видео"
    )
    parser.add_argument(
        "-o", "--output", 
        type=str, 
        default="output.mp4", 
        help="Путь для сохранения выходного видео (по умолчанию: output.mp4)"
    )
    parser.add_argument(
        "-l", "--level", 
        type=int, 
        default=6, 
        help="Уровень фильтрации для bilateralFilter (по умолчанию: 6)"
    )
    parser.add_argument(
        "-s", "--scale", 
        type=float, 
        default=2.0, 
        help="Множитель увеличения размера кадра (по умолчанию: 2.0)"
    )
    parser.add_argument(
        "--sigma-color", 
        type=float, 
        default=75.0, 
        help="Параметр sigmaColor для bilateralFilter (по умолчанию: 75.0)"
    )
    parser.add_argument(
        "--sigma-space", 
        type=float, 
        default=75.0, 
        help="Параметр sigmaSpace для bilateralFilter (по умолчанию: 75.0)"
    )
    
    return parser.parse_args()

def frame_processor(input_queue, output_queue, args, scaled_size):
    while True:
        item = input_queue.get()
        if item is None:
            input_queue.task_done()
            break
        frame_id, frame = item
        try:
            frame = cv.resize(frame, scaled_size, interpolation=cv.INTER_CUBIC)
            frame = cv.bilateralFilter(frame, args.level, args.sigma_color, args.sigma_space)
            output_queue.put((frame_id, frame))
        except Exception as e:
            print(f"Ошибка обработки кадра {frame_id}: {e}")
        finally:
            input_queue.task_done()

def main():
    args = parse_arguments()
    
    video = cv.VideoCapture(args.video)
    if not video.isOpened():
        print(f"Не удалось открыть видео: {args.video}")
        sys.exit(1)
    
    frame_count = int(video.get(cv.CAP_PROP_FRAME_COUNT))
    fps = video.get(cv.CAP_PROP_FPS)
    frame_width = int(video.get(cv.CAP_PROP_FRAME_WIDTH))
    frame_height = int(video.get(cv.CAP_PROP_FRAME_HEIGHT))
    
    scaled_width = int(frame_width * args.scale)
    scaled_height = int(frame_height * args.scale)
    scaled_size = (scaled_width, scaled_height)
    
    output_path = args.output
    fourcc = cv.VideoWriter_fourcc(*'mp4v')
    out = cv.VideoWriter(output_path, fourcc, fps, scaled_size)

    input_queue = queue.Queue(maxsize=100)
    output_queue = queue.Queue(maxsize=100)
    num_threads = 4

    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=frame_processor, args=(input_queue, output_queue, args, scaled_size))
        t.start()
        threads.append(t)

    progress_bar = tqdm.tqdm(total=frame_count)
    next_frame_id = 0
    processed_frames = {}
    write_frame_id = 0

    try:
        while True:
            ret, frame = video.read()
            if not ret:
                break

            input_queue.put((next_frame_id, frame))
            next_frame_id += 1

            while write_frame_id in processed_frames:
                out.write(processed_frames.pop(write_frame_id))
                write_frame_id += 1
                progress_bar.update(1)

            while not output_queue.empty():
                frame_id, processed_frame = output_queue.get()
                processed_frames[frame_id] = processed_frame
                output_queue.task_done()

        input_queue.join()

        for _ in threads:
            input_queue.put(None)
        for t in threads:
            t.join()

        while not output_queue.empty():
            frame_id, processed_frame = output_queue.get()
            processed_frames[frame_id] = processed_frame
            output_queue.task_done()

        for frame_id in sorted(processed_frames):
            out.write(processed_frames[frame_id])
            progress_bar.update(1)

    finally:
        video.release()
        out.release()
        cv.destroyAllWindows()
        progress_bar.close()

if __name__ == "__main__":
    main()
