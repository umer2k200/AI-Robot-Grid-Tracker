import random
import heapq
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox


GRID_ROWS = 10
GRID_COLS = 12
FREE_SPACE = '*'
STATIC_OBSTACLE =  'S'
DYNAMIC_OBSTACLE = 'D1'
FAST_DYNAMIC_OBSTACLE = 'D2'
ROBOT = 'R'
ITEM = 'I'
ITEM_COUNT = 3
STATIC_OBSTACLE_COUNT = 3
DYNAMIC_OBSTACLE_COUNT = 1
FAST_DYNAMIC_OBSTACLE_COUNT = 2
CELL_SIZE = 45 

class GridNavigationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Efficient Warehouse Navigation")

        self.robot_image = tk.PhotoImage(file="robot3.png")
        self.collision_count = 0

        self.grid, self.robot_position, self.static_positions, self.dynamic_positions, self.fast_dynamic_positions,self.item_positions, self.fast_obstacle_states = initialize_grid(
            GRID_ROWS, GRID_COLS, STATIC_OBSTACLE_COUNT, DYNAMIC_OBSTACLE_COUNT, ITEM_COUNT, FAST_DYNAMIC_OBSTACLE_COUNT
        )
        self.collected_items = 0
        self.collected_path = []
        self.steps_taken = 0
        self.next_item = None

        self.canvas = tk.Canvas(root, width=GRID_COLS * CELL_SIZE, height=GRID_ROWS * CELL_SIZE, bg="white")
        self.canvas.grid(row=0, column=0, columnspan=4)

        ttk.Button(root, text="Start", command=self.start_simulation).grid(row=1, column=0, sticky="ew")
        ttk.Button(root, text="Reset", command=self.reset_simulation).grid(row=1, column=1, sticky="ew")
        ttk.Button(root, text="Pause", command=self.pause_simulation).grid(row=1, column=2, sticky="ew")
        ttk.Button(root, text="Quit", command=root.quit).grid(row=1, column=3, sticky="ew")

        self.info_label = ttk.Label(root, text="Items Collected: 0 | Steps: 0 | Collisions: 0 | Items: ", anchor="center")
        self.info_label.grid(row=2, column=0, columnspan=4, pady=10)

        self.update_canvas()
        self.simulation_running = False
       

    def update_canvas(self):
        self.canvas.delete("all")
        for row in range(len(self.grid)):
            for col in range(len(self.grid[0])):
                x0, y0 = col * CELL_SIZE, row * CELL_SIZE
                x1, y1 = x0 + CELL_SIZE, y0 + CELL_SIZE
                if self.grid[row][col] == FREE_SPACE:
                    color = "white"
                elif self.grid[row][col] == STATIC_OBSTACLE:
                    color = "gray"
                elif self.grid[row][col] == DYNAMIC_OBSTACLE:
                    color = "red"
                elif self.grid[row][col] == FAST_DYNAMIC_OBSTACLE:
                    color = "pink"
                elif self.grid[row][col] == ROBOT:
                    self.canvas.create_image(x0 + CELL_SIZE // 2, y0 + CELL_SIZE // 1.5, image=self.robot_image)
                    continue 
                elif self.grid[row][col] == ITEM:
                    color = "green"
                if self.grid[row][col] != ROBOT:
                    self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="black")
        #--------
        for item in self.item_positions:
            self.canvas.create_text(
                item[1] * CELL_SIZE + CELL_SIZE // 2, item[0] * CELL_SIZE + CELL_SIZE // 2, text="I", font=("Arial", 14)
            )
        for dynamic in self.dynamic_positions:
            self.canvas.create_text(
                dynamic[1] * CELL_SIZE + CELL_SIZE // 2, dynamic[0] * CELL_SIZE + CELL_SIZE // 2, text="D1", font=("Arial", 14)
            )
        for fast_dynamic in self.fast_dynamic_positions:
            self.canvas.create_text(
                fast_dynamic[1] * CELL_SIZE + CELL_SIZE // 2, fast_dynamic[0] * CELL_SIZE + CELL_SIZE // 2, text="D2", font=("Arial", 14)
            )
        for static in self.static_positions:
            self.canvas.create_text(
                static[1] * CELL_SIZE + CELL_SIZE // 2, static[0] * CELL_SIZE + CELL_SIZE // 2, text="S", font=("Arial", 14)
            )
        #------
        for i in range(GRID_ROWS):
            self.canvas.create_text(-15, i * CELL_SIZE + CELL_SIZE // 2, text=str(i), anchor="e", font=("Arial", 10))
        for j in range(GRID_COLS):
            self.canvas.create_text(j * CELL_SIZE + CELL_SIZE // 2, -15, text=str(j), anchor="s", font=("Arial", 10))
        if self.next_item:
            x0, y0 = self.next_item[1] * CELL_SIZE, self.next_item[0] * CELL_SIZE
            x1, y1 = x0 + CELL_SIZE, y0 + CELL_SIZE
            self.canvas.create_rectangle(x0, y0, x1, y1, fill="yellow", outline="black")
    
    def start_simulation(self):
        if not self.simulation_running:
            self.simulation_running = True
            self.collect_all_items()

    def pause_simulation(self):
        self.simulation_running = False

    def reset_simulation(self):
        self.simulation_running = False
        self.grid, self.robot_position, self.static_positions, self.dynamic_positions, self.fast_dynamic_positions, self.item_positions, self.fast_obstacle_states = initialize_grid(
            GRID_ROWS, GRID_COLS, STATIC_OBSTACLE_COUNT, DYNAMIC_OBSTACLE_COUNT, ITEM_COUNT, FAST_DYNAMIC_OBSTACLE_COUNT
        )
        self.collected_items = 0
        self.steps_taken = 0
        self.collected_path = []
        self.collision_count = 0
        self.update_info()
        self.update_canvas()

    def update_info(self):
        item_positions_str = ", ".join([f"({x}, {y})" for x, y in self.item_positions])
        self.info_label.config(
            text=(
                f"Items Collected: {self.collected_items} | Steps: {self.steps_taken} "
                f"| Collisions: {self.collision_count} | Items: {item_positions_str}"
            )
        )


    def collect_all_items(self):
        if not self.item_positions or not self.simulation_running:
            messagebox.showinfo("Simulation Complete", "All items have been collected!")
            self.simulation_running = False
            self.next_item = None
            return

        self.item_positions.sort(key=lambda item: heuristic(self.robot_position, item))
        self.next_item = self.item_positions[0]
        next_item = self.item_positions.pop(0)
        path_to_item = a_star(self.grid, self.robot_position, next_item)

        if not path_to_item:
            messagebox.showinfo("Navigation Alert", f"Cannot reach item at {next_item}.")
            return

        def move_step(step_index):
            if not self.simulation_running:
                return

            if step_index < len(path_to_item):
                self.grid[self.robot_position[0]][self.robot_position[1]] = FREE_SPACE
                self.robot_position = path_to_item[step_index]
                
                # Check for collision
                if self.robot_position in self.dynamic_positions or \
                self.robot_position in self.fast_dynamic_positions or \
                self.robot_position in self.static_positions:
                    self.collision_count += 1
                    messagebox.showwarning("Collision Detected", "The robot collided with an obstacle!")
                
                self.grid[self.robot_position[0]][self.robot_position[1]] = ROBOT
                
                self.dynamic_positions, self.fast_dynamic_positions, self.fast_obstacle_states, self.collision_count = move_dynamic_obstacles(
                    self.grid, self.dynamic_positions, self.fast_dynamic_positions, self.fast_obstacle_states, self.robot_position,self.collision_count
                )

                self.update_canvas()
                self.steps_taken += 1
                self.update_info()
                self.canvas.after(500, move_step, step_index + 1)
            else:
                self.collected_items += 1
                #messagebox.showinfo("Item Collected", "The robot has collected an item!")
                self.update_info()
                self.collect_all_items()

        move_step(0)

def initialize_grid(rows, cols, static_count, dynamic_count, item_count, fast_dynamic_count):
    grid = [[FREE_SPACE for _ in range(cols)] for _ in range(rows)]
    
    # Place static obstacles
    static_positions = []
    for _ in range(static_count):
        while True:
            x, y = random.randint(0, rows-1), random.randint(0, cols-1)
            if grid[x][y] == FREE_SPACE:
                grid[x][y] = STATIC_OBSTACLE
                static_positions.append((x, y))
                break

    # Place dynamic obstacles
    dynamic_positions = []
    for _ in range(dynamic_count):
        while True:
            x, y = random.randint(0, rows-1), random.randint(0, cols-1)
            if grid[x][y] == FREE_SPACE:
                grid[x][y] = DYNAMIC_OBSTACLE
                dynamic_positions.append((x, y))
                break
    
    # Place fast dynamic obstacles
    fast_dynamic_positions = []
    for _ in range(fast_dynamic_count):
        while True:
            x, y = random.randint(0, rows-1), random.randint(0, cols-1)
            if grid[x][y] == FREE_SPACE:
                grid[x][y] = FAST_DYNAMIC_OBSTACLE
                fast_dynamic_positions.append((x, y))
                break
    
    # Place items
    item_positions = []
    for _ in range(item_count):
        while True:
            x, y = random.randint(0, rows-1), random.randint(0, cols-1)
            if grid[x][y] == FREE_SPACE:
                grid[x][y] = ITEM
                item_positions.append((x, y))
                break
    
    # Place robot
    while True:
        rx, ry = random.randint(0, rows-1), random.randint(0, cols-1)
        if grid[rx][ry] == FREE_SPACE:
            grid[rx][ry] = ROBOT
            break
    
    fast_obstacle_states = [True] * fast_dynamic_count

    return grid, (rx, ry), static_positions, dynamic_positions, fast_dynamic_positions,item_positions, fast_obstacle_states


def move_dynamic_obstacles(grid, dynamic_positions, fast_dynamic_positions, fast_obstacle_states,robot_position,collision_count):
    def move_obstacle(grid, position,obstacle_type):
        rows, cols = len(grid), len(grid[0])
        x, y = position
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        random.shuffle(directions)
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < rows and 0 <= ny < cols and grid[nx][ny] == FREE_SPACE:
                grid[x][y] = FREE_SPACE
                grid[nx][ny] = obstacle_type
                return nx, ny
        return x, y

    # def move_fast_obstacle(grid, position):
    #     new_position = move_obstacle(grid, position)
    #     return move_obstacle(grid, new_position)

    new_dynamic_positions = []
    for position in dynamic_positions:
        new_dynamic_positions.append(move_obstacle(grid, position,DYNAMIC_OBSTACLE))

    new_fast_dynamic_positions = []
    for idx, position in enumerate(fast_dynamic_positions):
        if fast_obstacle_states[idx]:  
            new_position = move_obstacle(grid, position, FAST_DYNAMIC_OBSTACLE)
            fast_obstacle_states[idx] = False  
        else:
            new_position = position
            fast_obstacle_states[idx] = True 
        new_fast_dynamic_positions.append(new_position)
    return new_dynamic_positions, new_fast_dynamic_positions, fast_obstacle_states,collision_count


def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def a_star(grid, start, goal):
    rows, cols = len(grid), len(grid[0])
    open_set = []
    heapq.heappush(open_set, (0, start))
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path

        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor = (current[0] + dx, current[1] + dy)
            if 0 <= neighbor[0] < rows and 0 <= neighbor[1] < cols:
                if grid[neighbor[0]][neighbor[1]] not in [STATIC_OBSTACLE, DYNAMIC_OBSTACLE]:
                    tentative_g_score = g_score[current] + 1
                    if tentative_g_score < g_score.get(neighbor, float('inf')):
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g_score
                        f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
    return None

if __name__ == "__main__":
    root = tk.Tk()
    app = GridNavigationApp(root)
    root.mainloop()
