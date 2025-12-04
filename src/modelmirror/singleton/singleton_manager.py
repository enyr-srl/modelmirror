import asyncio
import threading
from typing import Any

from modelmirror.parser.code_link_parser import CodeLinkParser
from modelmirror.parser.model_link_parser import ModelLinkParser
from modelmirror.parser.secret_parser import SecretParser


class MirrorSingletons:
    __instances: dict[str, Any] = {}
    __lock = threading.Lock()
    __instance_locks: dict[str, threading.Lock] = {}

    @classmethod
    def get_or_create_instance(
        cls,
        mirror_class: type,
        package_name: str,
        code_link_parser: CodeLinkParser,
        model_link_parser: ModelLinkParser,
        check_circular_types: bool,
        secret_parser: SecretParser,
    ) -> Any:
        """Get existing singleton or create new one (automatically per thread/task context)."""
        instance_key = cls.__create_instance_key(
            package_name, code_link_parser, model_link_parser, check_circular_types, secret_parser
        )

        # Get or create a lock for this specific instance key
        with cls.__lock:
            if instance_key not in cls.__instance_locks:
                cls.__instance_locks[instance_key] = threading.Lock()
            instance_lock = cls.__instance_locks[instance_key]

        # Use the specific lock for this instance
        with instance_lock:
            if instance_key not in cls.__instances:
                instance: Any = object.__new__(mirror_class)
                cls.__instances[instance_key] = instance

            return cls.__instances[instance_key]

    @classmethod
    def __create_instance_key(
        cls,
        package_name: str,
        code_link_parser: CodeLinkParser,
        model_link_parser: ModelLinkParser,
        check_circular_types: bool,
        secret_parser: SecretParser,
    ) -> str:
        """Create unique key for Mirror instance including thread/task context."""
        thread_id = threading.get_ident()
        key = f"{package_name}:{id(code_link_parser)}:{id(model_link_parser)}:{check_circular_types}:{secret_parser}:{thread_id}"
        try:
            current_task = asyncio.current_task()
            if current_task:
                key += f":{id(current_task)}"
        except RuntimeError:
            pass

        return key
