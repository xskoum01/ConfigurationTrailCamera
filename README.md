🎯 Configuration Trail Camera
Configuration Trail Camera is a Python desktop application built with PyQt6.
It provides an easy-to-use interface for configuring, controlling, and monitoring a trail camera based on an ESP32 microcontroller.

🚀 What It Does
- Connects to an ESP32-based trail camera via a serial (UART) connection.

- Loads and saves configuration (wake-up time, photo resolution, photo quality, APN, URL, keys).

- Lets you take a photo remotely and display it in the app.

- Reads and displays battery level, charging status, signal level, and remaining battery time.

- Sends SMS commands based on selected options.

- Allows you to reset the trail camera or LTE module and restore default settings.

- Fully controllable via a simple PyQt GUI.

🛠️ Technologies Used
- Python 3

- PyQt6 for GUI

- pyserial for serial communication

- JSON for configuration exchange

📸 Main Features
- Connect to any available serial port

- Add phone numbers dynamically

- Configure camera wake-up times, resolution, and photo sending options

- View photos directly inside the app

- Real-time status bar messages for clear feedback

- Save configuration to the device or reset it to factory defaults

