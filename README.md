# 🏔️ Gaki Pelzom – The Bhutan Challenge

> **A turn‑based policy simulation game inspired by Bhutan’s Gross National Happiness (GNH) index.**  
> Balance **Economy, Environment, Culture, and Governance** over 15 turns. Every decision ripples through your district, shaping its future – and your progress is permanently saved for your next run!

---

## 📌 Table of Contents

- [🌏 Overview](#-overview)
- [✨ Key Features](#-key-features)
- [🎮 How to Play](#-how-to-play)
- [⚙️ Installation & Setup](#️-installation--setup)
- [🕹️ Controls](#️-controls)
- [🗃️ Data Files & Customisation](#️-data-files--customisation)
- [📂 File Structure](#-file-structure)
- [📦 Dependencies](#-dependencies)
- [🎨 Credits & Assets](#-credits--assets)
- [📚 Web References & Citations](#-web-references--citations)
- [📄 License](#-license)

---

## 🌏 Overview

**Gaki Pelzom** (roughly *“Path of Happiness”* in Dzongkha) simulates governing a district in Bhutan. You start by selecting one of 20 districts on an interactive map, each with its own starting pillars and hidden variables. Over 15 turns, you face a series of decision scenarios – each offering three choices – that directly impact your district:

- **Four Visible Pillars:** Economy, Environment, Culture, Governance.
- **Five Hidden Stats:** Social Unrest, Ecological Stress, Corruption Index, Foreign Influence, Public Trust.

> 🎯 **Ultimate Goal:** Maximise the **GNH Index** (the average of your four pillars) by Turn 15. After each playthrough, your district's ending values carry over as its new starting state, turning every run into part of an extended governance campaign.

---

## ✨ Key Features

- 🔄 **Persistent World** – District progress permanently carries over between playthroughs.
- 🔀 **15 Unique Decision Scenarios** – Dynamic selection guarantees scenarios never repeat within a single run.
- 🚨 **Fully Integrated Crisis System** – Hidden stats exceeding safe thresholds (e.g., *Corruption > 60*) trigger urgent, unexpected crises.
- 📉 **Passive Decay** – Unchecked stress in hidden stats slowly degrades your four primary pillars over time.
- 👻 **Ghost Feedback** – Narrative feedback previews consequences for 2 seconds before numerical stats shift.
- 🗣️ **Advisor Voices** – Hover over any choice to receive distinct hints from your **Economist**, **Ranger**, and **Monk** advisors.
- 📊 **End‑Screen Analytics** – Comprehensive final report featuring performance grades (*Excellent / Good / Struggling / Critical*) and a custom Matplotlib trend graph tracking your 15-turn trajectory.
- 🖥️ **Fullscreen Pygame Interface** – Rich UI complete with animated counters and custom sound effects.

---

## 🎮 How to Play

### 1. Map Selection

1. **Hover** over any district polygon on the interactive map to highlight it.
2. **Click** a district to open its sidebar panel displaying its name, population, description, and initial pillar stats.
3. Click the **BEGIN** button to launch your campaign.

### 2. The 15-Turn Loop

Each turn progresses through the following flow:

```text
 ┌──────────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐
 │  Scenario / Crisis   │ ───► │   Hover Advisors &   │ ───► │  Ghost Narrative     │
 │  Event Appears       │      │   Select an Option   │      │  Feedback (~2s)      │
 └──────────────────────┘      └──────────────────────┘      └──────────────────────┘
                                                                        │
 ┌──────────────────────┐      ┌──────────────────────┐                 │
 │  Next Turn / Graph   │ ◄─── │ Passive Decay & Stat │ ◄───────────────┘
 │  Snapshot Saved      │      │ Updates Clamped 0-100│
 └──────────────────────┘      └──────────────────────┘
```

- **Scenario / Crisis:** A policy challenge (e.g., “Hydropower Dam Proposal”) or crisis (e.g., “Corruption Scandal”) appears.
- **Options & Advice:** Review three options and hover over each to inspect advisor feedback.
- **Choice & Resolution:** Select an option to trigger narrative ghost feedback before permanent stat adjustments apply (clamped between 0 and 100).
- **Turn Advance:** Passive decay processes, stats log to history, and a new non-repeating scenario is drawn.

### 3. End Screen & Campaign Persistence

- **End-Game Analysis:** Review your final GNH score, grade, pillar breakdown, and Matplotlib trajectory graph.
- **Save State:** Returning to the map (via `ESC` or the Back button) saves your final stats to `game_data.json`. Selecting the same district in your next run resumes right where you left off!

---

## ⚙️ Installation & Setup

### Prerequisites

- Python 3.10+ installed on your system.
- Git installed on your system.

### 🪟 Windows Setup

1. Open PowerShell or Command Prompt and clone the repository:

   ```dos
   git clone https://github.com/rinzinthinley978/JakarHSS-GNH-project.git
   cd JakarHSS-GNH-project
   ```

2. Create and activate a virtual environment:

   ```dos
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. Install dependencies:

   ```dos
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Run the game:

   ```dos
   python main.py
   ```

### 🍎 macOS Setup

1. Open Terminal and clone the repository:

   ```bash
   git clone https://github.com/rinzinthinley978/JakarHSS-GNH-project.git
   cd JakarHSS-GNH-project
   ```

2. Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Run the game:

   ```bash
   python3 main.py
   ```

### 🐧 Linux Setup (Ubuntu / Debian / Arch / Fedora)

1. Install system dependencies (required for Pygame audio & graphics):

   **Ubuntu/Debian:**
   ```bash
   sudo apt update
   sudo apt install python3-venv python3-pip git libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev
   ```

   **Arch Linux:**
   ```bash
   sudo pacman -S python git sdl2 sdl2_image sdl2_mixer sdl2_ttf
   ```

   **Fedora:**
   ```bash
   sudo dnf install python3-devel git SDL2-devel SDL2_image-devel SDL2_mixer-devel SDL2_ttf-devel
   ```

2. Clone the repository:

   ```bash
   git clone https://github.com/rinzinthinley978/JakarHSS-GNH-project.git
   cd JakarHSS-GNH-project
   ```

3. Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

4. Install dependencies:

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. Run the game:

   ```bash
   python3 main.py
   ```

---

## 🕹️ Controls

| Action                     | Input / Key                          |
|----------------------------|--------------------------------------|
| Select District            | Left‑Click on district polygon       |
| Start Game                 | Click **BEGIN** button               |
| Choose Scenario Option     | Left‑Click on option button          |
| Return to Map              | Press `ESC` (from Game Scene or End Screen) |
| Quit Game                  | Close window or press `ESC` on map   |

---

## 🗃️ Data Files & Customisation

Game configuration files reside in the `data/` directory:

| File                          | Type       | Purpose                                                      |
|-------------------------------|------------|--------------------------------------------------------------|
| `game_data.json`              | Dynamic    | Stores live district pillar and hidden stat states (auto-saved). |
| `default_data.json`           | Read‑Only  | Factory‑reset backup values for all 20 districts.            |
| `decisions.json`              | Editable   | Scenario pool, prerequisites, options, stat deltas, and advisor quotes. |
| `crises.json`                 | Editable   | Crisis definitions, trigger conditions, and resolution paths. |
| `bhutan_districts.geojson`    | Read‑Only  | Vector boundary geometries for the map.                      |

> [!TIP]
> You can easily add custom policy scenarios or crises by editing `decisions.json` or `crises.json`! Changes load automatically upon restarting the game as long as valid JSON syntax is maintained.

---

## 📂 File Structure

```plaintext
JakarHSS-GNH-project/
├── main.py                         # Core game loop & state coordinator
├── game_func/
│   ├── __init__.py
│   ├── data_loader.py              # Persistence, JSON I/O & scaling helpers
│   ├── game_state.py               # Live stat tracking & decay engine
│   ├── game_scene.py               # Render pipeline, ghost phase & end screen
│   ├── ui_panel.py                 # District info sidebar renderer
│   ├── district_loader.py          # Map interaction & polygon detection
│   ├── districts_process.py        # GeoJSON spatial scaling & RAM coordinate generation
│   ├── scenario_engine.py          # Scenario deck manager (prevents duplicates)
│   ├── crisis_engine.py            # Crisis evaluation & cooldown timers
│   ├── loading.py                  # Initial loading screen handler
│   └── font_manager.py             # Typography loader & wrapper
├── data/
│   ├── game_data.json              # Persistent save file
│   ├── default_data.json           # Factory reset data
│   ├── decisions.json              # Policy scenario library
│   ├── crises.json                 # Crisis event library
│   └── bhutan_districts.geojson    # Source map geometries
├── assets/
│   ├── ui/                         # Interface textures, buttons, panels, fonts
│   └── sounds/                     # BGM tracks and interface SFX
├── requirements.txt
└── README.md
```

---

## 📦 Dependencies

All core packages are specified in `requirements.txt`:

- 🎮 **pygame** >= 2.6.0 – Graphics rendering, event loop, and audio playback.
- 📐 **shapely** >= 2.0.6 – Point‑in‑polygon spatial collision detection.
- 🗺️ **geojson** >= 3.1.0 – Geographic data parsing.
- 📈 **matplotlib** >= 3.8.0 – End‑game trajectory graph rendering (headless Agg backend).
- 🔢 **numpy** >= 1.24.0 – Array operations and audio signal processing.

---

## 🎨 Credits & Assets

### 👥 Development Team

- **Developers:** Rinzin Thinley, Pema Norbu Zangpo, Deki Yangzom
- **UI/Icon Asset Design:** Deki Yangzom
- **Repository:** [rinzinthinley978/JakarHSS-GNH-project](https://github.com/rinzinthinley978/JakarHSS-GNH-project)
- **Inspiration:** Bhutan’s Gross National Happiness philosophy
- **Map Source:** District boundaries adapted from public GeoJSON repositories

### 🖌️ Third‑Party Asset Attribution

**Graphics & UI**

- Main Menu Background & App Icon (`main_menu.png`, `icon.png`): Original artwork by Deki Yangzom.
- Button Sprites (`button.png`): Created by Hiskia Revaldo (Vecteezy - Wooden Board Pixel Art).
- Loading Bar Elements (`loading_bar_layout.png`, `loading_bar_progress.png`): Created by Baraltech / harsitbaral (GitHub - LoadingBarPyGame).
- Navigation UI (`back_button.png`): Created by crusenho (itch.io - Complete UI Essential Pack).
- Panels & Cursors (`panel.png`, `mouse_icon.png`): Created by cupnooble (itch.io - Sprout Lands UI Pack).

**🔤 Typography**

- Pixel Body Font (`pixel_body.ttf`): Pixel Operator by Jayvee Enaguas (DaFont).
- Pixel Heading Font (`pixel_heading.ttf`): Source via OnlineWebFonts.

**🔊 Audio & Sound Effects**

- Background Music (`bgm.wav`): Cute Loops 2 pack by sonatina (itch.io).
- Click SFX (`click.wav`): Modern technology select (Mixkit Free License).
- Success / Lock SFX: Fantasy game success notification (Mixkit Free License).

---

## 📚 Web References & Citations

Baraltech. (2021). *LoadingBarPyGame* [Computer software]. GitHub. [https://github.com/harsitbaral/LoadingBarPyGame](https://github.com/harsitbaral/LoadingBarPyGame)

Crusenho. (2020). *Complete UI essential pack* [Video game asset pack]. itch.io. [https://crusenho.itch.io/complete-ui-essential-pack](https://crusenho.itch.io/complete-ui-essential-pack)

Cupnooble. (2021). *Sprout lands UI pack* [Video game asset pack]. itch.io. [https://cupnooble.itch.io/sprout-lands-ui-pack](https://cupnooble.itch.io/sprout-lands-ui-pack)

Enaguas, J. (2018). *Pixel operator font family* (Version 2018.10.04-1) [Font]. DaFont. [https://www.dafont.com/pixel-operator.font](https://www.dafont.com/pixel-operator.font)

Mixkit. (n.d.-a). *Fantasy game success notification* [Sound effect]. Envato Elements. [https://mixkit.co/free-sound-effects/win/](https://mixkit.co/free-sound-effects/win/)

Mixkit. (n.d.-b). *Modern technology select* [Sound effect]. Envato Elements. [https://mixkit.co/free-sound-effects/click/](https://mixkit.co/free-sound-effects/click/)

Pygame Developers. (2024). *Pygame* (Version 2.6.0) [Computer software]. Python Software Foundation. [https://www.pygame.org/](https://www.pygame.org/)

Revaldo, H. (2021). *Wooden board pixel art design vector* [Vector graphic]. Vecteezy. [https://www.vecteezy.com/vector-art/2042129-wooden-board-pixel-art](https://www.vecteezy.com/vector-art/2042129-wooden-board-pixel-art)

Sonatina. (2021). *Cute loops 2* [Audio music pack]. itch.io. [https://sonatina.itch.io/cute-loops-2](https://sonatina.itch.io/cute-loops-2)

The Shapely Development Team. (2024). *Shapely: Manipulation and analysis of geometric objects* (Version 2.0.6) [Computer software]. PyPI. [https://pypi.org/project/shapely/](https://pypi.org/project/shapely/)

---

## 📄 License

Distributed under the MIT License. You are free to use, modify, and distribute this software provided original attribution is preserved alongside asset licenses.