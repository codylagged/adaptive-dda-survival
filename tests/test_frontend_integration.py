import pytest
import pygame
from frontend.session import GameSession
from frontend.app import GameApp
from backend.game_engine import GameEngine

@pytest.fixture
def app():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    app = GameApp(screen)
    yield app
    pygame.quit()

# ... (truncated for brevity in this thought, but I'll use full content)