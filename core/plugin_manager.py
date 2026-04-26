"""
Plugin Manager for Loading and Managing Plugins
"""

import importlib
import os
from typing import Dict, Any, List
from abc import ABC, abstractmethod


class Plugin(ABC):
    @abstractmethod
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass


class PluginManager:
    def __init__(self, plugin_dir: str = "plugins"):
        self.plugin_dir = plugin_dir
        self.plugins: Dict[str, Plugin] = {}

    def load_plugins(self):
        if not os.path.exists(self.plugin_dir):
            return
        for file in os.listdir(self.plugin_dir):
            if file.endswith(".py") and not file.startswith("__"):
                module_name = file[:-3]
                try:
                    module = importlib.import_module(f"plugins.{module_name}")
                    for attr in dir(module):
                        obj = getattr(module, attr)
                        if isinstance(obj, type) and issubclass(obj, Plugin) and obj != Plugin:
                            plugin_instance = obj()
                            self.plugins[plugin_instance.get_name()] = plugin_instance
                except Exception as e:
                    print(f"Failed to load plugin {module_name}: {e}")

    def get_plugin(self, name: str) -> Plugin:
        return self.plugins.get(name)

    def list_plugins(self) -> List[str]:
        return list(self.plugins.keys())

    def process_with_plugin(self, plugin_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        plugin = self.get_plugin(plugin_name)
        if plugin:
            return plugin.process(data)
        return data