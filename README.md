# Inventory Mapper

A cross-platform desktop application for creating interactive floor plans with spatial inventory tracking, Google Sheets integration, and reseller marketplace features.

## Features

### Phase 1: Core Infrastructure ✅ Complete
- [x] SQLite database with full-text search
- [x] Interactive canvas with pan and zoom
- [x] Grid display and snapping
- [x] Basic application window with menus
- [x] Configuration management

### Phase 2: Vector Drawing Tools ✅ Complete
- [x] Rectangle, line, and polygon drawing tools
- [x] Layer management panel (create, rename, delete, show/hide)
- [x] Mouse-driven drawing interface
- [x] Save/load floor plans to database
- [x] Shape serialization and persistence
- [x] Drawing toolbar with tool selection

### Phase 3: Inventory Management ✅ Complete
- [x] Full CRUD operations for inventory items
- [x] Inventory panel with searchable table view
- [x] Item editor dialog for add/edit operations
- [x] FTS5 full-text search across inventory
- [x] Category management system
- [x] CSV import for bulk inventory loading
- [x] Stock status indicators (in stock, low stock, out of stock)
- [x] Color-coded status display

### Phase 4: Spatial Inventory Placement ✅ Complete
- [x] Drag-and-drop inventory items from panel to floor plan
- [x] Color-coded inventory markers (green: in stock, orange: low, red: out)
- [x] Persistent placement storage in database
- [x] Automatic loading of markers when opening floor plans
- [x] Search-to-highlight: select item in panel to highlight and center on map
- [x] Grid snapping for precise marker placement
- [x] Item tooltips showing details on hover
- [x] Double-click markers to edit item (via scene signal)

### Upcoming Phases
- **Phase 5**: Google Sheets two-way synchronization
- **Phase 6**: Export/import (JSON, CSV, PNG, PDF)
- **Phase 7**: Cross-platform packaging
- **Phase 8**: Reseller features (eBay comp data, product images)

## Requirements

- Python 3.9 or higher
- macOS, Windows, or Linux

## Installation

### 1. Clone or Download the Project

```bash
cd ~/inventory_mapper  # Navigate to the project directory
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
```

### 3. Activate Virtual Environment

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```cmd
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Run the Application

```bash
python main.py
```

### First Launch

On first launch, the application will:
- Create a database at `~/Library/Application Support/InventoryMapper/inventory_mapper.db` (macOS)
- Display an empty canvas ready for floor plan creation

### Current Functionality (Phases 1-4)

- **Floor Plan Management:**
  - **Create:** Ctrl+N to create new floor plan with custom name
  - **Open:** Ctrl+O to load existing floor plans
  - **Save:** Ctrl+S to persist floor plan and all shapes to database
  - **Layer Management:** Create, rename, delete, show/hide layers

- **Drawing Tools:** (Left toolbar)
  - **Select Tool:** Move and manipulate existing shapes
  - **Rectangle Tool:** Click-drag-release to draw rectangles
  - **Line Tool:** Click-drag-release to draw lines
  - **Polygon Tool:** Click to add vertices, double-click to finish
  - **Grid Snapping:** Automatically snap shapes to grid for precision

- **Canvas Navigation:**
  - **Pan:** Middle mouse button + drag OR Spacebar + left mouse drag
  - **Zoom:** Ctrl + Mouse wheel OR View menu → Zoom In/Out
  - **Zoom to Fit:** Ctrl+0 or View menu → Zoom to Fit

- **Inventory Management:** (Right panel - Inventory tab)
  - **Add Items:** Click "Add Item" button for item editor dialog
  - **Edit Items:** Double-click item or select and click "Edit Item"
  - **Delete Items:** Select item and click "Delete Item"
  - **Search:** Real-time full-text search across all inventory
  - **Import CSV:** Tools menu → Import Inventory CSV for bulk loading
  - **Stock Status:** Color-coded indicators (Green=In Stock, Orange=Low, Red=Out)

- **Spatial Inventory Placement:** (Phase 4 - NEW!)
  - **Drag to Place:** Drag items from inventory panel onto floor plan canvas
  - **Visual Markers:** Color-coded circular markers show item locations
  - **Search & Find:** Click item in inventory panel to highlight and center on map
  - **Persistent Storage:** Marker positions saved and restored with floor plans
  - **Item Details:** Hover over markers for tooltips with item info
  - **Grid Snapping:** Markers snap to grid for organized placement

- **Keyboard Shortcuts:**
  - `Ctrl+N`: New floor plan
  - `Ctrl+O`: Open floor plan
  - `Ctrl+S`: Save floor plan
  - `Ctrl+=`: Zoom in
  - `Ctrl+-`: Zoom out
  - `Ctrl+0`: Zoom to fit
  - `Ctrl+F`: Find inventory (focus search)
  - `Delete`: Delete selected shapes
  - `Ctrl+Q`: Exit application

## Project Structure

```
inventory_mapper/
├── main.py                          # Application entry point
├── requirements.txt                 # Python dependencies
├── README.md                       # This file
│
├── app/
│   ├── config.py                   # Settings management
│   ├── constants.py                # Application constants
│   │
│   ├── models/                     # Data models
│   │   ├── database.py             # SQLite database manager
│   │   ├── inventory_item.py       # Inventory model (Phase 3)
│   │   ├── floor_plan.py          # Floor plan model (Phase 2)
│   │   └── shape.py               # Vector shape models (Phase 2)
│   │
│   ├── ui/                         # User interface
│   │   ├── main_window.py         # Main application window
│   │   ├── widgets/
│   │   │   ├── canvas_scene.py    # Drawing canvas (QGraphicsScene)
│   │   │   ├── canvas_view.py     # Canvas view with pan/zoom
│   │   │   └── ...                # Other widgets (future)
│   │   │
│   │   ├── graphics_items/        # Custom drawing items (Phase 2)
│   │   └── dialogs/               # Dialog windows (future)
│   │
│   ├── controllers/               # Business logic (future)
│   ├── services/                  # External services (future)
│   └── utils/                     # Utilities (future)
│
├── resources/                     # Icons, styles, templates
├── data/                          # User data (databases, exports)
└── tests/                         # Unit tests
```

## Database Schema

The application uses SQLite with the following tables:

- **floor_plans**: Floor plan metadata
- **layers**: Organize shapes into layers
- **shapes**: Vector graphics elements
- **categories**: Inventory categories
- **inventory_items**: Item details (SKU, name, quantity, etc.)
- **inventory_placements**: Item positions on floor plans
- **sync_state**: Google Sheets synchronization tracking

Full-text search is enabled on inventory items for fast searching.

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black app/ main.py
```

### Adding Dependencies

```bash
pip install <package>
pip freeze > requirements.txt
```

## Roadmap

### Phase 2: Vector Drawing ✅ Complete
- Rectangle, line, and polygon drawing tools
- Layer management panel
- Selection and transform tools
- Background image import
- Save/load floor plans

### Phase 3: Inventory Management ✅ Complete
- Add/edit/delete inventory items
- Category and tag management
- Full-text search
- CSV import
- Image upload

### Phase 4: Spatial Inventory ✅ Complete
- Drag inventory items onto floor plan
- Color-coded markers (stock levels)
- Search to highlight on map
- Persistent marker storage

### Phase 5: Google Sheets Sync (Weeks 8-9)
- OAuth 2.0 authentication
- Two-way synchronization
- Conflict resolution
- Auto-sync timer

### Phase 6: Export/Import (Weeks 10-11)
- Export to JSON/XML
- Export as PNG/PDF
- Import floor plans
- Measurement tools
- Undo/redo

### Phase 7: Packaging (Week 12)
- PyInstaller executables
- macOS app bundle
- Windows installer
- Linux AppImage

### Phase 8: Future Enhancements
- eBay comp data integration
- Product image auto-import
- Barcode/QR code support
- Mobile companion app
- 3D visualization

## Configuration

Settings are stored in platform-specific locations:
- **macOS**: `~/Library/Preferences/com.InventoryMapper.InventoryMapper.plist`
- **Windows**: Registry under `HKEY_CURRENT_USER\Software\InventoryMapper\InventoryMapper`
- **Linux**: `~/.config/InventoryMapper/InventoryMapper.conf`

## Troubleshooting

### Database Issues

If you encounter database errors, you can reset by deleting:
- **macOS**: `~/Library/Application Support/InventoryMapper/inventory_mapper.db`
- **Windows**: `C:\Users\<username>\AppData\Local\InventoryMapper\InventoryMapper\inventory_mapper.db`
- **Linux**: `~/.local/share/InventoryMapper/inventory_mapper.db`

The database will be recreated on next launch.

### High DPI Displays

The application automatically handles high DPI displays. If text appears blurry, ensure your system's display scaling is set correctly.

## License

Copyright © 2026 Inventory Mapper

## Support

For issues, feature requests, or questions, please open an issue on the project repository.

## Credits

Built with:
- [PySide6](https://doc.qt.io/qtforpython-6/) - Qt for Python GUI framework
- [SQLite](https://www.sqlite.org/) - Database engine
- [Pillow](https://python-pillow.org/) - Image processing
- [gspread](https://docs.gspread.org/) - Google Sheets API wrapper
