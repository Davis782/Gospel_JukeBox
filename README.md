# Gospel JukeBox Application Application

## Overview
The Gospel JukeBox is a music player application that allows you to play gospel songs and view associated lyrics and images.

## Project Structure

The application follows this structure:

```
/                           # Root directory
├── main.py                 # Main application file
├── Gospel_JukeBox.py       # JukeBox implementation
├── requirements.txt        # Dependencies
├── README.md               # This file with instructions
├── data/                   # Application data
│   └── songs/              # Song directories with mp3, txt, and image files
├── mp3_files/              # MP3 files with corresponding lyrics
├── pictures/               # Image files
├── Sandbox_Files/          # Non-essential files
    ├── Dockerfile          # Docker configuration
    ├── .dockerignore       # Docker ignore file
    └── Unused_Test_Files/  # Test and backup files
```

## Development Setup

### Prerequisites
- - Python 3.8 or higher
- Required Python packages (listed in requirements.txt)

### Installation
1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```

## Docker Setup

#

## Version Control Guidelines

#

## Maintenance Guidelines

- Keep the root directory clean with only essential files
- Place test files in the Sandbox_Files/Unused_Test_Files directory
- Update .dockerignore when adding new file types
- Document changes to the folder structure
- Regularly update dependencies for security

## Troubleshooting

### Common Issues
1. **Port conflicts**: Ensure port 8550 is not in use by another application
2. **Missing files**: Verify all required files are in the correct locations
3. **Docker errors**: Ensure Docker is running properly on your system

### Getting Help
If you encounter issues not covered here, please create an issue in the repository with:
- A clear description of the problem
- Steps to reproduce
- Expected vs. actual behavior
- Environment details (OS, Python version, etc.)