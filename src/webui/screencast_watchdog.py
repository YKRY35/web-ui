import base64
from typing import ClassVar, Callable, Awaitable

from bubus import BaseEvent
from pydantic import PrivateAttr

from browser_use.browser.events import AgentFocusChangedEvent, BrowserConnectedEvent, BrowserStopEvent
from browser_use.browser.watchdog_base import BaseWatchdog
from browser_use.utils import create_task_with_error_handling

try:
	from cdp_use.cdp.page.events import ScreencastFrameEvent
except ImportError:
	ScreencastFrameEvent = dict


class ScreencastWatchdog(BaseWatchdog):
	"""
	Watchdog that streams browser frames to connected WebSocket clients via CDP screencast.
	Mirrors the pattern of RecordingWatchdog but pushes raw JPEG bytes instead of writing video.
	"""

	LISTENS_TO: ClassVar[list[type[BaseEvent]]] = [
		BrowserConnectedEvent,
		BrowserStopEvent,
		AgentFocusChangedEvent,
	]
	EMITS: ClassVar[list[type[BaseEvent]]] = []

	_broadcast_frame: Callable[[bytes], Awaitable[None]] | None = PrivateAttr(default=None)
	_current_session_id: str | None = PrivateAttr(default=None)

	async def on_BrowserConnectedEvent(self, event: BrowserConnectedEvent) -> None:
		self.browser_session.cdp_client.register.Page.screencastFrame(self._on_screencast_frame)
		await self._start_screencast()

	async def on_AgentFocusChangedEvent(self, event: AgentFocusChangedEvent) -> None:
		await self._start_screencast()

	async def on_BrowserStopEvent(self, event: BrowserStopEvent) -> None:
		await self._stop_screencast()
		self._current_session_id = None

	async def _start_screencast(self) -> None:
		try:
			cdp_session = await self.browser_session.get_or_create_cdp_session()
			if self._current_session_id == cdp_session.session_id:
				return
			if self._current_session_id:
				try:
					await self.browser_session.cdp_client.send.Page.stopScreencast(
						session_id=self._current_session_id
					)
				except Exception:
					pass
			self._current_session_id = cdp_session.session_id
			profile = self.browser_session.browser_profile
			w = getattr(profile, 'window_size', {}).get('width', 1280) if isinstance(getattr(profile, 'window_size', None), dict) else 1280
			h = getattr(profile, 'window_size', {}).get('height', 1100) if isinstance(getattr(profile, 'window_size', None), dict) else 1100
			await cdp_session.cdp_client.send.Page.startScreencast(
				params={
					'format': 'jpeg',
					'quality': 70,
					'maxWidth': w,
					'maxHeight': h,
					'everyNthFrame': 1,
				},
				session_id=cdp_session.session_id,
			)
			self.logger.info(f'ScreencastWatchdog: started screencast on session {cdp_session.session_id}')
		except Exception as e:
			self.logger.error(f'ScreencastWatchdog: failed to start screencast: {e}')
			self._current_session_id = None

	async def _stop_screencast(self) -> None:
		if self._current_session_id:
			try:
				await self.browser_session.cdp_client.send.Page.stopScreencast(
					session_id=self._current_session_id
				)
			except Exception:
				pass

	def _on_screencast_frame(self, event: ScreencastFrameEvent, session_id: str | None) -> None:
		if self._current_session_id and session_id != self._current_session_id:
			return
		raw_bytes = base64.b64decode(event['data'])
		create_task_with_error_handling(
			self._broadcast_and_ack(raw_bytes, event, session_id),
			name='screencast_broadcast_ack',
			logger_instance=self.logger,
			suppress_exceptions=True,
		)

	async def _broadcast_and_ack(
		self, raw_bytes: bytes, event: ScreencastFrameEvent, session_id: str | None
	) -> None:
		if self._broadcast_frame:
			await self._broadcast_frame(raw_bytes)
		try:
			await self.browser_session.cdp_client.send.Page.screencastFrameAck(
				params={'sessionId': event['sessionId']},
				session_id=session_id,
			)
		except Exception as e:
			self.logger.debug(f'ScreencastWatchdog: ack failed: {e}')
