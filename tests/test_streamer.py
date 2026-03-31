from concurrent.futures import Future
from unittest.mock import patch

import numpy

from facefusion import state_manager
from facefusion.streamer import collect_done_stream_frames, get_stream_workers, open_virtual_camera
from facefusion.uis import choices as uis_choices


def create_done_future(fill_value : int) -> Future:
	future = Future()
	future.set_result(numpy.full((1, 1, 3), fill_value, dtype = numpy.uint8))
	return future


def test_get_stream_workers() -> None:
	state_manager.init_item('execution_thread_count', 1)
	assert get_stream_workers() == 1

	state_manager.init_item('execution_thread_count', 8)
	assert get_stream_workers() == 2


def test_collect_done_stream_frames() -> None:
	pending_future = Future()
	futures = [ create_done_future(1), pending_future, create_done_future(2) ]

	done_vision_frames = collect_done_stream_frames(futures)

	assert [ int(done_vision_frame[0, 0, 0]) for done_vision_frame in done_vision_frames ] == [ 1, 2 ]
	assert futures == [ pending_future ]


def test_open_virtual_camera_uses_bgr_pixel_format() -> None:
	class FakePixelFormat:
		BGR = 'bgr'

	class FakeCamera:
		def __init__(self, **kwargs) -> None:
			self.kwargs = kwargs

	fake_module = type('FakeModule',
	(),
	{
		'Camera': FakeCamera,
		'PixelFormat': FakePixelFormat
	})

	with patch('facefusion.streamer.import_module', return_value = fake_module):
		virtual_camera, can_send_bgr = open_virtual_camera('640x480', 30)

	assert can_send_bgr is True
	assert virtual_camera.kwargs ==\
	{
		'width': 640,
		'height': 480,
		'fps': 30,
		'print_fps': False,
		'fmt': 'bgr'
	}


def test_open_virtual_camera_without_bgr_pixel_format() -> None:
	class FakeCamera:
		def __init__(self, **kwargs) -> None:
			self.kwargs = kwargs

	fake_module = type('FakeModule',
	(),
	{
		'Camera': FakeCamera
	})

	with patch('facefusion.streamer.import_module', return_value = fake_module):
		virtual_camera, can_send_bgr = open_virtual_camera('640x480', 30)

	assert can_send_bgr is False
	assert virtual_camera.kwargs ==\
	{
		'width': 640,
		'height': 480,
		'fps': 30,
		'print_fps': False
	}


def test_open_virtual_camera_without_dependency() -> None:
	with patch('facefusion.streamer.import_module', side_effect = ImportError()):
		assert open_virtual_camera('640x480', 30) is None


def test_webcam_modes_include_virtualcam() -> None:
	assert 'virtualcam' in uis_choices.webcam_modes
