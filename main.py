import sys
import time
import pygame

# Import game modules
from game_func.district_loader import MapScreen
from game_func.districts_process import DistProc
from game_func.loading import loadingScreen
from game_func.data_loader import DataLoader
from game_func.ui_panel import Panel
from game_func.font_manager import FontManager
from game_func.game_scene import GameScene
from game_func.game_state import GameState
from game_func.scenario_engine import ScenarioEngine
from game_func.crisis_engine import CrisesEngine
from game_func.main_menu import MainMenu

# Initialize Pygame and its audio subsystem (mixer)
pygame.init()
pygame.mixer.init()

# --- Core Systems Initialization ---
# Create reusable systems: data loader, fonts, UI panels, and game engines
data_loader = DataLoader()
heading_font = FontManager('assets/ui/pixel_heading.ttf')
body_font = FontManager('assets/ui/pixel_body.ttf')

loading_screen = loadingScreen(data_loader, heading_font)
info_panel = Panel(data_loader, heading_font, body_font)
game_scene = GameScene(data_loader, info_panel, heading_font, body_font)
district_processor = DistProc(data_loader)
map_screen = MapScreen(data_loader, district_processor, heading_font)
game_state = GameState(data_loader)
scenario_engine = ScenarioEngine()
crisis_engine = CrisesEngine()
main_menu = MainMenu(data_loader, heading_font, body_font)

# --- Audio Setup ---
# Set background music and volume
pygame.mixer.music.play(-1)  # play indefinitely
pygame.mixer.music.set_volume(0.5)

# --- Window and Cursor Setup ---
# Configure window title, icon, and custom mouse cursor
pygame.display.set_icon(data_loader.game_icon)
pygame.display.set_caption(data_loader.title)
pygame.mouse.set_cursor(data_loader.cursor_sprite)

# --- Game State Variables ---
# Track current state, user interactions, and pending actions
running = True
current_state = "Loading"
hover_index = None
pending_choice = None
pending_scenario = None
pending_was_crisis = False
current_scenario = None
is_current_crisis = False
game_saved = False
menu_action = None

time.sleep(0.5)  # brief delay to ensure assets are ready

def reset_game_session():
    # Reset all game state to start a new session
    global current_scenario, pending_choice, pending_scenario, game_saved, is_current_crisis, pending_was_crisis
    data_loader.reload_data()         # reload any dynamic game data
    game_state.reset()                # reset game state tracking
    game_scene.reset()                # reset scene components
    scenario_engine.clear_lock()      # clear scenario locks
    crisis_engine.reset()             # reset crisis tracking
    data_loader.selected_district = None
    current_scenario = None
    pending_choice = None
    pending_scenario = None
    pending_was_crisis = False
    game_saved = False
    is_current_crisis = False

def construct_feedback_message(choice_effect):
    # Generate a user-friendly summary of a choice's effects
    effects = choice_effect.get('effects', choice_effect)
    delayed = choice_effect.get('delayed', [])

    # Prefer a delayed message if available
    if delayed and len(delayed) > 0 and delayed[0].get('message'):
        return delayed[0]['message']

    # Otherwise summarize pillar changes
    pillars = effects.get('pillars', {})
    positive = [name.capitalize() for name, magnitude in pillars.items() if magnitude > 0]
    negative = [name.capitalize() for name, magnitude in pillars.items() if magnitude < 0]

    parts = []
    if positive:
        parts.append(f"{', '.join(positive)} flourishes")
    if negative:
        parts.append(f"{', '.join(negative)} suffers")

    return '. '.join(parts) + '.' if parts else "The consequences of your decision will unfold in time..."

# --- Main Game Loop ---
# Handles events, updates, rendering, and state transitions
while running:
    # Scale fix: convert real mouse position to virtual coordinates
    data_loader.mousePos = data_loader.get_virtual_mouse_pos()
    delta_time = data_loader.clock.tick(data_loader.frames)

    # ---------- Event Handling ----------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # ESC key returns to map from game or end screen
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if current_state in ('Game Scene', 'End Screen'):
                reset_game_session()
                current_state = 'Map'

        # Menu events
        if current_state == "Menu":
            action = main_menu.handle_events(event)
            if action:
                menu_action = action

        # Map events
        elif current_state == 'Map':
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                panel_action = info_panel.handle_events(event)

                if panel_action == "back":
                    data_loader.selected_district = None
                    current_state = "Menu"

                elif panel_action == "begin":
                    district_data = data_loader.get_district_data()
                    if district_data:
                        game_state.receive_data(district_data)
                        game_scene.reset()
                        # Check for a crisis first, otherwise a normal scenario
                        crisis = crisis_engine.check_crises(game_state)
                        if crisis:
                            current_scenario = crisis
                            is_current_crisis = True
                        else:
                            current_scenario = scenario_engine.filter_deck(
                                game_state.turn, game_state.played_scenarios, game_state.flags
                            )
                            is_current_crisis = False
                        current_state = 'Game Scene'
                    else:
                        print(f"Error: Selected district '{data_loader.selected_district}' returned no data.")

                else:
                    map_screen.check_click()

        # Game Scene events
        elif current_state == 'Game Scene':
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                choice_effect = game_scene.handle_choice(event, data_loader.mousePos)
                if choice_effect:
                    # Store the pending choice until ghost animation ends
                    pending_choice = choice_effect
                    pending_scenario = current_scenario
                    pending_was_crisis = is_current_crisis

                    feedback = construct_feedback_message(choice_effect)
                    game_scene.set_ghost_feedback(feedback)

                    if isinstance(pending_scenario, dict) and 'id' in pending_scenario:
                        game_scene.ghost_scenario_title = pending_scenario.get('title', '')

        # End Screen events
        elif current_state == 'End Screen':
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game_scene.back_rect.collidepoint(data_loader.mousePos):
                    reset_game_session()
                    current_state = 'Map'

    # ---------- Game Logic Updates ----------
    # Apply pending choice after ghost phase finishes
    if pending_choice and not game_scene.ghost_active:
        game_state.apply_choice(pending_choice)
        if isinstance(pending_scenario, dict) and 'id' in pending_scenario:
            if pending_was_crisis:
                crisis_engine.resolve_crisis()
            else:
                game_state.update_scenario_details(pending_scenario['id'])
                scenario_engine.clear_lock()

        pending_choice = None
        pending_scenario = None
        pending_was_crisis = False

        # Check for a new crisis after the choice
        crisis = crisis_engine.check_crises(game_state)
        if crisis:
            current_scenario = crisis
            is_current_crisis = True
        else:
            current_scenario = scenario_engine.filter_deck(
                game_state.turn, game_state.played_scenarios, game_state.flags
            )
            is_current_crisis = False

    # End game after 15 turns
    if current_state == 'Game Scene' and game_state.turn >= 15:
        current_state = 'End Screen'

    # Save final state once when entering end screen
    if current_state == 'End Screen' and not game_saved:
        final_state = game_state.get_final_state()
        data_loader.save_district_data(data_loader.selected_district, final_state)
        game_saved = True

    # ---------- State Transitions ----------
    if current_state == "Loading":
        loading_screen.do_work(delta_time)
        if loading_screen.loading_finished:
            current_state = "Menu"

    elif current_state == "Menu" and menu_action:
        if menu_action == "start":
            current_state = "Map"
        elif menu_action == "reset":
            data_loader.reset_all_district_data()
        elif menu_action == "quit":
            running = False
        menu_action = None

    elif current_state == 'Map':
        map_screen.check_hover()

    # ---------- Rendering ----------
    # Always fill the virtual surface with the background color
    data_loader.virtual_surface.fill('#ffffff')

    if current_state == "Loading":
        loading_screen.check_loading()

    elif current_state == "Menu":
        main_menu.draw(data_loader.virtual_surface)

    elif current_state == 'Map':
        map_screen.draw(data_loader.virtual_surface)
        info_panel.screen = data_loader.virtual_surface
        info_panel.draw_panel()

    elif current_state == 'Game Scene':
        game_scene.screen = data_loader.virtual_surface
        hover_index = game_scene.handle_hover(data_loader.mousePos)
        game_scene.display_info(game_state)
        game_scene.draw_scenario(current_scenario, hover_index)

    elif current_state == 'End Screen':
        game_scene.screen = data_loader.virtual_surface
        game_scene.draw_end_screen(game_state)

    # Always scale the virtual surface and blit it to the real screen
    data_loader.render_frame()

    data_loader.show_fps(0)
    pygame.display.flip()

pygame.quit()
sys.exit()
