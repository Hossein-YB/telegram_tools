import asyncio
from inspect import iscoroutinefunction
from typing import Optional, Callable, Dict, List, Union

from pyrogram import Client
from pyrogram.filters import Filter

from .utils.config import config
from .utils.exceptions import ListenerTimeout, ListenerStopped
from .types import ListenerTypes, Identifier, Listener


class CustomClient(Client):
    listeners: Dict[ListenerTypes, List[Listener]]
    old__init__: Callable

    def __init__(self,
                 name: str,
                 api_id: Optional[Union[int, str]] = None,
                 api_hash: Optional[str] = None,
                 bot_token: Optional[str] = None,
                 phone_number: Optional[str] = None,
                 **kwargs):
        self.listeners = {listener_type: [] for listener_type in ListenerTypes}
        super().__init__(name=name, api_id=api_id, api_hash=api_hash,
                         bot_token=bot_token, phone_number=phone_number, **kwargs)

    async def listen(
            self,
            filters: Optional[Filter] = None,
            listener_type: ListenerTypes = ListenerTypes.MESSAGE,
            timeout: Optional[int] = None,
            unallowed_click_alert: bool = True,
            chat_id: Union[Union[int, str], List[Union[int, str]]] = None,
            user_id: Union[Union[int, str], List[Union[int, str]]] = None,
            message_id: Union[int, List[int]] = None,
            inline_message_id: Union[str, List[str]] = None,
    ):
        pattern = Identifier(
            from_user_id=user_id,
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
        )

        loop = asyncio.get_event_loop()
        future = loop.create_future()

        listener = Listener(
            future=future,
            filters=filters,
            unallowed_click_alert=unallowed_click_alert,
            identifier=pattern,
            listener_type=listener_type,
        )

        future.add_done_callback(lambda _future: self.remove_listener(listener))

        self.listeners[listener_type].append(listener)

        try:
            return await asyncio.wait_for(future, timeout)
        except asyncio.exceptions.TimeoutError:
            if callable(config.timeout_handler):
                if iscoroutinefunction(config.timeout_handler.__call__):
                    await config.timeout_handler(pattern, listener, timeout)
                else:
                    await self.loop.run_in_executor(
                        None, config.timeout_handler, pattern, listener, timeout
                    )
            elif config.throw_exceptions:
                raise ListenerTimeout(timeout)

    async def ask(
            self,
            chat_id: Union[Union[int, str], List[Union[int, str]]],
            text: str,
            filters: Optional[Filter] = None,
            listener_type: ListenerTypes = ListenerTypes.MESSAGE,
            timeout: Optional[int] = None,
            unallowed_click_alert: bool = True,
            user_id: Union[Union[int, str], List[Union[int, str]]] = None,
            message_id: Union[int, List[int]] = None,
            inline_message_id: Union[str, List[str]] = None,
            *args,
            **kwargs,
    ):
        sent_message = None
        if text.strip() != "":
            chat_to_ask = chat_id[0] if isinstance(chat_id, list) else chat_id
            sent_message = await self.send_message(chat_to_ask, text, *args, **kwargs)

        response = await self.listen(
            filters=filters,
            listener_type=listener_type,
            timeout=timeout,
            unallowed_click_alert=unallowed_click_alert,
            chat_id=chat_id,
            user_id=user_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
        )
        if response:
            response.sent_message = sent_message

        return response

    def remove_listener(self, listener: Listener):
        try:
            self.listeners[listener.listener_type].remove(listener)
        except ValueError:
            pass

    def get_listener_matching_with_data(
            self, data: Identifier, listener_type: ListenerTypes
    ) -> Optional[Listener]:
        matching = []
        for listener in self.listeners[listener_type]:
            if listener.identifier.matches(data):
                matching.append(listener)

        # in case of multiple matching listeners, the most specific should be returned
        def count_populated_attributes(listener_item: Listener):
            return listener_item.identifier.count_populated()

        return max(matching, key=count_populated_attributes, default=None)

    def get_listener_matching_with_identifier_pattern(
            self, pattern: Identifier, listener_type: ListenerTypes
    ) -> Optional[Listener]:
        matching = []
        for listener in self.listeners[listener_type]:
            if pattern.matches(listener.identifier):
                matching.append(listener)

        # in case of multiple matching listeners, the most specific should be returned

        def count_populated_attributes(listener_item: Listener):
            return listener_item.identifier.count_populated()

        return max(matching, key=count_populated_attributes, default=None)

    def get_many_listeners_matching_with_data(
            self,
            data: Identifier,
            listener_type: ListenerTypes,
    ) -> List[Listener]:
        listeners = []
        for listener in self.listeners[listener_type]:
            if listener.identifier.matches(data):
                listeners.append(listener)
        return listeners

    def get_many_listeners_matching_with_identifier_pattern(
            self,
            pattern: Identifier,
            listener_type: ListenerTypes,
    ) -> List[Listener]:
        listeners = []
        for listener in self.listeners[listener_type]:
            if pattern.matches(listener.identifier):
                listeners.append(listener)
        return listeners

    async def stop_listening(
            self,
            listener_type: ListenerTypes = ListenerTypes.MESSAGE,
            chat_id: Union[Union[int, str], List[Union[int, str]]] = None,
            user_id: Union[Union[int, str], List[Union[int, str]]] = None,
            message_id: Union[int, List[int]] = None,
            inline_message_id: Union[str, List[str]] = None,
    ):
        pattern = Identifier(
            from_user_id=user_id,
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
        )
        listeners = self.get_many_listeners_matching_with_identifier_pattern(pattern, listener_type)

        for listener in listeners:
            await self.stop_listener(listener)

    async def stop_listener(self, listener: Listener):
        self.remove_listener(listener)

        if listener.future.done():
            return

        if callable(config.stopped_handler):
            if iscoroutinefunction(config.stopped_handler.__call__):
                await config.stopped_handler(None, listener)
            else:
                await self.loop.run_in_executor(
                    None, config.stopped_handler, None, listener
                )
        elif config.throw_exceptions:
            listener.future.set_exception(ListenerStopped())

    def register_next_step_handler(
            self,
            callback: Callable,
            filters: Optional[Filter] = None,
            listener_type: ListenerTypes = ListenerTypes.MESSAGE,
            unallowed_click_alert: bool = True,
            chat_id: Union[Union[int, str], List[Union[int, str]]] = None,
            user_id: Union[Union[int, str], List[Union[int, str]]] = None,
            message_id: Union[int, List[int]] = None,
            inline_message_id: Union[str, List[str]] = None,
    ):
        pattern = Identifier(
            from_user_id=user_id,
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
        )

        listener = Listener(
            callback=callback,
            filters=filters,
            unallowed_click_alert=unallowed_click_alert,
            identifier=pattern,
            listener_type=listener_type,
        )

        self.listeners[listener_type].append(listener)
