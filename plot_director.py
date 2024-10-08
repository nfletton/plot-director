import ast
import curses
import os
import re
import sys
import time

import requests
from nextdraw import NextDraw

PARAM_CASTS = {
    'speed_pendown': [int],
    'speed_penup': [int],
    'accel': [int],
    'pen_pos_down': [int],
    'pen_pos_up': [int],
    'pen_rate_lower': [int],
    'pen_rate_raise': [int],
    'pen_delay_down': [int],
    'pen_delay_up': [int],
    'const_speed': [bool],
    'model': [int],
    'penlift': [int],
    'port': [int],
    'port_config': [int],

    'units': [int],

    'load_config': [lambda x: x],

    'goto': [float, float],
    'moveto': [float, float],
    'lineto': [float, float],
    'go': [float, float],
    'move': [float, float],
    'line': [float, float],
    'draw_path': [ast.literal_eval],
    'delay': [int],
    'usb_command': [lambda x: x],
    'usb_query': [lambda x: x],
}


def notify(message, webhook):
    if webhook:
        requests.post(f"{webhook}", data=message.encode(encoding='utf-8'))


def convert_params(conversions, f_name, string_params):
    if f_name in conversions:
        return [func(string_params[i]) for i, func in enumerate(conversions[f_name])]
    else:
        return []


class PlotDirector:
    def __init__(self, nd, webhook_url):
        self.ad = nd
        self.pause = False
        self.webhook_url = webhook_url

    definitions = {}

    def process_function(self, command_parts):
        function_name = command_parts[0]
        try:
            if len(command_parts) > 1:
                params = convert_params(PARAM_CASTS, function_name, command_parts[1:])
            else:
                params = []

            api_function = getattr(self.ad, function_name)
            api_function(*params)
        except Exception as e:
            print(f"Error executing command {function_name}: {e}")

    def process_option(self, option_parts):
        if len(option_parts) > 1:
            option_name = option_parts[0]
            option_value = convert_params(PARAM_CASTS, option_name, option_parts[1:])[0]
            try:
                setattr(getattr(self.ad, 'options'), option_name, option_value)
            except Exception as e:
                print(f"Error setting option '{option_name} to '{option_value}': {e}")
        else:
            print("No option name/value pair specified")

    def process_definition(self, statement):
        name, _, commands = statement.partition(' ')
        self.definitions[name] = commands

    def process_statement(self, statement):
        if statement[0] == '#':
            print(statement)
            return
        statement_parts = re.split(r'\s+', statement)

        match statement_parts[0]:
            case 'def':
                self.process_definition(statement[4:])
            case 'options':
                self.process_option(statement_parts[1:])
            case 'pause':
                message = f"Plot Paused: {statement[6:]}"
                notify(message, webhook_url)
                print(message)
                self.pause = True
            case _:
                if statement_parts[0] in self.definitions:
                    commands = self.definitions[statement_parts[0]]
                    self.process_definition_body(commands)
                else:
                    self.process_function(statement_parts)

    def process_definition_body(self, commands):
        for command in commands.split('|'):
            statement = command.strip()
            if statement:
                self.process_statement(statement)

    def process_stream(self, screen, stream):
        curses.cbreak()
        screen.nodelay(True)

        for line in stream:
            # get key press

            key_press = screen.getch()

            match key_press:
                case _:
                    pass

            if self.pause:
                print("Plot paused. Press 'c' to continue")
                self.wait_on_continue(screen)
            statement = line.strip()
            if statement:
                self.process_statement(statement)

    def process_commands(self, command_file):
        if os.path.isfile(command_file):
            with open(command_file, 'r') as file:
                curses.wrapper(self.process_stream, file)
            self.ad.moveto(0.0, 0.0)
            notify("Pen plot completed", webhook_url)
        else:
            print(f"File '{command_file}' does not exist.")

    def wait_on_continue(self, screen):
        while(self.pause):
            time.sleep(1)
            key_press = screen.getch()
            if key_press == ord('c'):
                self.pause = False
                print("Continuing plot.......")


def safe(ad):
    if input("Is the NextDraw in the home position? (y/n): ").lower() != 'y':
        print("\n*** 1. Turn off NextDraw power supply.          ***")
        print("*** 2. Move the carriage to the home position. ***")
        print("*** 3. Turn the power supply back on.          ***")
        return False
    has_power = True if int(ad.usb_query("QC\r").split(",")[1]) > 276 else False
    if not has_power:
        print("\n*** NextDraw power supply appears to be off. ****")
    return has_power


if __name__ == '__main__':
    filename = sys.argv[1]
    if len(sys.argv) > 2:
        webhook_url = sys.argv[2]
    else:
        webhook_url = ""
    nd = NextDraw()
    nd.interactive()
    nd.options.homing = False
    nd.options.model = 2
    nd.options.penlift = 3
    nd.options.units = 2
    connected = nd.connect()
    if connected:
        if safe(nd):
            director = PlotDirector(nd, webhook_url)
            director.process_commands(filename)
        nd.disconnect()

    else:
        print("NextDraw not connected.")
        sys.exit()
