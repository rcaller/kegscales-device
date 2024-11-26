# Kegscales - device

## Summary

Micropython for the RaspBerry Pi Pico Kegscales project

## Project Outline
The kegscales project is attempting to create a replacement for the soon to be defunct Plaato Keg.
The project aims to create a device that can measure how much beverage remains in a keg using easily 
available components and a 3d printed enclosure.

The project currently consists of the Raspberry Pi Pico communicating over BLE with an android app

## This Repository
This repository contains micropython code to be installed onto a Raspberry Pi Pico W microcontroller.

### Installation
Download the compiled firmware from the latest release.  Plug your raspberry pi pico w into a PC with a usb cable.  At should appear as a writable directory, simply drop the firmware into this directory, the Pico should reboot and start running (the led will start flashing after a little while).  Now scan and detect the device from the app and continue configuration from there.
