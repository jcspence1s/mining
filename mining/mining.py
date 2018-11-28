import random
import tkinter
import heapq
import collections


class Zerg:
    returns = list()            # List of zergs for return
    starting_locations = dict()     # Dict of starting locations by map id
    landing_clear = dict()      # Dict of bools signaling clear landing pads
    deploying = dict()          # Dict of zergs being deployed by id
    map_graphs = dict()         # Dict of graph objects by map id
    map_display = dict()   # Dict of frames for map displays
    map_minerals = dict()       # Dict of minerals per map by id

    def __init__(self, health):
        self.health = health

    def action(self):
        pass

'''
    Graph, PriorityQueue, heuristic, and a_star_search was implemented
    based on the following website. Code was modified in places to fit
    the needs of the program.

    Source:
    https://www.redblobgames.com/pathfinding/a-star/implementation.html
'''


class Graph():
    def __init__(self):
        self.width = 200    # Twice as big as needed to accomodate odd coords
        self.height = 200
        self.weights = {}   # Dict of weights for nodes, Acid = 4, ground = 1
        self.walls = []     # List of walls to avoid
        self.acid = []      # List of acid tiles for weights
        self.visited = set()    # Set of visited tiles
        self.unvisited = list()  # List of visitalbe tiles yet to be explored

    def cost(self, from_node, to_node):
        weight = 1
        if to_node in self.acid:
            weight = 4
        return self.weights.get(to_node, weight)

    def in_bounds(self, id):
        (x, y) = id
        return 0 <= x < self.width and 0 <= y < self.height

    def passable(self, id):
        return id not in self.walls

    def neighbors(self, id):
        (x, y) = id
        results = [(x+1, y), (x, y-1), (x-1, y), (x, y+1)]
        if (x+y) % 2 == 0:
            results.reverse()
        results = filter(self.in_bounds, results)
        results = filter(self.passable, results)
        return results

    def __str__(self):
        output = ""
        for edge in self.edges:
            output += str(edge)
        return output


class PriorityQueue:
    def __init__(self):
        self.elements = []

    def empty(self):
        return len(self.elements) == 0

    def put(self, item, priority):
        heapq.heappush(self.elements, (priority, item))

    def get(self):
        return heapq.heappop(self.elements)[1]


def heuristic(a, b):
    (x1, y1) = a
    (x2, y2) = b
    return abs(x1 - x2) + abs(y1 + y2)


def a_star_search(graph, start, goal):
    '''
    Combined a_star_search and reconstruct path from above source
    '''
    frontier = PriorityQueue()
    frontier.put(start, 0)
    came_from = {}
    cost_so_far = {}
    came_from[start] = None
    cost_so_far[start] = 0

    while not frontier.empty():
        current = frontier.get()

        if current == goal:
            break

        for next in graph.neighbors(current):
            new_cost = cost_so_far[current] + graph.cost(current, next)
            if next not in cost_so_far or new_cost < cost_so_far[next]:
                cost_so_far[next] = new_cost
                priority = new_cost + heuristic(goal, next)
                frontier.put(next, priority)
                came_from[next] = current

    current = goal
    path = []
    while current != start:
        path.append(current)
        current = came_from[current]
    path.append(start)
    path.reverse()
    return path


class Overlord(Zerg):
    def __init__(self, total_ticks, refined_minerals, dashboard=None):
        super().__init__(100)
        self.dashboard = dashboard      # Display object
        self.total_ticks = total_ticks  # Keeps track of ticks remaining
        self.maps = {}                  # Dict of maps by id
        self.drones = {}                # Dict of drones by id
        self.deploy = list()            # List of drones to deploy
        self.random_map_id = 0          # Which map to deploy to
        self.return_count = 0           # How many drones waiting for return
        self.map_dashboards = list()    # List of Tkinter windows for maps
        self.last_discovery = 0         # Variance for discovery

        screen_position = "300x200+{}+{}"   # Screen placement for map windows
        screen_x = 300
        screen_y = 500
        for x in range(3):  # Initializes the map windows
            self.map_dashboards.append(Dashboard(self.dashboard))
            self.map_dashboards[x].geometry(
                    screen_position.format(screen_x, screen_y))
            screen_x += 300

            dash_title = "MAP {}".format(x)
            self.map_dashboards[x].title(dash_title)
            self.map_dashboards[x].log.forget()
            del self.map_dashboards[x].log
            self.map_dashboards[x].log = tkinter.Text(
                    self.map_dashboards[x], height=10,  width=30)
            self.map_dashboards[x].log.grid(row=110, column=0, columnspan=100)
        # TODO make logic to create zerg horde
        drone_count = int(refined_minerals / 9)
        for value in range(drone_count):
            z = Drone()
            self.drones[id(z)] = z
            self.deploy.append(id(z))

    def add_map(self, map_id, summary):
        self.maps[map_id] = summary
        Zerg.map_graphs[map_id] = Graph()
        width, height = 100, 100
        Zerg.map_display[map_id] = [[
            tkinter.Frame(
                self.map_dashboards[map_id], height=12, width=12, bg='black')
            for x in range(width)] for y in range(height)]

    def action(self):
        self.delete = []
        self.total_ticks -= 1
        for zerg in self.drones:
            drone = self.drones[zerg]
            self.get_drone_info(drone)
        for zerg in self.delete:
            self.drones.pop(zerg)
        if Zerg.returns:
            returning = Zerg.returns.pop()
            result = 'RETURN {}'.format(returning)
            if returning in self.drones:
                Zerg.landing_clear[self.drones[returning].map] = True
            self.deploy.append(returning)
            self.drones[returning].deployed = False
            self.return_count += 1
        elif self.deploy and self.total_ticks > 15:
            deploying = self.deploy.pop()
            if self.random_map_id not in Zerg.landing_clear:
                Zerg.landing_clear[self.random_map_id] = True
            if self.random_map_id not in Zerg.deploying:
                Zerg.deploying[self.random_map_id] = False
            if Zerg.landing_clear[self.random_map_id] is True:
                result = 'DEPLOY {} {}'.format(deploying, self.random_map_id)
                self.drones[deploying].map = self.random_map_id
                if self.random_map_id < 2:
                    self.random_map_id += 1
                else:
                    self.random_map_id = 0
                self.drones[deploying].deployed = True
                Zerg.deploying[self.random_map_id] = True
            else:
                self.deploy.append(deploying)
                result = "NONE"
        else:
            result = "NONE"
        self.update_dashboard(self.dashboard, result)
        return result

    def update_dashboard(self, dashboard, result):
        for dash in range(3):
            self.map_dashboards[dash].log.config(state=tkinter.NORMAL)
            self.map_dashboards[dash].log.delete('1.0', tkinter.END)
            self.map_dashboards[dash].log.config(state=tkinter.DISABLED)
        for drone_id, drone in self.drones.items():
            if drone.deployed is True:
                drone_string = "{}({}): {}".format(
                        drone_id, drone.map, list(drone.commands))
                self.map_dashboards[drone.map].log.config(state=tkinter.NORMAL)
                self.map_dashboards[drone.map].log.insert(
                        tkinter.END, drone_string)
                self.map_dashboards[drone.map].log.insert(tkinter.END, "\n")
                self.map_dashboards[drone.map].log.see(tkinter.END)
                self.map_dashboards[drone.map].log.config(
                        state=tkinter.DISABLED)
                self.map_dashboards[drone.map].log.grid()

        self.dashboard.log.config(state=tkinter.NORMAL)
        self.dashboard.log.delete('1.0', tkinter.END)
        self.dashboard.log.insert(tkinter.END, result)
        self.dashboard.log.insert(tkinter.END, "\n")
        self.dashboard.log.see(tkinter.END)
        self.dashboard.log.config(state=tkinter.DISABLED)

    def update_display(self, drone, north, south, east, west):
        x_coord = drone.context.x
        y_coord = drone.context.y
        print_north = Zerg.map_display[drone.map][north[1]][north[0]]
        print_south = Zerg.map_display[drone.map][south[1]][south[0]]
        print_east = Zerg.map_display[drone.map][east[1]][east[0]]
        print_west = Zerg.map_display[drone.map][west[1]][west[0]]
        print_zerg = Zerg.map_display[drone.map][y_coord][x_coord]

        if drone.context.north == "#":
            print_north.config(bg='gray50')
        elif drone.context.north == "~":
            print_north.config(bg='lawn green')
        elif drone.context.north == "*":
            print_north.config(bg='blue')
        elif drone.context.north == "_":
            print_north.config(bg='gold')
        elif drone.context.north == " ":
            print_north.config(bg='grey60')

        if drone.context.south == "#":
            print_south.config(bg='gray50')
        elif drone.context.south == "~":
            print_south.config(bg='lawn green')
        elif drone.context.south == "*":
            print_south.config(bg='blue')
        elif drone.context.south == "_":
            print_south.config(bg='gold')
        elif drone.context.south == " ":
            print_south.config(bg='grey60')

        if drone.context.east == "#":
            print_east.config(bg='gray50')
        elif drone.context.east == "~":
            print_east.config(bg='lawn green')
        elif drone.context.east == "*":
            print_east.config(bg='blue')
        elif drone.context.east == "_":
            print_east.config(bg='gold')
        elif drone.context.west == " ":
            print_east.config(bg='grey60')

        if drone.context.west == "#":
            print_west.config(bg='gray50')
        elif drone.context.west == "~":
            print_west.config(bg='lawn green')
        elif drone.context.west == "*":
            print_west.config(bg='blue')
        elif drone.context.west == "_":
            print_west.config(bg='gold')
        elif drone.context.west == " ":
            print_west.config(bg='grey60')

        print_north.grid(row=north[1], column=north[0], sticky='NW')
        print_south.grid(row=south[1], column=south[0], sticky='NW')
        print_east.grid(row=east[1], column=east[0], sticky='NW')
        print_west.grid(row=west[1], column=west[0], sticky='NW')
        print_zerg.config(bg='magenta2')

    def get_drone_info(self, drone):
        if drone.context:
            path = None
            tile = (drone.context.x, drone.context.y)
            north = (drone.context.x, int(drone.context.y) + 1)
            south = (drone.context.x, int(drone.context.y) - 1)
            east = (int(drone.context.x) + 1, drone.context.y)
            west = (int(drone.context.x) - 1, drone.context.y)
            Zerg.map_graphs[drone.map].visited.add(tile)
            if drone.last_tile == tile:
                drone.commands = dict()
            else:
                drone.last_tile = tile
            allowed = " ~#"
            if drone.context.north == "*":
                Zerg.map_minerals.update({drone.map: north})
            if drone.context.south == "*":
                Zerg.map_minerals.update({drone.map: south})
            if drone.context.east == "*":
                Zerg.map_minerals.update({drone.map: east})
            if drone.context.west == "*":
                Zerg.map_minerals.update({drone.map: west})

            if drone.context.north == "#":
                Zerg.map_graphs[drone.map].walls.append(north)
            if drone.context.south == "#":
                Zerg.map_graphs[drone.map].walls.append(south)
            if drone.context.east == "#":
                Zerg.map_graphs[drone.map].walls.append(east)
            if drone.context.west == "#":
                Zerg.map_graphs[drone.map].walls.append(west)

            if drone.context.north == "~":
                Zerg.map_graphs[drone.map].acid.append(north)
            if drone.context.south == "~":
                Zerg.map_graphs[drone.map].acid.append(south)
            if drone.context.east == "~":
                Zerg.map_graphs[drone.map].acid.append(east)
            if drone.context.west == "~":
                Zerg.map_graphs[drone.map].acid.append(west)

            if drone.context.north != "#" and \
                    north not in Zerg.map_graphs[drone.map].visited:
                Zerg.map_graphs[drone.map].unvisited.append(north)
            if drone.context.south != "#" and \
                    south not in Zerg.map_graphs[drone.map].visited:
                Zerg.map_graphs[drone.map].unvisited.append(south)
            if drone.context.east != "#" and \
                    east not in Zerg.map_graphs[drone.map].visited:
                Zerg.map_graphs[drone.map].unvisited.append(east)
            if drone.context.west != "#" and \
                    west not in Zerg.map_graphs[drone.map].visited:
                Zerg.map_graphs[drone.map].unvisited.append(west)

            self.update_display(drone, north, south, east, west)
            Zerg.map_graphs[drone.map].unvisited = sorted(
                    list(set(Zerg.map_graphs[drone.map].unvisited).difference(
                        Zerg.map_graphs[drone.map].visited)))
            if drone.map in Zerg.map_minerals and Zerg.map_minerals[drone.map]:
                path = a_star_search(
                        Zerg.map_graphs[drone.map], tile,
                        Zerg.map_minerals[drone.map])
                if tile == path[0]:
                    path.pop(0)
            if drone.commands:
                outdated = list()
                for key in drone.commands:
                    if drone.last_tile != tile:
                        outdated.append(key)
                for item in outdated:
                    drone.commands.pop(item)
            if (not drone.commands and drone.carry > 7) or \
                    ('Return' not in drone.commands and self.total_ticks < 25):
                path = a_star_search(
                        Zerg.map_graphs[drone.map], tile,
                        Zerg.starting_locations[drone.map])
                if tile == path[0]:
                    path.pop(0)
                drone.commands.update({"Return": path})
            elif not drone.commands and path and drone.carry < 10:
                if Zerg.map_minerals[drone.map] in \
                        Zerg.map_graphs[drone.map].visited:
                    Zerg.map_minerals.pop(drone.map)
                else:
                    drone.commands.update({"Mine": path})
            elif 'Discover' not in drone.commands:
                if len(Zerg.map_graphs[drone.map].unvisited) > 0:
                    if self.last_discovery % 2 == 0:
                        new_tile = Zerg.map_graphs[drone.map].unvisited.pop(0)
                    else:
                        new_tile = Zerg.map_graphs[drone.map].unvisited.pop()
                    self.last_discovery += 1

                    path = a_star_search(
                            Zerg.map_graphs[drone.map], tile,
                            new_tile)
                    if tile == path[0]:
                        path.pop(0)
                    drone.commands.update({"Discover": path})
                else:
                    drone.commands.update({"Discover": None})
            if drone.health <= 0:
                self.delete.append(id(drone))


class Drone(Zerg):

    last_bias = 0

    def __init__(self):
        super().__init__(40)
        self.moves = 1
        self.last_tile = None
        self.capacity = 10
        self.health = 40
        self.carry = 0
        self.steps = 0
        self.map = -1
        self.context = None
        self.bias = Drone.last_bias % 4
        self.deployed = False
        Drone.last_bias += 1
        self.commands = dict()

    def get_direction(self, starting, ending):
        directions = {0: 'NORTH', 1: 'SOUTH', 2: 'EAST', 3: 'WEST'}
        if starting[0] < ending[0]:
            return directions[3]
        elif starting[0] > ending[0]:
            return directions[2]
        elif starting[1] < ending[1]:
            return directions[1]
        elif starting[1] > ending[1]:
            return directions[0]

    def action(self, context):
        directions = {0: 'NORTH', 1: 'SOUTH', 2: 'EAST', 3: 'WEST'}
        neighbors = {0: context.north, 1: context.south,
                     2: context.east, 3: context.west}
        if self.map not in Zerg.starting_locations:
            Zerg.starting_locations[self.map] = (context.x, context.y)
            Zerg.map_graphs[self.map].visited.add((context.x, context.y))
        if Zerg.starting_locations[self.map] == (context.x, context.y):
            Zerg.landing_clear[self.map] = False
        else:
            Zerg.landing_clear[self.map] = True
        self.steps += 1
        if self.steps % 25 == 0:
            self.bias = random.randint(0, 3)
        self.context = context
        if 'Return' not in self.commands:
            if context.north == "*" and self.carry < 10:
                self.commands = dict()
                self.carry += 1
                return directions.get(0)
            elif context.south == "*" and self.carry < 10:
                self.commands = dict()
                self.carry += 1
                return directions.get(1)
            elif context.east == "*" and self.carry < 10:
                self.commands = dict()
                self.carry += 1
                return directions.get(2)
            elif context.west == "*" and self.carry < 10:
                self.commands = dict()
                self.carry += 1
                return directions.get(3)
        if self.commands:
            if 'Mine' in self.commands:
                goto = "Center"
                if len(self.commands['Mine']) > 0:
                    goto = self.get_direction(
                        self.commands['Mine'].pop(0), (context.x, context.y))
                if self.commands and len(self.commands['Mine']) == 0:
                    self.commands.pop('Mine')
                else:
                    self.carry += 1

                return goto
            elif 'Return' in self.commands:
                goto = "Center"
                if len(self.commands['Return']) > 0:
                    to_tile = self.commands['Return'].pop(0)
                    if to_tile == (context.x, context.y)\
                            and len(self.commands['Return']) > 0:
                        to_tile = self.commands['Return'].pop(0)
                    goto = self.get_direction(to_tile, (context.x, context.y))
                if Zerg.starting_locations[self.map] == (context.x, context.y):
                    self.carry = 0
                    self.path_step = 0
                    Zerg.returns.append(id(self))
                    self.commands.pop('Return')

                return goto

            elif 'Discover' in self.commands:
                goto = "Center"
                if self.commands['Discover']:
                    to_tile = self.commands['Discover'].pop(0)
                    if to_tile == (context.x, context.y)\
                            and len(self.commands['Discover']) > 0:
                        to_tile = self.commands['Discover'].pop(0)
                    goto = self.get_direction(to_tile, (context.x, context.y))
                    return goto

                self.commands.pop('Discover')
                allowed = " ~"
                if self.bias == 0:
                    return Drone.north_bias(
                            self.last_tile, context, directions, allowed)
                elif self.bias == 1:
                    return Drone.south_bias(
                            self.last_tile, context, directions, allowed)
                elif self.bias == 2:
                    return Drone.east_bias(
                            self.last_tile, context, directions, allowed)
                elif self.bias == 3:
                    return Drone.west_bias(
                            self.last_tile, context, directions, allowed)

        return "CENTER"

    def north_bias(last_tile, context, directions, allowed):
        if context.north in allowed and context.y + 1 != last_tile[1]:
            return directions.get(0)
        elif context.east in allowed and context.x + 1 != last_tile[0]:
            return directions.get(2)
        elif context.south in allowed and context.y - 1 != last_tile[1]:
            return directions.get(1)
        elif context.west in allowed and context.x - 1 != last_tile[0]:
            return directions.get(3)
        else:
            return "CENTER"

    def south_bias(last_tile, context, directions, allowed):
        if context.south in allowed and context.y - 1 != last_tile[1]:
            return directions.get(1)
        elif context.west in allowed and context.x - 1 != last_tile[0]:
            return directions.get(3)
        elif context.north in allowed and context.y + 1 != last_tile[1]:
            return directions.get(0)
        elif context.east in allowed and context.x + 1 != last_tile[0]:
            return directions.get(2)
        else:
            return "CENTER"

    def east_bias(last_tile, context, directions, allowed):
        if context.east in allowed and context.x + 1 != last_tile[0]:
            return directions.get(2)
        elif context.north in allowed and context.y + 1 != last_tile[1]:
            return directions.get(0)
        elif context.west in allowed and context.x - 1 != last_tile[0]:
            return directions.get(3)
        elif context.south in allowed and context.y - 1 != last_tile[1]:
            return directions.get(1)
        else:
            return "CENTER"

    def west_bias(last_tile, context, directions, allowed):
        if context.west in allowed and context.x - 1 != last_tile[0]:
            return directions.get(3)
        elif context.south in allowed and context.y - 1 != last_tile[1]:
            return directions.get(1)
        elif context.east in allowed and context.x + 1 != last_tile[0]:
            return directions.get(2)
        elif context.north in allowed and context.y + 1 != last_tile[1]:
            return directions.get(0)
        else:
            return "CENTER"


class Dashboard(tkinter.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.geometry("300x200+300+200")
        self.title("Overlord's Dashboard")
        self.log = tkinter.Text(self, height=10,  width=30)
        self.log.pack()