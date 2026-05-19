# RetroList - Emulator & ROM Manager

A lightweight, desktop-based ROM manager built with Python and CustomTkinter. RetroList helps you organize your retro game collection, manage custom metadata, and launch games directly into your favorite emulators with a clean, modern user interface.

## 🚀 Features

* **Console Management:** Add, edit, delete, and manually reorder your game consoles. Assign specific emulator executables (`.exe`) and ROM directories for each system.
* **Library View (Master-Detail Layout):** A responsive interface that displays your game list alongside detailed metadata and cover art.
* **Automated ROM Scanning:** One-click scan to detect and add new ROMs from your assigned folders.
* **Metadata Editor:** Customize game details including Developer, Release Year, Genre, and Language. 
* **Badges & Cover Art:** Assign "Hack" or "Translated" badges to specific games and upload custom cover art images.
* **Advanced Search & Filtering:** Search by name, filter by genre, and sort by various criteria (A-Z, Year, Newest/Oldest).
* **Mass Edit via CSV:** Export your entire database to a `.csv` file, edit it in Google Sheets or Excel, and import it back to update your library instantly.
* **Quick Launch:** Play your games directly from the app.

## 📸 Screenshots

<<<<<<< HEAD
=======

>>>>>>> e7b2ce6 (chore: clean up repository and update .gitignore)
| Home View | Library View |
|:---:|:---:|
| ![Home](https://i.postimg.cc/dV7z6SG7/retrolist-screenshot1.jpg) | ![Library](https://i.postimg.cc/qMqYBZDJ/retrolist-screenshot2.jpg) |

## 🛠️ Tech Stack

* **Language:** Python 3.x
* **GUI Framework:** CustomTkinter
* **Database:** SQLite3
* **Image Processing:** Pillow (PIL)

## 🎮 How to Use

* Click Menu -> Add Console on the Home screen.
* Enter the console name and assign the Emulator Path (e.g., nestopia.exe) and the ROMs Folder.
* Click on the newly created console card to enter its Library View.
* Click Scan ROMs at the top right to populate your list.
* Select any game, click Edit to update its metadata/cover, or click Launch to play.
* To backup or mass-edit data, use the Export/Import CSV options from the main menu.

## ⚠️ Known Issues & Technical Debt
Currently running as an MVP (Minimum Viable Product).
UI components in the Library View might require refactoring into separate classes (Master/Detail components) in future updates for better maintainability.
Ensure your database file (retrolist.db) and image folders (covers/, icons/) are backed up before performing massive CSV imports.

## 📄 License
MIT License
