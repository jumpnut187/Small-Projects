# OpenWebUI Controller

A desktop application for managing and monitoring the OpenWebUI service with an easy-to-use graphical interface.

## Features

- Start and stop OpenWebUI service with a single click
- Monitor system resources (CPU, RAM, GPU) in real-time
- View terminal output logs directly in the application
- Easy installation of OpenWebUI if not already installed
- Quick access to the OpenWebUI interface through clickable links

## Requirements

- Python 3.6+
- tkinter (usually included with Python installations)
- psutil (for system monitoring)
- GPUtil (optional, for NVIDIA GPU monitoring)
- OpenWebUI (can be installed through the application)

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r Requirements.txt
```

3. Run the application:

```bash
python Open_WebUI_GUI_Server.py
```

## Usage

### Starting OpenWebUI

1. Ensure OpenWebUI is installed (if not, use the "Install OpenWebUI" button)
2. Click the "Start OpenWebUI" button
3. Access the web interface by clicking the "http://localhost:8080" link

### Monitoring Resources

The application shows real-time metrics for:
- CPU usage
- Memory usage
- GPU usage (if available)
- GPU memory (if available)
- Process memory consumption

### Logs

The terminal log section displays the output from the OpenWebUI process, making it easy to troubleshoot issues.

## Platform Support

- Windows
- macOS (with special handling for Apple Silicon/Metal GPU)
- Linux

## Troubleshooting

- If OpenWebUI command is not found, ensure it's installed and in your PATH, or use the "Browse" button to locate the executable
- Check the terminal log for error messages
- Make sure you have proper permissions to execute commands

## License

GNU GENERAL PUBLIC LICENSE Version 2
                       

## Links

- [OpenWebUI Documentation](https://docs.openwebui.com/)
- [OpenWebUI GitHub Repository](https://github.com/open-webui/open-webui)
