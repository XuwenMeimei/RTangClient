# RTangClient

## Overview
RTangClient is a multimedia application built using PySide6 that allows users to play music, manage game launches, and display notifications through a toast system. The application features a clean and modern UI with customizable styles.

## Features
- Music playback controls (play, pause, next, previous)
- Game launch functionality with progress indication
- Toast notifications for user feedback
- Customizable UI styles

## Project Structure
```
RTangClient
├── src
│   ├── __init__.py
│   ├── main.py
│   ├── ui
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   ├── sidebar.py
│   │   ├── title_bar.py
│   │   ├── content.py
│   │   └── music_bar.py
│   ├── utils
│   │   ├── __init__.py
│   │   └── resource.py
│   ├── music
│   │   ├── __init__.py
│   │   └── player.py
│   └── toast
│       ├── __init__.py
│       └── toast_manager.py
├── assets
│   └── (logo.png, music_icon.png, etc.)
├── styles
│   └── pink_theme.qss
└── README.md
```

## Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```
   cd RTangClient
   ```
3. Install the required dependencies:
   ```
   pip install PySide6
   ```

## Usage
To run the application, execute the following command:
```
python src/main.py
```

## Customization
You can customize the appearance of the application by modifying the `styles/pink_theme.qss` file. 

## Contributing
Contributions are welcome! Please feel free to submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.