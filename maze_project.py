"""
MAZE GENERATOR & SOLVER - Complete Version
Production-Ready with GUI Buttons
Language: Python 3.8+
"""

import random
import json
import time
import sys
import threading
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum

try:
    import pygame
    from pygame.locals import *
except ImportError:
    print("ERROR: pygame not installed")
    print("Install with: pip install pygame")
    sys.exit(1)

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
except ImportError:
    print("ERROR: PyOpenGL not installed")
    print("Install with: pip install PyOpenGL PyOpenGL_accelerate")
    sys.exit(1)


class GameState(Enum):
    """Game states."""
    IDLE = "IDLE"
    GENERATING = "GENERATING"
    SOLVING = "SOLVING"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"


@dataclass
class MazeConfig:
    """Maze configuration."""
    rows: int = 20
    cols: int = 30
    cell_size: float = 0.4
    cycle_probability: float = 0.05
    generation_speed: int = 1
    solving_speed: int = 1
    
    def validate(self) -> bool:
        """Validate configuration."""
        return 5 <= self.rows <= 100 and 5 <= self.cols <= 100


class MazeGenerator:
    """Stack-based DFS maze generation."""
    
    def __init__(self, rows: int, cols: int, cycle_prob: float = 0.05):
        """Initialize maze generator."""
        self.rows = rows
        self.cols = cols
        self.cycle_probability = cycle_prob
        
        # North and East walls (1 = intact, 0 = eaten)
        self.north_wall = [[1] * cols for _ in range(rows)]
        self.east_wall = [[1] * cols for _ in range(rows)]
        
        # Visited tracking
        self.visited = [[False] * cols for _ in range(rows)]
        self.stack = []
        self.current_row = random.randint(0, rows - 1)
        self.current_col = random.randint(0, cols - 1)
        self.visited[self.current_row][self.current_col] = True
        self.generation_complete = False
        
    def get_unvisited_neighbors(self, r: int, c: int) -> List[Tuple[int, int, str]]:
        """Get unvisited neighbors (row, col, direction)."""
        neighbors = []
        directions = [
            (r - 1, c, 'N'),
            (r, c + 1, 'E'),
            (r + 1, c, 'S'),
            (r, c - 1, 'W')
        ]
        
        for nr, nc, direction in directions:
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                if not self.visited[nr][nc]:
                    neighbors.append((nr, nc, direction))
        
        return neighbors
    
    def step(self) -> bool:
        """Generate one step. Returns True if complete."""
        if self.generation_complete:
            return True
        
        neighbors = self.get_unvisited_neighbors(self.current_row, self.current_col)
        
        if neighbors:
            nr, nc, direction = random.choice(neighbors)
            self.visited[nr][nc] = True
            self.stack.append((self.current_row, self.current_col))
            
            # Eat through wall
            if direction == 'N':
                self.north_wall[self.current_row][self.current_col] = 0
            elif direction == 'S':
                self.north_wall[nr][nc] = 0
            elif direction == 'E':
                self.east_wall[self.current_row][self.current_col] = 0
            elif direction == 'W':
                self.east_wall[nr][nc] = 0
            
            self.current_row, self.current_col = nr, nc
        elif self.stack:
            self.current_row, self.current_col = self.stack.pop()
        else:
            # Open entrance and exit
            self.north_wall[0][0] = 0
            self.north_wall[self.rows - 1][self.cols - 1] = 0
            self.generation_complete = True
            return True
        
        # Random cycle creation - FIXED
        if random.random() < self.cycle_probability:
            visited_cells = [(r, c) for r in range(self.rows) for c in range(self.cols) if self.visited[r][c]]
            if visited_cells:
                r, c = random.choice(visited_cells)
                neighbors = [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
                for nr, nc in neighbors:
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        if nr == r - 1 and self.north_wall[r][c] == 1:
                            self.north_wall[r][c] = 0
                            break
                        elif nr == r + 1 and self.north_wall[nr][c] == 1:
                            self.north_wall[nr][c] = 0
                            break
                        elif nc == c + 1 and self.east_wall[r][c] == 1:
                            self.east_wall[r][c] = 0
                            break
                        elif nc == c - 1 and self.east_wall[nr][c] == 1:
                            self.east_wall[nr][c] = 0
                            break
        
        return False


class MazeSolver:
    """Backtracking maze solver."""
    
    def __init__(self, generator: MazeGenerator):
        """Initialize solver."""
        self.generator = generator
        self.rows = generator.rows
        self.cols = generator.cols
        self.visited = [[False] * self.cols for _ in range(self.rows)]
        self.stack = []
        self.path = []
        self.dead_ends = set()
        
        self.current_row = 0
        self.current_col = 0
        self.visited[0][0] = True
        self.solving_complete = False
        
    def can_move(self, r: int, c: int, nr: int, nc: int) -> bool:
        """Check if we can move from (r,c) to (nr,nc)."""
        if not (0 <= nr < self.rows and 0 <= nc < self.cols):
            return False
        
        if nr == r - 1 and self.generator.north_wall[r][c] == 0:
            return True
        if nr == r + 1 and self.generator.north_wall[nr][c] == 0:
            return True
        if nc == c + 1 and self.generator.east_wall[r][c] == 0:
            return True
        if nc == c - 1 and self.generator.east_wall[nr][c] == 0:
            return True
        
        return False
    
    def step(self) -> bool:
        """Solve one step. Returns True if complete."""
        if self.solving_complete:
            return True
        
        # Check if at exit
        if self.current_row == self.rows - 1 and self.current_col == self.cols - 1:
            self.path.append((self.current_row, self.current_col))
            self.solving_complete = True
            return True
        
        # Try adjacent cells
        moves = [(self.current_row - 1, self.current_col),
                 (self.current_row, self.current_col + 1),
                 (self.current_row + 1, self.current_col),
                 (self.current_row, self.current_col - 1)]
        
        possible_moves = []
        for nr, nc in moves:
            if self.can_move(self.current_row, self.current_col, nr, nc):
                if not self.visited[nr][nc]:
                    possible_moves.append((nr, nc))
        
        if possible_moves:
            nr, nc = random.choice(possible_moves)
            self.visited[nr][nc] = True
            self.stack.append((self.current_row, self.current_col))
            self.path.append((self.current_row, self.current_col))
            self.current_row, self.current_col = nr, nc
        elif self.stack:
            self.dead_ends.add((self.current_row, self.current_col))
            self.current_row, self.current_col = self.stack.pop()
        else:
            self.solving_complete = True
            return True
        
        return False


class MazeGame:
    """Main maze game."""
    
    def __init__(self, config: MazeConfig):
        """Initialize game."""
        self.config = config
        self.generator = MazeGenerator(config.rows, config.cols, config.cycle_probability)
        self.solver = None
        self.state = GameState.IDLE
        self.speed_multiplier = 1.0
        self.gen_steps = 0
        self.solve_steps = 0
        self.start_time = time.time()
        
    def restart(self):
        """Restart maze."""
        self.generator = MazeGenerator(self.config.rows, self.config.cols, self.config.cycle_probability)
        self.solver = None
        self.state = GameState.IDLE
        self.gen_steps = 0
        self.solve_steps = 0
        self.start_time = time.time()
    
    def start_generation(self):
        """Start generation."""
        if self.state == GameState.IDLE:
            self.state = GameState.GENERATING
    
    def start_solving(self):
        """Start solving."""
        if self.state == GameState.GENERATING and self.generator.generation_complete:
            self.solver = MazeSolver(self.generator)
            self.state = GameState.SOLVING
    
    def step(self):
        """Game step."""
        if self.state == GameState.GENERATING:
            for _ in range(self.config.generation_speed):
                if self.generator.step():
                    self.start_solving()
                    break
            self.gen_steps += 1
        
        elif self.state == GameState.SOLVING:
            for _ in range(self.config.solving_speed):
                if self.solver.step():
                    self.state = GameState.COMPLETED
                    break
            self.solve_steps += 1
    
    def pause(self):
        """Pause game."""
        if self.state in [GameState.GENERATING, GameState.SOLVING]:
            self.state = GameState.PAUSED
    
    def resume(self):
        """Resume game."""
        if self.state == GameState.PAUSED:
            self.state = GameState.GENERATING if self.gen_steps > 0 else GameState.IDLE
    
    def new_maze(self, rows: int, cols: int):
        """Generate new maze."""
        self.config.rows = rows
        self.config.cols = cols
        self.restart()


class MazeUI:
    """Premium GUI with Tkinter and Pygame."""
    
    def __init__(self, game: MazeGame):
        """Initialize UI."""
        import tkinter as tk
        from tkinter import ttk
        
        self.game = game
        self.root = tk.Tk()
        self.root.title("Maze Generator & Solver - Premium")
        self.root.geometry("1400x750")
        self.root.configure(bg="#0d1117")
        
        # Color scheme
        self.BG = "#0d1117"
        self.FG = "#e6edf3"
        self.ACCENT = "#00d9ff"
        self.BTN_BG = "#161b22"
        self.BTN_HOVER = "#0f3460"
        self.BTN_ACTIVE = "#00d9ff"
        
        pygame.init()
        self.setup_pygame_surface()
        self.setup_ui()
        self.running = True
        
    def setup_pygame_surface(self):
        """Setup pygame surface for maze rendering."""
        import tkinter as tk
        self.pygame_surface = pygame.Surface((700, 700))
        self.cell_pixel_size = 700 / self.game.config.cols
        
    def setup_ui(self):
        """Create premium UI layout."""
        import tkinter as tk
        
        # Main container
        main_frame = tk.Frame(self.root, bg=self.BG)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Left side - Maze display
        left_frame = tk.Frame(main_frame, bg=self.BTN_BG, relief=tk.FLAT, bd=1)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))
        
        tk.Label(left_frame, text="MAZE VISUALIZATION", font=("Arial", 11, "bold"), 
                fg=self.ACCENT, bg=self.BTN_BG).pack(pady=10)
        
        self.canvas = tk.Canvas(left_frame, bg="#000000", width=700, height=700, 
                               highlightthickness=1, highlightbackground=self.ACCENT)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Right side - Controls
        right_frame = tk.Frame(main_frame, bg=self.BG, width=250)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10)
        right_frame.pack_propagate(False)
        
        # Title
        tk.Label(right_frame, text="CONTROLS", font=("Arial", 14, "bold"), 
                fg=self.ACCENT, bg=self.BG).pack(pady=(0, 15))
        
        # Status box
        self.status_frame = tk.Frame(right_frame, bg=self.BTN_BG, relief=tk.FLAT, bd=1)
        self.status_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.status_text = tk.Label(self.status_frame, 
                                   text="State: IDLE\nRows: 20 | Cols: 30\nSpeed: 1.0x", 
                                   font=("Courier", 9), fg=self.ACCENT, bg=self.BTN_BG, 
                                   justify=tk.LEFT)
        self.status_text.pack(padx=10, pady=10)
        
        # Main control buttons
        self.create_section_label(right_frame, "GENERATION")
        self.create_button(right_frame, "Generate", self.on_generate, "#00ff88")
        self.create_button(right_frame, "Solve", self.on_solve, "#00d9ff")
        self.create_button(right_frame, "Restart", self.on_restart, "#ffaa00")
        self.create_button(right_frame, "Pause/Resume", self.on_pause, "#ff6b6b")
        
        # Difficulty section
        self.create_section_label(right_frame, "DIFFICULTY", top_pad=15)
        diff_frame = tk.Frame(right_frame, bg=self.BG)
        diff_frame.pack(fill=tk.X, pady=(5, 10))
        
        difficulties = [
            ("Easy\n10×15", 10, 15, "#4ade80"),
            ("Medium\n20×30", 20, 30, "#60a5fa"),
            ("Hard\n30×40", 30, 40, "#f97316"),
            ("Extreme\n50×60", 50, 60, "#ef4444"),
        ]
        
        for text, rows, cols, color in difficulties:
            btn = tk.Button(diff_frame, text=text, font=("Arial", 8, "bold"),
                           fg="#ffffff", bg=color, activebackground=self.lighten_color(color),
                           command=lambda r=rows, c=cols: self.on_difficulty(r, c),
                           relief=tk.FLAT, padx=5, pady=5, cursor="hand2", bd=0)
            btn.pack(side=tk.LEFT, padx=2, fill=tk.BOTH, expand=True)
        
        # Speed section
        self.create_section_label(right_frame, "SPEED", top_pad=15)
        speed_frame = tk.Frame(right_frame, bg=self.BG)
        speed_frame.pack(fill=tk.X, pady=(5, 10))
        
        tk.Button(speed_frame, text="◀ Slower", font=("Arial", 9, "bold"),
                 fg="#ffffff", bg=self.BTN_BG, activebackground=self.BTN_HOVER,
                 command=self.on_speed_down, relief=tk.FLAT, padx=8, pady=6, 
                 cursor="hand2", bd=0).pack(side=tk.LEFT, padx=2, fill=tk.BOTH, expand=True)
        
        tk.Button(speed_frame, text="Faster ▶", font=("Arial", 9, "bold"),
                 fg="#ffffff", bg=self.BTN_BG, activebackground=self.BTN_HOVER,
                 command=self.on_speed_up, relief=tk.FLAT, padx=8, pady=6, 
                 cursor="hand2", bd=0).pack(side=tk.LEFT, padx=2, fill=tk.BOTH, expand=True)
        
        # Quit button
        tk.Button(right_frame, text="QUIT", font=("Arial", 11, "bold"),
                 fg="#ffffff", bg="#8b0000", activebackground="#b00000",
                 command=self.on_quit, relief=tk.FLAT, padx=20, pady=12, 
                 cursor="hand2", bd=0).pack(fill=tk.X, pady=(20, 0))
    
    def create_section_label(self, parent, text, top_pad=10):
        """Create section label."""
        import tkinter as tk
        tk.Label(parent, text=text, font=("Arial", 10, "bold"), 
                fg=self.ACCENT, bg=self.BG).pack(pady=(top_pad, 8))
    
    def create_button(self, parent, text, command, color):
        """Create premium button."""
        import tkinter as tk
        btn = tk.Button(parent, text=text, font=("Arial", 10, "bold"),
                       fg="#ffffff", bg=color, activebackground=self.lighten_color(color),
                       command=command, relief=tk.FLAT, padx=15, pady=10, 
                       cursor="hand2", bd=0)
        btn.pack(fill=tk.X, pady=5)
        return btn
    
    @staticmethod
    def lighten_color(hex_color):
        """Lighten a hex color."""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        new_rgb = tuple(min(255, c + 40) for c in rgb)
        return '#{:02x}{:02x}{:02x}'.format(*new_rgb)
    
    def on_generate(self):
        """Generate button clicked."""
        self.game.start_generation()
        self.update_status()
        self.draw()
    
    def on_solve(self):
        """Solve button clicked."""
        if self.game.state == GameState.IDLE:
            self.game.start_generation()
        self.game.start_solving()
        self.update_status()
        self.draw()
    
    def on_restart(self):
        """Restart button clicked."""
        self.game.restart()
        self.canvas.delete("all")
        self.update_status()
    
    def on_pause(self):
        """Pause button clicked."""
        if self.game.state in [GameState.GENERATING, GameState.SOLVING]:
            self.game.pause()
        elif self.game.state == GameState.PAUSED:
            self.game.resume()
        self.update_status()
    
    def on_difficulty(self, rows, cols):
        """Difficulty button clicked."""
        self.game.new_maze(rows, cols)
        self.canvas.delete("all")
        self.update_status()
    
    def on_speed_up(self):
        """Speed up button clicked."""
        self.game.speed_multiplier = min(3.0, self.game.speed_multiplier + 0.2)
        self.update_status()
    
    def on_speed_down(self):
        """Speed down button clicked."""
        self.game.speed_multiplier = max(0.1, self.game.speed_multiplier - 0.2)
        self.update_status()
    
    def on_quit(self):
        """Quit button clicked."""
        self.running = False
        self.root.quit()
    
    def update_status(self):
        """Update status display."""
        status = f"State: {self.game.state.value}\n"
        status += f"Rows: {self.game.config.rows} | Cols: {self.game.config.cols}\n"
        status += f"Speed: {self.game.speed_multiplier:.1f}x"
        self.status_text.config(text=status)
    
    def draw(self):
        """Draw maze on canvas with professional rendering."""
        self.canvas.delete("all")
        gen = self.game.generator
        
        # Draw background
        self.canvas.create_rectangle(0, 0, 700, 700, fill="#000000", outline="")
        
        cell_size = self.cell_pixel_size
        
        # Draw all cells first
        for r in range(gen.rows):
            for c in range(gen.cols):
                x1 = c * cell_size
                y1 = r * cell_size
                x2 = x1 + cell_size
                y2 = y1 + cell_size
                
                # Cell background
                if gen.visited[r][c]:
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill="#0a1628", outline="")
                else:
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill="#000000", outline="")
        
        # Draw walls with proper rendering
        wall_color = "#00d9ff"
        wall_thick = 2
        
        for r in range(gen.rows):
            for c in range(gen.cols):
                x1 = c * cell_size
                y1 = r * cell_size
                x2 = x1 + cell_size
                y2 = y1 + cell_size
                
                # North wall
                if gen.north_wall[r][c]:
                    self.canvas.create_line(x1, y1, x2, y1, fill=wall_color, width=wall_thick)
                
                # East wall
                if gen.east_wall[r][c]:
                    self.canvas.create_line(x2, y1, x2, y2, fill=wall_color, width=wall_thick)
                
                # South wall (border)
                if r == gen.rows - 1:
                    self.canvas.create_line(x1, y2, x2, y2, fill=wall_color, width=wall_thick)
                
                # West wall (border)
                if c == 0:
                    self.canvas.create_line(x1, y1, x1, y2, fill=wall_color, width=wall_thick)
        
        # Draw right and bottom border
        self.canvas.create_line(gen.cols * cell_size, 0, gen.cols * cell_size, gen.rows * cell_size, 
                               fill=wall_color, width=wall_thick)
        self.canvas.create_line(0, gen.rows * cell_size, gen.cols * cell_size, gen.rows * cell_size, 
                               fill=wall_color, width=wall_thick)
        
        # Draw solver path (blue) - show as squares
        if self.game.solver:
            for pr, pc in self.game.solver.path:
                x1 = pc * cell_size + 3
                y1 = pr * cell_size + 3
                x2 = x1 + cell_size - 6
                y2 = y1 + cell_size - 6
                self.canvas.create_rectangle(x1, y1, x2, y2, fill="#4169ff", outline="")
        
        # Draw dead ends (orange) - show as squares
        if self.game.solver:
            for pr, pc in self.game.solver.dead_ends:
                x1 = pc * cell_size + 2
                y1 = pr * cell_size + 2
                x2 = x1 + cell_size - 4
                y2 = y1 + cell_size - 4
                self.canvas.create_rectangle(x1, y1, x2, y2, fill="#ff8800", outline="")
        
        # Draw generation mouse (green dot)
        if self.game.state in [GameState.GENERATING, GameState.PAUSED]:
            r, c = gen.current_row, gen.current_col
            x = c * cell_size + cell_size / 2
            y = r * cell_size + cell_size / 2
            self.canvas.create_oval(x - 5, y - 5, x + 5, y + 5, fill="#00ff88", outline="#00ff88", width=2)
        
        # Draw solver mouse (red dot)
        if self.game.solver and self.game.state in [GameState.SOLVING, GameState.COMPLETED, GameState.PAUSED]:
            x = self.game.solver.current_col * cell_size + cell_size / 2
            y = self.game.solver.current_row * cell_size + cell_size / 2
            self.canvas.create_oval(x - 5, y - 5, x + 5, y + 5, fill="#ff6b6b", outline="#ff6b6b", width=2)
        
        # Calculate frame delay based on speed multiplier
        delay = max(5, int(50 / self.game.speed_multiplier))
        self.root.after(delay, self.update_game)
    
    def update_game(self):
        """Update game state without freezing UI."""
        if self.game.state not in [GameState.IDLE, GameState.PAUSED]:
            self.game.step()
        
        self.update_status()
        self.draw()
    
    def run(self):
        """Start UI loop."""
        self.draw()
        self.root.mainloop()


def main():
    """Main entry point."""
    import tkinter as tk
    
    config = MazeConfig(rows=20, cols=30)
    
    if not config.validate():
        print("ERROR: Invalid configuration")
        return
    
    game = MazeGame(config)
    ui = MazeUI(game)
    ui.run()


if __name__ == "__main__":
    main()
