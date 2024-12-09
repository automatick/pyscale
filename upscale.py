import cv2 as cv
import tqdm
import argparse
import sys
import threading
import queue
import subprocess
import os

def parse_arguments():
    parser = argparse.ArgumentParser(description="Обработка видео с использованием фильтра и ресайза.")
    
    parser.add_argument(
        "video", 
        type=str, 
        help="Путь к входному видео"
    )
    parser.add_argument(
        "--ocl", action="store_true",
        help="Включение обработки с помощью OpenCL (по умолчанию: False)"
    )
    parser.add_argument(
        "--cuda", action="store_true",
        help="Включение обработки с помощью CUDA (по умолчанию: False)"
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

def extract_audio(input_video, audio_file):
    try:
        subprocess.run([
            "ffmpeg", "-i", input_video, "-q:a", "0", "-map", "a", audio_file
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Аудио успешно извлечено.")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка извлечения аудио: {e}")
        sys.exit(1)

def merge_audio_video(processed_video, audio_file, output_file):
    try:
        subprocess.run([
            "ffmpeg", "-i", processed_video, "-i", audio_file, "-c:v", "copy", "-c:a", "aac", output_file
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Видео и аудио успешно объединены.")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка объединения видео и аудио: {e}")
        sys.exit(1)

def cleanup_temp_files(*files):
    for file in files:
        try:
            os.remove(file)
            print(f"Удалён временный файл: {file}")
        except OSError as e:
            print(f"Ошибка удаления файла {file}: {e}")

def frame_processor(input_queue, output_queue, args, scaled_size, use_cuda, use_ocl):
    while True:
        item = input_queue.get()
        if item is None:
            input_queue.task_done()
            break
        frame_id, frame = item
        try:
            if use_cuda:
                gpu_frame = cv.cuda_GpuMat()
                gpu_frame.upload(frame)
                gpu_frame = cv.cuda.bilateralFilter(gpu_frame, args.level, args.sigma_color, args.sigma_space)
                frame = gpu_frame.download()
            elif use_ocl:
                frame = cv.bilateralFilter(frame, args.level, args.sigma_color, args.sigma_space)
            else:
                frame = cv.bilateralFilter(frame, args.level, args.sigma_color, args.sigma_space)

            frame = cv.resize(frame, scaled_size, interpolation=cv.INTER_LANCZOS4)
            output_queue.put((frame_id, frame))
        except Exception as e:
            print(f"Ошибка обработки кадра {frame_id}: {e}")
        finally:
            input_queue.task_done()

def main():
    args = parse_arguments()
    
    use_cuda = args.cuda
    use_ocl = args.ocl

    if use_ocl:
        cv.ocl.setUseOpenCL(True)
        print("OpenCL включён.")

    if use_cuda and not cv.cuda.getCudaEnabledDeviceCount():
        print("CUDA недоступен на этом устройстве.")
        sys.exit(1)
    elif use_cuda:
        print("CUDA включён.")

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
    temp_video_path = "temp_video.mp4"
    audio_file = "temp_audio.aac"
    final_output_path = "final_" + output_path
    
    extract_audio(args.video, audio_file)

    fourcc = cv.VideoWriter_fourcc(*'mp4v')
    out = cv.VideoWriter(temp_video_path, fourcc, fps, scaled_size)

    input_queue = queue.Queue(maxsize=100)
    output_queue = queue.Queue(maxsize=100)
    num_threads = 4

    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=frame_processor, args=(input_queue, output_queue, args, scaled_size, use_cuda, use_ocl))
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

    merge_audio_video(temp_video_path, audio_file, final_output_path)

    cleanup_temp_files(temp_video_path, audio_file)

if __name__ == "__main__":
    main()
