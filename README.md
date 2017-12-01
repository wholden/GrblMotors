# GrblMotors
Python-based interface to GRBL for simple motion control

This driver is intended to provide a simplified python interface to GRBL for simple motion control tasks.  GRBL is very well written, and performs very well for tasks like acceleration profiles, homing routines, and fast, reliable USB communication.  GRBL also makes very efficient use of the Aruduino Uno hardware and available pins.  Also, with extremely cheaply stepper motor drivers (A4988 or DRV8825), and cheap arduino shields for mounting them (e.g. https://blog.protoneer.co.nz/arduino-cnc-shield/), making use of GRBL allows a complex setup with four different motors to be controlled from a single compact board.

This driver simplifies controlling GRBL to python commands that move in terms of actual steps of the stepper motor.  User functions are written on top of this driver to take care of the conversion from steps to physically meaningful dimensions.

Though this is part of a laboratory experiment system, so the configuration and layout is made with our specific use in mine, the grbldriver.py file itself is more general.
