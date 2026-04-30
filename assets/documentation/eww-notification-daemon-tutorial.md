# Custom EWW Notification Daemon: Tutorial

**Source:** [YouTube – Vimjoyer](https://www.youtube.com/watch?v=UP3pJT1-UoQ)  
**Channel:** Vimjoyer  
**Duration:** 6:00  
**Code:** https://github.com/vimjoyer/eww-notification-daemon  

> **Note:** Transcribed from auto-generated captions. Technical terms corrected where identifiable.

---

## Introduction

EWW (ElKowary Widgets) is an amazing widget engine for both X.Org and Wayland. It is so powerful that you can replace any part of your desktop with it — and so today we are going to make a simple notification daemon which can be easily extended with your own functionality.

---

## Prerequisites

Before we begin, make sure to install EWW itself and also a programming language that will provide the logic for it, like Python.

EWW stores its configuration in the XDG config directory, so create and place a `eww.yuck` file inside. Yuck is a special markup programming language used by EWW and its syntax is very similar to Lisp.

---

## Defining the EWW Window

Open the file and we can begin our configuration by defining a window. Give it a name and let's define some properties.

`monitor` is a required one — if you only have one monitor like me, simply put a zero there; otherwise the fastest way is to just guess the number.

Next, let's provide it with `geometry` to define its position on the screen. Geometry takes a bunch of parameters itself like X offset, Y offset, and the anchor. It makes sense for a notification daemon to have a set amount of pixels here, but for most other widgets percentage is preferred.

A `stacking` property tells our window that it should sit on top of any other program. Assign it to `fg` (foreground) if you are on X.Org, or `overlay` if you are on Wayland.

---

## First Test

Before we can test it for the first time, we need to also put some widgets inside the window. For now, use a simple label. Launch your window with `eww open notifications` and you will see a small label appear at the top right corner of your screen.

We are almost there, except we did not write any logic yet.

---

## Python Backend Setup

Create a `main.py` file in the same directory and let's fill it with some code. We will need the `dbus-python` and `PyGObject` packages, so install them and add these imports at the top.

A Nix file with all of the required dependencies as well as all of the code from this video is going to be in the link in the description.

---

## How D-Bus Notifications Work

Notifications on most Linux desktops are done with a dbus interprocess message system. All of the notifications that you receive are usually going through the `org.freedesktop.Notifications` bus. Programs send messages containing your notifications to a dbus daemon, which then redirects those messages to whoever happens to own the bus. In our case, we are the bus owners.

---

## The Notification Server Class

Add this notification server class that does all of the service registering for you and initialize it in `main`. All of this looks quite complicated, and I myself have only used Python once or twice — so the most important part that you might want to change here is the `notify` method. This is the part of the code that will be called each time some program decides to tell you some news.

For now, let's simply try to log all arguments with `print`. Launch the main file in the terminal and send yourself a notification with `notify-send`, for example. You will see all the notification data immediately.

---

## Building the Notification System

We don't want to display only one notification though, so let's make a system where each new notification is added to the list with a 10-second lifetime.

For it, we are going to define a `Notification` class at the top which is going to contain some data that we want to showcase. We will also define a `notifications` array for storing those objects, and two functions which insert objects at the beginning, use threading to remove each one of them after 10 seconds, and print the state of our notification system.

For now, the `print_state` function is just going to log every notification object that we have in one line.

Replace the logic in the `notify` method to just add a notification object with a summary, body, and an app icon to the array. If we now open our window, we can see that the last printed message shows the latest notifications in the system. Not bad — but who needs notifications in the terminal?

---

## Moving Notifications into the Widget

Let's move them to a widget. Open the Yuck file and define a `listen` variable above our window. It is going to invoke a command that we give to it once, and replace its content with whatever standard output gets flushed into it each time it is flushed.

If we launch our widget now, we are going to see that each time we send some notifications, more objects are added to the top right corner of your screen.

---

## Outputting Real Yuck Syntax from Python

Pretty cool — but we also want it to look decent. So let's instead tell EWW to take the content of this listen variable and treat it as part of its own syntax with `defpoll`. With this line, we can go back to the Python script and instead of printing Python objects, make it output real Yuck syntax.

I made a simple tree of boxes and labels that contains references to each notification's summary, body, and program icons. It gets generated for every present notification and then all of them get interpolated into the main vertical box.

If we launch our widget, we can see all of the new notifications appear with their images and text displayed correctly. Amazing.

---

## Styling with SCSS

The next step would be giving those ugly boxes some style with SCSS. Use the regular GTK styling options here and make it look the way you want by defining colors, paddings, margins, and borders. Classes here come from window names or `class` properties on the widgets. This is the styling I chose to use — and here's how it looks.

---

## Conclusion

Our super simple notification daemon is now completed. It might not be as feature-rich as other popular solutions, but because we just went through each part of the code together, you can add any functionality you need — including overriding certain app icons, changing colors in specific situations, saving history your way, or pretty much anything really.

As usual, don't forget to check out the Discord server, leave a like or a comment if you enjoyed this video, or subscribe if you are feeling extra generous. Thanks for watching, and I will see you in the next one.
