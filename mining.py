import random
import tkinter

class Zerg:
    returns = list()
    starting_locations = dict()
    landing_clear = dict()
    deploying = dict()

    def __init__(self, health):
        self.health = health

    def action(self):
        pass

class Overlord(Zerg):
    def __init__(self, total_ticks, refined_minerals, dashboard=None):
        super().__init__(100)
        self.dashboard = dashboard
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

    def action(self):
        print("Zergs", self.drones.keys())
        print("Returns", Zerg.returns)
        print("Deploy", self.deploy)
        self.delete = []
        print(Zerg.starting_locations)
        for zerg in self.drones:
            drone = self.drones[zerg]
            if drone.context:
                drone.commands = dict()
                if drone.context.north == "*" and drone.carry < 10:
                    drone.commands.update({"Mine": 0})
                elif drone.context.south == "*" and drone.carry < 10:
                    drone.commands.update({"Mine": 1})
                elif drone.context.east == "*" and drone.carry < 10:
                    drone.commands.update({"Mine": 2})
                elif drone.context.west == "*" and drone.carry < 10:
                    drone.commands.update({"Mine": 3})
                elif drone.context.north == "_" and drone.carry > 5:
                    drone.commands.update({"Return": 0})
                elif drone.context.south == "_" and drone.carry > 5:
                    drone.commands.update({"Return": 1})
                elif drone.context.east == "_" and drone.carry > 5:
                    drone.commands.update({"Return": 2})
                elif drone.context.west == "_" and drone.carry > 5:
                    drone.commands.update({"Return": 3})
                elif drone.context.north == "~" or drone.context.north == "#":
                    drone.commands.update({"Avoid": 1})
                elif drone.context.south == "~" or drone.context.south == "#":
                    drone.commands.update({"Avoid": 0})
                elif drone.context.east == "~" or drone.context.east == "#":
                    drone.commands.update({"Avoid": 3})
                elif drone.context.west == "~" or drone.context.west == "#":
                    drone.commands.update({"Avoid": 2})

                if drone.health <= 0:
                    self.delete.append(zerg)
        for zerg in self.delete:
            self.drones.pop(zerg)
        if Zerg.returns:
            returning = Zerg.returns.pop()
            result = 'RETURN {}'.format(returning)
            Zerg.landing_clear[self.drones[returning].map] = True
            self.deploy.append(returning)
            self.return_count += 1
        elif self.deploy:
            deploying = self.deploy.pop()
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
                result = "NONE"
        else:
            result = "NONE"
        self.dashboard.log.config(state=tkinter.NORMAL)
        self.dashboard.log.insert(tkinter.END, result)
        self.dashboard.log.insert(tkinter.END, "\n")
        self.dashboard.log.see(tkinter.END)
        self.dashboard.log.config(state=tkinter.DISABLED)
        print("Return count: ", self.return_count)
        return result

class Drone(Zerg):
    def __init__(self):
        super().__init__(40)
        self.moves = 1
        self.capacity = 10
        self.carry = 0
        self.steps = 0
        self.map = 0
        self.context = None
        self.commands = dict()

    def action(self, context):
        directions = {0: 'NORTH', 1: 'SOUTH', 2: 'EAST', 3: 'WEST'}
        print(self.carry)
        if self.steps == 0 and self.map not in Zerg.starting_locations:
            Zerg.starting_locations[self.map] = "{}, {}".format(context.x, context.y)
        if Zerg.starting_locations[self.map] == "{}, {}".format(context.x, context.y):
            Zerg.landing_clear[self.map] = False
        else:
            Zerg.landing_clear[self.map] = True
        self.context = context
        print(self.commands)
        if self.commands:
            if 'Mine' in self.commands:
                self.carry += 1
                direction = self.commands['Mine']
                self.commands.pop('Mine')
                return directions.get(direction)
            elif 'Return' in self.commands:
                self.carry = 0
                direction = self.commands['Return']
                self.commands.pop('Return')
                Zerg.returns.append(id(self))
                return directions.get(direction)
            elif 'Avoid' in self.commands:
                direction = self.commands['Avoid']
                self.commands.pop('Avoid')
                return directions.get(direction)
        '''
        if context.north == "*" and self.carry < 10:
            self.carry += 1
            return directions.get(0)
        elif context.south == "*" and self.carry < 10:
            self.carry += 1
            return directions.get(1)
        elif context.east == "*" and self.carry < 10:
            self.carry += 1
            return directions.get(2)
        elif context.east == "*" and self.carry < 10:
            self.carry += 1
            return directions.get(3)
        if context.north == "_" and self.carry > 5:
            self.carry = 0
            self.steps += 1
            Zerg.returns.append(id(self))
            return directions.get(0)
        elif context.south == "_" and self.carry > 5:
            self.carry = 0
            self.steps += 1
            Zerg.returns.append(id(self))
            return directions.get(1)
        elif context.east == "_" and self.carry > 5:
            self.carry = 0
            self.steps += 1
            Zerg.returns.append(id(self))
            return directions.get(2)
        elif context.east == "_" and self.carry > 5:
            self.carry = 0
            self.steps += 1
            Zerg.returns.append(id(self))
            return directions.get(3)
        if context.north == "#":
            self.steps += 1
            return directions.get(1)
        elif context.south == "#":
            self.steps += 1
            return directions.get(0)
        elif context.east == "#":
            self.steps += 1
            return directions.get(3)
        elif context.east == "#":
            self.steps += 1
            return directions.get(2)
        '''
        random_choice = random.randint(0, 3)  # both arguments are inclusive
        return directions.get(random_choice, "CENTER")

class Dashboard(tkinter.Toplevel):
     def __init__(self, parent):
        super().__init__(parent)
        self.geometry("300x200+300+0")
        self.title("Overlord's Dashboard")
        self.log = tkinter.Text(self, height=10,  width=30)
        self.log.pack()
