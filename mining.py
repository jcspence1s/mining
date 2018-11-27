import random
import tkinter
import heapq
import collections


class Zerg:
    returns = list()
    starting_locations = dict()
    landing_clear = dict()
    deploying = dict()
    map_graphs = dict()
    map_minerals = dict()

    def __init__(self, health):
        self.health = health

    def action(self):
        pass


class Graph():
    def __init__(self):
        self.width = 200
        self.height = 200
        self.edges = {}
        self.weights = {}
        self.walls = []
        self.acid = []

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
        output = "\n"
        output.join(['\t'.join([str(cell) for cell in row]) for row in self.edges])
        return output

class Queue:
    def __init__(self):
        self.elements = collections.deque()

    def empty(self):
        return len(self.elements) == 0

    def put(self, x):
        self.elements.append(x)

    def get(self):
        return self.elements.popleft()

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

def breadth_first_search(graph, start):
    frontier = Queue()
    frontier.put(start)
    came_from = {}
    came_from[start] = None

    while not frontier.empty():
        current = frontier.get()
        for next in graph.neighbors(current):
            if next not in came_from:
                frontier.put(next)
                came_from[next] = current

    return came_from

def a_star_search(graph, start, goal):
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

    return came_from, cost_so_far


def reconstruct_path(came_from, start, goal):
    current = goal
    path = []
    while current!= start:
        path.append(current)
        current = came_from[current]
    path.append(start)
    path.reverse()
    return path


class Overlord(Zerg):
    def __init__(self, total_ticks, refined_minerals, dashboard=None):
        super().__init__(100)
        self.dashboard = dashboard
        self.total_ticks = total_ticks
        self.maps = {}
        self.drones = {}
        self.deploy = list()
        self.random_map_id = 0
        self.return_count = 0
        self.drop_zone_count = 0
        #TODO make logic to create zerg horde
        drone_count = int(refined_minerals / 9)
        for value in range(drone_count):
            z = Drone()
            self.drones[id(z)] = z
            self.deploy.append(id(z))

    def add_map(self, map_id, summary):
        self.maps[map_id] = summary
        Zerg.map_graphs[map_id] = Graph()

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
            self.return_count += 1
        elif self.deploy and self.total_ticks > 15:
            deploying = self.deploy.pop()
            if deploying in self.drones:
                self.drones[deploying].map = self.random_map_id
            if self.random_map_id not in Zerg.landing_clear:
                Zerg.landing_clear[self.random_map_id] = True
            if self.random_map_id not in Zerg.deploying:
                Zerg.deploying[self.random_map_id] = False
            if Zerg.landing_clear[self.random_map_id] == True:
                result = 'DEPLOY {} {}'.format(deploying, self.random_map_id)
                if self.random_map_id < 2:
                    self.random_map_id += 1
                else:
                    self.random_map_id = 0
                Zerg.deploying[self.random_map_id] = True
            else:
                self.deploy.append(deploying)
                result = "NONE"
        else:
            result = "NONE"
        self.dashboard.log.config(state=tkinter.NORMAL)
        self.dashboard.log.insert(tkinter.END, result)
        self.dashboard.log.insert(tkinter.END, "\n")
        self.dashboard.log.see(tkinter.END)
        self.dashboard.log.config(state=tkinter.DISABLED)
        return result

    def get_drone_info(self, drone):
        if drone.context:
            path = None
            tile = (drone.context.x, drone.context.y)
            north = (drone.context.x, int(drone.context.y) + 1)
            south = (drone.context.x, int(drone.context.y) - 1)
            east = (int(drone.context.x) + 1, drone.context.y)
            west = (int(drone.context.x) - 1, drone.context.y)
            Zerg.map_graphs[drone.map].edges.update({tile: list()})
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
            if drone.context.north in allowed:
                Zerg.map_graphs[drone.map].edges[tile].append(north)
            if drone.context.south in allowed:
                Zerg.map_graphs[drone.map].edges[tile].append(south)
            if drone.context.east in allowed:
                Zerg.map_graphs[drone.map].edges[tile].append(east)
            if drone.context.west in allowed:
                Zerg.map_graphs[drone.map].edges[tile].append(west)
            if drone.map in Zerg.map_minerals and Zerg.map_minerals[drone.map]:
                came_from,  cost_so_far = a_star_search(
                        Zerg.map_graphs[drone.map],
                        tile,
                        Zerg.map_minerals[drone.map]
                    )
                path = reconstruct_path(came_from,
                                     tile,
                                     Zerg.map_minerals[drone.map])
            if drone.commands:
                outdated = list()
                for key in drone.commands:
                    if drone.last_tile != tile:
                        outdated.append(key)
                for item in outdated:
                    drone.commands.pop(item)
            if (not drone.commands and drone.carry > 7) or ('Return' not in drone.commands and self.total_ticks < 25):
                came_from, cost_so_far = a_star_search(
                        Zerg.map_graphs[drone.map],
                        tile,
                        Zerg.starting_locations[drone.map])
                path = reconstruct_path(came_from,
                                tile,
                                Zerg.starting_locations[drone.map])
                if tile == path[0]:
                    path.pop(0)
                drone.commands.update({"Return": path})
            elif not drone.commands and path and drone.carry < 10:
                drone.commands.update({"Mine": path})
                Zerg.map_minerals.pop(drone.map)
            elif not drone.commands:
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
        self.map = 0
        self.context = None
        self.bias = Drone.last_bias % 4
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
        #if self.map in Zerg.map_minerals:
            #print("Minerals I see: ", Zerg.map_minerals[self.map])
        #jprint("Commands: ", self.commands)
        #print("Carring:  ", self.carry)
        print(Zerg.map_graphs[self.map])
        directions = {0: 'NORTH', 1: 'SOUTH', 2: 'EAST', 3: 'WEST'}
        neighbors = {0: context.north, 1: context.south, 2: context.east, 3: context.west}
        if self.map not in Zerg.starting_locations:
            Zerg.starting_locations[self.map] = (context.x, context.y)
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
                    goto = self.get_direction(self.commands['Mine'].pop(0), (context.x, context.y))
                if self.commands and len(self.commands['Mine']) == 0:
                    if self.map in Zerg.map_minerals:
                        Zerg.map_minerals.pop(self.map)
                    self.commands.pop('Mine')
                else:
                    self.carry += 1

                return goto
                '''
                direction = self.commands['Mine']
                self.commands.pop('Mine')
                return directions.get(direction)
            '''
            elif 'Return' in self.commands:
                print("Commands: ", self.commands)
                goto = "Center"
                if len(self.commands['Return']) > 0:
                    print("Supposed: ", self.commands['Return'][0])
                    to_tile = self.commands['Return'].pop(0)
                    if to_tile == (context.x, context.y) and len(self.commands['Return']) > 0:
                        to_tile = self.commands['Return'].pop(0)
                    goto = self.get_direction(to_tile, (context.x, context.y))
                    print("going to: ", goto)
                # if len(self.commands['Return']) == 0:
                if Zerg.starting_locations[self.map] == (context.x, context.y):
                    self.carry = 0
                    self.path_step = 0
                    Zerg.returns.append(id(self))
                    self.commands.pop('Return')

                return goto

            elif 'Discover' in self.commands:
                self.commands.pop('Discover')
                allowed = " ~"
                if self.bias == 0:
                    return Drone.north_bias(self.last_tile, context, directions, allowed)
                elif self.bias == 1:
                    return Drone.south_bias(self.last_tile, context, directions, allowed)
                elif self.bias == 2:
                    return Drone.east_bias(self.last_tile, context, directions, allowed)
                elif self.bias == 3:
                    return Drone.west_bias(self.last_tile, context, directions, allowed)

        #zerg_directions = [context.north, context.south, context.east, context.west]
        #random_choice = random.randint(0, 3)  # both arguments are inclusive
        #if zerg_directions[random_choice] == "#" or zerg_directions[random_choice] == "~":
            #return "CENTER"
        return "CENTER"


    def north_bias(last_tile, context, directions, allowed):
        if context.north in allowed and context.y + 1 != last_tile[1]:
            return directions.get(0)
        elif context.east in allowed and context.x + 1 != last_tile[0]:
            return directions.get(2)
        elif context.south in allowed and context.y - 1 != last_tile[1]: return directions.get(1)
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
        self.geometry("300x200+300+0")
        self.title("Overlord's Dashboard")
        self.log = tkinter.Text(self, height=10,  width=30)
        self.log.pack()