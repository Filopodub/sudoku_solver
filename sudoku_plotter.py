from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor, ColorSensor, TouchSensor
from pybricks.parameters import Port
from pybricks.tools import wait


class SudokuPlotter:
    def __init__(self, motor_x_port, motor_y_port, color_sensor_port, touch_sensor_y_port, touch_sensor_x_start_port, touch_sensor_x_end_port, csv_file="scanned_data.csv"):
        self.ev3 = EV3Brick()
        self.motor_x = Motor(motor_x_port)
        self.motor_y = Motor(motor_y_port)
        self.color_sensor = ColorSensor(color_sensor_port)
        self.touch_sensor_y = TouchSensor(touch_sensor_y_port)
        self.touch_sensor_x_start = TouchSensor(touch_sensor_x_start_port)
        self.touch_sensor_x_end = TouchSensor(touch_sensor_x_end_port)
        self.ready = False
        self.current_x = 0
        self.current_y = 0
        self.direction = 1  # 1 for forward, -1 for backward
        self.row_data = []  # Stores data for the current row
        self.csv_file = csv_file
        self.init_csv_file()

    def init_csv_file(self):
        """Initializes the text file and writes the header."""
        with open(self.csv_file, mode="w") as file:
            file.write("")

    def beep(self):
        """Makes the EV3 beep."""
        self.ev3.speaker.beep()

    def set_X(self, position):
        """Sets the current X position."""
        self.current_x = position

    def set_Y(self, position):
        """Sets the current Y position."""
        self.current_y = position

    def get_position(self):
        """Returns the current X and Y position."""
        return self.current_x, self.current_y

    def save_value(self):
        """Saves the reflection value at the current position."""
        reflection = self.color_sensor.reflection()
        if len(self.row_data) < 400:
            self.row_data.append(reflection)

    def write_row_data(self):
        """Writes the current row's data to the file."""
        # Reverse the data if the direction is backward
        if self.direction == -1:
            self.row_data.reverse()

        with open(self.csv_file, mode="a") as file:
            file.write(",".join(map(str, self.row_data)) + "\n")
        self.row_data = []  # Clear the row data for the next row

    def bumper_handler_X(self, direction, set_position):
        """Handles the X-axis bumper."""
        self.beep()
        print("Reached bumper X; waiting for release...")

        self.motor_x.run_angle(500,100*direction)
        wait(100)

        self.beep()
        self.set_X(set_position)
        print("Bumper X released; position reset to" ,set_position)
        self.direction = direction 

    def bumper_handler_Y(self):
        """Handles the Y-axis bumper."""
        self.beep()
        print("Reached bumper Y; waiting for release...")

        while self.touch_sensor_y.pressed():
            self.motor_y.run_angle(500, 100)
            wait(100)

        self.beep()
        self.set_Y(0)
        print("Bumper Y released; position reset to 0.")

    def go_to_start(self, speed = 300):
        """Moves to the starting position."""
        print("#### Go to start! ####")

        # Move Motor X to start
        self.motor_x.run(-speed)
        
        while not self.touch_sensor_x_start.pressed(): 
            wait(10)  

        self.motor_x.stop()
        self.bumper_handler_X(1, 0)

        # Move Motor Y to start
        self.motor_y.run(-speed)
        
        while not self.touch_sensor_y.pressed(): 
            wait(10)  

        self.motor_y.stop()
        self.bumper_handler_Y()

        # Set everything to ready
        self.ready = True
        print("#### All ready! ####\n")
        print("Press middle button to start:")
        wait(1000)
    

    def scanning_cycle(self, speed=600):
        """Performs the scanning cycle with continuous movement."""
        print("#### Scanning! ####")
        if not self.ready:
            print("Scanner is not ready. Initialize first.")
            return  

        self.direction = 1  # 1 for forward, -1 for backward
        self.ready = False

        while self.current_y < 400:
            # Before starting X movement, record start position
            start_x_position = self.motor_x.angle()  # Read encoder value

            # Start continuous movement in X direction
            self.motor_x.run(self.direction * speed)

            while not (self.touch_sensor_x_start.pressed() and self.direction == -1) and \
                not (self.touch_sensor_x_end.pressed() and self.direction == 1):

                # Track the angle traveled
                current_position = self.motor_x.angle()  # Get current position
                angle_traveled = abs(current_position - start_x_position)
                
                if angle_traveled >= 3500:
                    self.motor_x.run(self.direction * speed/5)


                # Save data every 10 degrees traveled
                if angle_traveled % 10 == 0:
                    self.save_value()

                wait(1)
                            
                
            # Stop X movement when bumper is reached
            self.motor_x.stop()

            # Measure the distance traveled in degrees
            end_x_position = self.motor_x.angle()  # Read final encoder value
            distance_traveled = abs(end_x_position - start_x_position)
            print(distance_traveled)

            # Handle bumper behavior and direction reversal
            if self.touch_sensor_x_start.pressed() and self.direction == -1:
                self.bumper_handler_X(1, 0)
            elif self.touch_sensor_x_end.pressed() and self.direction == 1:
                last_position = self.current_x
                self.bumper_handler_X(-1, last_position)

            self.write_row_data()

            # Move Y continuously for the next row
            self.motor_y.run_angle(speed, 30)  # Move Y-axis for a fixed duration
            self.current_y += 1  # Approximate movement tracking
            print(self.current_y)

            wait(100)  # Small delay between rows

        print("#### All scanned! ####\n")

