# Flask Paging and TTS Alert System

This project is a browser-based real-time alert system built with Flask and Socket.IO. It allows administrators to send audio alerts and spoken messages to connected clients through a control panel. Clients can register with a name and group, and receive alerts instantly through their web browser or Raspberry Pi- device.

The system is intended to be used for environments like fire stations and will eventually be implemented to aid the live-ins.

## Features

- Real-time communication using WebSockets (via Flask-SocketIO)
- Web-based client and admin interfaces (found on localhost:8080/client or localhost:8080/admin or whatever URL is chosen)
- Password-protected admin control panel (Password should be changed prior to implementation)
- Trigger alerts for:
  - Individual users
  - Entire groups (Group A or Group B)
- Text-to-Speech (TTS) messaging:
  - Type a message to be spoken on the client
  - Target selected users or groups
- Scheduled and repeating TTS messages:
  - Set a specific time for a message to play
  - Optionally repeat messages on a fixed interval
- Client-side custom alert sounds:
  - Clients can upload a personal alert tone
  - Server stores and plays this tone when alerts are triggered

Project Structure

- Server.py                  #   Flask + SocketIO backend server
  - index.html                 #   Admin interface (login and control panel)
  - client.html                #   Client interface (receives alerts)
  - test_app.py                #   Unit tests for backend routes
- requirements.txt           #   Dependency list
- static/
- templates/                
- .github/
  - workflows/
    - python-tests.yml   #   GitHub Actions workflow for automated testing


