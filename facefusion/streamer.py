import os
import subprocess
from concurrent.futures import Future
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from importlib import import_module
from typing import Any, Deque, Iterator, List, Optional, Tuple

import cv2
import numpy
from tqdm import tqdm

from facefusion import ffmpeg_builder, logger, state_manager, translator
from facefusion.audio import create_empty_audio_frame
from facefusion.content_analyser import analyse_stream
from facefusion.ffmpeg import open_ffmpeg
from facefusion.filesystem import is_directory
from facefusion.processors.core import get_processors_modules
from facefusion.types import Fps, StreamMode, VisionFrame
from facefusion.vision import extract_vision_mask, read_static_images

MAX_PENDING_STREAM_FRAMES = 2


def get_stream_workers() -> int:
	execution_thread_count = state_manager.get_item('execution_thread_count') or 1
	return max(1, min(execution_thread_count, MAX_PENDING_STREAM_FRAMES))


def collect_done_stream_frames(futures : List[Future[VisionFrame]]) -> List[VisionFrame]:
	done_vision_frames = []

	for future_done in [ future for future in futures if future.done() ]:
		done_vision_frames.append(future_done.result())
		futures.remove(future_done)
	return done_vision_frames


def multi_process_capture(camera_capture : cv2.VideoCapture, camera_fps : Fps) -> Iterator[VisionFrame]:
	capture_deque : Deque[VisionFrame] = deque()
	stream_workers = get_stream_workers()

	with tqdm(desc = translator.get('streaming'), unit = 'frame', disable = state_manager.get_item('log_level') in [ 'warn', 'error' ]) as progress:
		with ThreadPoolExecutor(max_workers = stream_workers) as executor:
			futures = []

			while camera_capture and camera_capture.isOpened():
				has_capture_vision_frame, capture_vision_frame = camera_capture.read()

				if has_capture_vision_frame and capture_vision_frame is not None and analyse_stream(capture_vision_frame, camera_fps):
					camera_capture.release()

				for done_vision_frame in collect_done_stream_frames(futures):
					capture_deque.append(done_vision_frame)

				while len(capture_deque) > 1:
					capture_deque.popleft()

				if len(futures) >= stream_workers:
					continue

				if has_capture_vision_frame and capture_vision_frame is not None:
					future = executor.submit(process_stream_frame, capture_vision_frame)
					futures.append(future)

				while capture_deque:
					progress.update()
					yield capture_deque.popleft()

		for done_vision_frame in collect_done_stream_frames(futures):
			capture_deque.append(done_vision_frame)

		while len(capture_deque) > 1:
			capture_deque.popleft()

		while capture_deque:
			progress.update()
			yield capture_deque.popleft()


def process_stream_frame(target_vision_frame : VisionFrame) -> VisionFrame:
	source_vision_frames = read_static_images(state_manager.get_item('source_paths'))
	source_audio_frame = create_empty_audio_frame()
	source_voice_frame = create_empty_audio_frame()
	temp_vision_frame = target_vision_frame.copy()
	temp_vision_mask = extract_vision_mask(temp_vision_frame)

	for processor_module in get_processors_modules(state_manager.get_item('processors')):
		logger.disable()
		if processor_module.pre_process('stream'):
			logger.enable()
			temp_vision_frame, temp_vision_mask = processor_module.process_frame(
			{
				'source_vision_frames': source_vision_frames,
				'source_audio_frame': source_audio_frame,
				'source_voice_frame': source_voice_frame,
				'target_vision_frame': target_vision_frame,
				'temp_vision_frame': temp_vision_frame,
				'temp_vision_mask': temp_vision_mask
			})
		logger.enable()

	return temp_vision_frame


def open_stream(stream_mode : StreamMode, stream_resolution : str, stream_fps : Fps) -> subprocess.Popen[bytes]:
	commands = ffmpeg_builder.chain(
		ffmpeg_builder.capture_video(),
		ffmpeg_builder.set_media_resolution(stream_resolution),
		ffmpeg_builder.set_input_fps(stream_fps)
	)

	if stream_mode == 'udp':
		commands.extend(ffmpeg_builder.set_input('-'))
		commands.extend(ffmpeg_builder.set_stream_mode('udp'))
		commands.extend(ffmpeg_builder.set_stream_quality(2000))
		commands.extend(ffmpeg_builder.set_output('udp://localhost:27000?pkt_size=1316'))

	if stream_mode == 'v4l2':
		device_directory_path = '/sys/devices/virtual/video4linux'
		commands.extend(ffmpeg_builder.set_input('-'))
		commands.extend(ffmpeg_builder.set_stream_mode('v4l2'))

		if is_directory(device_directory_path):
			device_names = os.listdir(device_directory_path)

			for device_name in device_names:
				device_path = '/dev/' + device_name
				commands.extend(ffmpeg_builder.set_output(device_path))

		else:
			logger.error(translator.get('stream_not_loaded').format(stream_mode = stream_mode), __name__)

	return open_ffmpeg(commands)


def open_virtual_camera(stream_resolution : str, stream_fps : Fps) -> Optional[Tuple[Any, bool]]:
	width, height = map(int, stream_resolution.split('x'))

	try:
		pyvirtualcam = import_module('pyvirtualcam')
	except ImportError:
		logger.error(translator.get('stream_dependency_not_loaded').format(stream_mode = 'virtualcam', dependency = 'pyvirtualcam'), __name__)
		return None

	camera_kwargs =\
	{
		'width': width,
		'height': height,
		'fps': stream_fps,
		'print_fps': False
	}
	can_send_bgr = hasattr(pyvirtualcam, 'PixelFormat') and hasattr(pyvirtualcam.PixelFormat, 'BGR')

	if can_send_bgr:
		camera_kwargs['fmt'] = pyvirtualcam.PixelFormat.BGR

	try:
		virtual_camera = pyvirtualcam.Camera(**camera_kwargs)
		return virtual_camera, can_send_bgr
	except Exception as exception:
		logger.error(translator.get('stream_not_loaded').format(stream_mode = 'virtualcam') + ' (' + str(exception) + ')', __name__)
		return None
