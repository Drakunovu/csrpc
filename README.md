# Counter-Strike 1.6 RPC

## What is this about?

This is a simple Python script that shows information of Counter-Strike 1.6 in Discord Rich Presence, using either IP of the server or Steam WebAPI to get status of the server.

## Releases

You can find all the latest releases [here](https://nightly.link/Drakunovu/csrpc/workflows/build/master), choose the platform you want and it should work.

In Windows might give a Windows Defender alert, this is normal behaviour and you can add a exception and it would work, if you don't trust you can see the source code and even run and build it yourself.

## Requirements

[Python](https://www.python.org/downloads/) must be **>= 3.6**

Install the needed packages:

`pip install -r requirements.txt`

## TO-DO

Here is a list of things that could make better this script:

* Make the script work on almost any Valve games (Half-Life-based ones, or even Source-based ones) with automatic recognition of the game

* Multilingual support

* More variables to show (for example, PUGs Servers could show "T: 1 | CT: 5" in the details section)

* Possible better formatting code and optimizations
