# PEK Pimp Project

## Overview
The PEK Pimp project is a Python application that rewards users with PEK tokens based on their PIMP transactions. It continuously queries the Hive Engine API for PIMP transfers, calculates the corresponding PEK rewards, and sends the rewards to eligible users.

## Files
- `src/pek_pimp.py`: Contains the main functionality of the application, including the logic for sending PEK tokens and querying the Hive Engine API.
- `requirements.txt`: Lists the dependencies required for the project.

## Setup Instructions
1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd pek_pimp
   ```

2. **Install Dependencies**
   Ensure you have Python installed, then run:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**
   Execute the following command to start the application:
   ```bash
   python src/pek_pimp.py
   ```

## Usage
The application will run continuously, checking for new PIMP transactions every minute. When eligible transactions are found, it will automatically send the corresponding PEK rewards to the users.

## Contributing
Feel free to submit issues or pull requests for any improvements or bug fixes.