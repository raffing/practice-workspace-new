from pathlib import Path
from typing import List, Dict, Any
from PySide6.QtCore import Qt, QAbstractListModel, QModelIndex
from app.constants import FILE_ICONS

class FileSystemNavigator:
    def __init__(self, root_path: Path, show_files: bool = True, show_directories: bool = True, start_path: Path = None):
        self.root_path = root_path
        self.current_path = start_path or root_path
        self.show_files = show_files
        self.show_directories = show_directories
        
    def get_items(self) -> List[Dict[str, Any]]:
        items = []
        
        if self.current_path != self.root_path:
            items.append({
                'name': '📁 ..', 'type': 'parent',
                'path': self.current_path.parent, 'is_dir': True,
                'display_name': '..'
            })
        
        try:
            all_items = sorted(
                self.current_path.iterdir(),
                key=lambda x: (not x.is_dir(), x.name.lower())
            )
            
            for item in all_items:
                if item.name.startswith('.'):
                    continue
                
                if item.is_dir() and self.show_directories:
                    items.append({
                        'name': f'📁 {item.name}', 'type': 'folder',
                        'path': item, 'is_dir': True, 'display_name': item.name
                    })
                elif item.is_file() and self.show_files:
                    icon = FILE_ICONS.get(item.suffix.lower(), '📎')
                    items.append({
                        'name': f'{icon} {item.name}', 'type': 'file',
                        'path': item, 'is_dir': False, 'display_name': item.name
                    })
        except PermissionError:
            pass
        
        return items
    
    def navigate_to(self, path: Path):
        self.current_path = path
    
    def get_relative_path(self) -> str:
        try:
            rel = self.current_path.relative_to(self.root_path)
            return str(rel) if str(rel) != '.' else 'Workspace root'
        except ValueError:
            return self.current_path.name

class FileSystemListModel(QAbstractListModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []
        
    def rowCount(self, parent=QModelIndex()):
        return len(self._items)
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._items):
            return None
        item = self._items[index.row()]
        if role == Qt.DisplayRole:
            return item.get('name', '')
        elif role == Qt.UserRole:
            return item
        return None
    
    def set_items(self, items):
        self.beginResetModel()
        self._items = items
        self.endResetModel()
    
    def get_item(self, index):
        if index.isValid() and index.row() < len(self._items):
            return self._items[index.row()]
        return None